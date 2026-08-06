"""The InferenceArbiter (KD-12).

One arbiter governs *all* local inference — whisper and the LLM — in two
priority classes:

* **interactive** — transcription, insight questions, category assist. Never
  waits behind background work. Ordered among themselves
  `transcription > question > category assist`.
* **background** — monthly summary generation. Runs only when nothing
  interactive is active, and only after a 60-second quiet period.

Stated outcomes, which are fixed by the design and not negotiable here:

* Transcription never waits and **preempts a running question**; the question
  terminates with the terminal code `preempted`.
* A question waits for a running transcription (bounded by the sidecar's 20 s
  timeout) and that wait is subtracted from its 110 s deadline, not added.
* Category assist yields to everything, never preempts, and is abandoned when
  something else needs the slot — which produces exactly the null result it is
  already designed to produce.
* An interactive arrival cancels an in-flight summary immediately and does not
  wait for it to unwind (R4 accepts ~1 s of overlap while cancellation lands).
"""

from __future__ import annotations

import asyncio
import itertools
import logging
from dataclasses import dataclass, field
from enum import IntEnum

from .config import get_settings

log = logging.getLogger("autonomos.arbiter")


class JobKind(IntEnum):
    """Lower value wins. Interactive is everything below SUMMARY."""

    TRANSCRIPTION = 0
    QUESTION = 1
    ASSIST = 2
    SUMMARY = 10


INTERACTIVE_KINDS = frozenset({JobKind.TRANSCRIPTION, JobKind.QUESTION, JobKind.ASSIST})

# Reasons an arbiter-driven cancellation carries.
REASON_PREEMPTED = "preempted"  # a transcription took the slot from a question
REASON_SUPERSEDED = "superseded"  # background/assist yielded to interactive work


class ArbiterTimeout(Exception):
    """The caller's wait budget elapsed before the slot became free."""


@dataclass
class Lease:
    kind: JobKind
    cancel: asyncio.Event
    seq: int
    reason: str | None = None
    detached: bool = False

    def cancelled(self) -> bool:
        return self.cancel.is_set()


@dataclass
class _Waiter:
    kind: JobKind
    seq: int
    cancel: asyncio.Event
    granted: asyncio.Event = field(default_factory=asyncio.Event)
    lease: Lease | None = None


class InferenceArbiter:
    def __init__(
        self,
        *,
        quiet_period_s: float | None = None,
        preempt_grace_s: float | None = None,
    ) -> None:
        settings = get_settings()
        self.quiet_period_s = (
            settings.arbiter_quiet_period_s if quiet_period_s is None else quiet_period_s
        )
        self.preempt_grace_s = (
            settings.arbiter_preempt_grace_s if preempt_grace_s is None else preempt_grace_s
        )
        self._lock = asyncio.Lock()
        self._active: Lease | None = None
        self._waiters: list[_Waiter] = []
        self._seq = itertools.count(1)
        self._last_interactive_end: float | None = None
        self._pump_handle: asyncio.TimerHandle | None = None

    # -- introspection ----------------------------------------------------
    @property
    def active_kind(self) -> JobKind | None:
        return self._active.kind if self._active else None

    def interactive_active(self) -> bool:
        if self._active is not None and self._active.kind in INTERACTIVE_KINDS:
            return True
        return any(w.kind in INTERACTIVE_KINDS for w in self._waiters)

    def quiet_remaining_s(self) -> float:
        if self._last_interactive_end is None:
            return 0.0
        loop = asyncio.get_running_loop()
        return max(0.0, self.quiet_period_s - (loop.time() - self._last_interactive_end))

    # -- acquisition ------------------------------------------------------
    async def acquire(
        self,
        kind: JobKind,
        cancel: asyncio.Event,
        *,
        wait_timeout_s: float | None = None,
    ) -> Lease:
        """Take the single inference slot, applying the priority rules above.

        Raises `ArbiterTimeout` if `wait_timeout_s` elapses first — which is how
        a question below `LLM_MIN_START_BUDGET_S` and an assist past its 6 s cap
        both terminate without starting doomed work.
        """
        waiter = _Waiter(kind=kind, seq=next(self._seq), cancel=cancel)

        async with self._lock:
            forced_preemption = self._preempt_for(kind)
            self._waiters.append(waiter)
            self._pump()

        grace = self.preempt_grace_s if forced_preemption else None
        budgets = [b for b in (wait_timeout_s, grace) if b is not None]
        timeout = min(budgets) if budgets else None

        try:
            if timeout is None:
                await waiter.granted.wait()
            else:
                await asyncio.wait_for(waiter.granted.wait(), timeout)
        except asyncio.TimeoutError:
            async with self._lock:
                if waiter.granted.is_set() and waiter.lease is not None:
                    return waiter.lease
                self._remove_waiter(waiter)
                if grace is not None and timeout == grace:
                    # The preempted holder has not unwound inside the grace
                    # period; take the slot anyway rather than make interactive
                    # work wait on background work (KD-12, R4 residual).
                    return self._force_take(kind, cancel)
                raise ArbiterTimeout(f"{kind.name} waited {timeout:.1f}s for the slot")

        assert waiter.lease is not None
        if cancel.is_set():
            # Cancelled while queueing; hand the slot straight back.
            self.release(waiter.lease)
            raise ArbiterTimeout(f"{kind.name} was cancelled while queued")
        return waiter.lease

    def release(self, lease: Lease) -> None:
        if lease.detached:
            return
        if self._active is lease:
            self._active = None
            if lease.kind in INTERACTIVE_KINDS:
                self._last_interactive_end = asyncio.get_running_loop().time()
            self._pump()

    # -- internals --------------------------------------------------------
    def _preempt_for(self, kind: JobKind) -> bool:
        """Cancel whatever the arriving kind outranks. True if we preempted."""
        active = self._active
        if active is None or kind not in INTERACTIVE_KINDS:
            return False
        if active.kind == JobKind.SUMMARY:
            self._cancel(active, REASON_SUPERSEDED)
            return True
        if kind == JobKind.TRANSCRIPTION and active.kind == JobKind.QUESTION:
            self._cancel(active, REASON_PREEMPTED)
            return True
        if kind in (JobKind.TRANSCRIPTION, JobKind.QUESTION) and active.kind == JobKind.ASSIST:
            self._cancel(active, REASON_SUPERSEDED)
            return True
        return False

    @staticmethod
    def _cancel(lease: Lease, reason: str) -> None:
        if not lease.cancel.is_set():
            lease.reason = reason
            lease.cancel.set()
            log.info("arbiter cancelled %s (%s)", lease.kind.name, reason)

    def _force_take(self, kind: JobKind, cancel: asyncio.Event) -> Lease:
        if self._active is not None:
            self._active.detached = True
        lease = Lease(kind=kind, cancel=cancel, seq=next(self._seq))
        self._active = lease
        log.warning("arbiter force-took the slot for %s after the grace period", kind.name)
        return lease

    def _remove_waiter(self, waiter: _Waiter) -> None:
        try:
            self._waiters.remove(waiter)
        except ValueError:
            pass

    def _pump(self) -> None:
        if self._active is not None or not self._waiters:
            return
        self._waiters.sort(key=lambda w: (int(w.kind), w.seq))
        waiter = self._waiters[0]
        if waiter.kind == JobKind.SUMMARY:
            remaining = self.quiet_remaining_s()
            if remaining > 0:
                self._schedule_pump(remaining)
                return
        self._waiters.pop(0)
        lease = Lease(kind=waiter.kind, cancel=waiter.cancel, seq=waiter.seq)
        self._active = lease
        waiter.lease = lease
        waiter.granted.set()

    def _schedule_pump(self, delay: float) -> None:
        loop = asyncio.get_running_loop()
        if self._pump_handle is not None:
            self._pump_handle.cancel()
        self._pump_handle = loop.call_later(delay + 0.01, self._pump)


_arbiter: InferenceArbiter | None = None


def get_arbiter() -> InferenceArbiter:
    global _arbiter
    if _arbiter is None:
        _arbiter = InferenceArbiter()
    return _arbiter


def reset_arbiter() -> None:
    global _arbiter
    _arbiter = None
