"""The InferenceArbiter's priority rules (KD-12).

Each test names the stated outcome it pins down, because two implementers could
not otherwise guess the same answer and the frontend's timeout handling depends
on which one holds.
"""

from __future__ import annotations

import asyncio

import pytest

from autonomos.arbiter import (
    REASON_PREEMPTED,
    REASON_SUPERSEDED,
    ArbiterTimeout,
    InferenceArbiter,
    JobKind,
)


def make_arbiter(quiet: float = 0.0, grace: float = 0.2) -> InferenceArbiter:
    return InferenceArbiter(quiet_period_s=quiet, preempt_grace_s=grace)


async def test_only_one_job_holds_the_slot():
    arbiter = make_arbiter()
    first = await arbiter.acquire(JobKind.QUESTION, asyncio.Event())
    with pytest.raises(ArbiterTimeout):
        await arbiter.acquire(JobKind.ASSIST, asyncio.Event(), wait_timeout_s=0.05)
    arbiter.release(first)
    lease = await arbiter.acquire(JobKind.ASSIST, asyncio.Event(), wait_timeout_s=0.5)
    assert lease.kind == JobKind.ASSIST


async def test_transcription_preempts_a_running_question():
    """Stated outcome: the question terminates with `preempted`, and the
    transcription does not wait for it to unwind."""
    arbiter = make_arbiter()
    question_cancel = asyncio.Event()
    question = await arbiter.acquire(JobKind.QUESTION, question_cancel)

    async def transcription():
        return await arbiter.acquire(JobKind.TRANSCRIPTION, asyncio.Event())

    task = asyncio.ensure_future(transcription())
    await asyncio.sleep(0.02)
    assert question_cancel.is_set()
    assert question.reason == REASON_PREEMPTED

    arbiter.release(question)  # the runner notices cancellation and lets go
    lease = await asyncio.wait_for(task, 1.0)
    assert lease.kind == JobKind.TRANSCRIPTION


async def test_transcription_takes_the_slot_even_if_the_holder_never_unwinds():
    """R4's residual: cancellation is not instantaneous, and interactive work
    still must not wait on background work."""
    arbiter = make_arbiter(grace=0.1)
    summary = await arbiter.acquire(JobKind.SUMMARY, asyncio.Event())
    lease = await asyncio.wait_for(
        arbiter.acquire(JobKind.TRANSCRIPTION, asyncio.Event()), 1.0
    )
    assert lease.kind == JobKind.TRANSCRIPTION
    assert summary.cancel.is_set()
    assert summary.reason == REASON_SUPERSEDED
    assert summary.detached is True


async def test_a_question_waits_for_a_running_transcription():
    """Stated outcome: preempting a short, bounded transcription to start a
    76-second answer would trade a guaranteed small wait for a broken 8.8."""
    arbiter = make_arbiter()
    transcription_cancel = asyncio.Event()
    transcription = await arbiter.acquire(JobKind.TRANSCRIPTION, transcription_cancel)

    task = asyncio.ensure_future(
        arbiter.acquire(JobKind.QUESTION, asyncio.Event(), wait_timeout_s=1.0)
    )
    await asyncio.sleep(0.05)
    assert not transcription_cancel.is_set()
    assert not task.done()

    arbiter.release(transcription)
    lease = await asyncio.wait_for(task, 1.0)
    assert lease.kind == JobKind.QUESTION


async def test_a_question_cancels_a_running_assist():
    arbiter = make_arbiter()
    assist_cancel = asyncio.Event()
    assist = await arbiter.acquire(JobKind.ASSIST, assist_cancel)
    task = asyncio.ensure_future(arbiter.acquire(JobKind.QUESTION, asyncio.Event()))
    await asyncio.sleep(0.02)
    assert assist_cancel.is_set()
    assert assist.reason == REASON_SUPERSEDED
    arbiter.release(assist)
    lease = await asyncio.wait_for(task, 1.0)
    assert lease.kind == JobKind.QUESTION


async def test_interactive_ordering_is_transcription_then_question_then_assist():
    arbiter = make_arbiter()
    holder = await arbiter.acquire(JobKind.TRANSCRIPTION, asyncio.Event())
    order: list[str] = []

    async def contender(kind: JobKind):
        lease = await arbiter.acquire(kind, asyncio.Event(), wait_timeout_s=5.0)
        order.append(kind.name)
        await asyncio.sleep(0.01)
        arbiter.release(lease)

    tasks = [
        asyncio.ensure_future(contender(JobKind.ASSIST)),
        asyncio.ensure_future(contender(JobKind.SUMMARY)),
        asyncio.ensure_future(contender(JobKind.QUESTION)),
    ]
    await asyncio.sleep(0.05)
    arbiter.release(holder)
    await asyncio.wait_for(asyncio.gather(*tasks), 3.0)
    assert order == ["QUESTION", "ASSIST", "SUMMARY"]


async def test_a_summary_waits_for_the_quiet_period_after_interactive_work():
    """A cancelled summary waits 60 s of quiet, so back-to-back captures do not
    livelock it (KD-12); here the period is shortened for the test."""
    arbiter = make_arbiter(quiet=0.3)
    transcription = await arbiter.acquire(JobKind.TRANSCRIPTION, asyncio.Event())
    arbiter.release(transcription)

    task = asyncio.ensure_future(arbiter.acquire(JobKind.SUMMARY, asyncio.Event()))
    await asyncio.sleep(0.1)
    assert not task.done()
    lease = await asyncio.wait_for(task, 2.0)
    assert lease.kind == JobKind.SUMMARY


async def test_a_cancelled_waiter_does_not_hold_the_slot():
    arbiter = make_arbiter()
    holder = await arbiter.acquire(JobKind.TRANSCRIPTION, asyncio.Event())
    cancel = asyncio.Event()
    task = asyncio.ensure_future(
        arbiter.acquire(JobKind.QUESTION, cancel, wait_timeout_s=2.0)
    )
    await asyncio.sleep(0.02)
    cancel.set()
    arbiter.release(holder)
    with pytest.raises(ArbiterTimeout):
        await asyncio.wait_for(task, 1.0)
    assert arbiter.active_kind is None


async def test_interactive_active_reports_waiters_too():
    arbiter = make_arbiter()
    assert arbiter.interactive_active() is False
    lease = await arbiter.acquire(JobKind.TRANSCRIPTION, asyncio.Event())
    assert arbiter.interactive_active() is True
    arbiter.release(lease)
    assert arbiter.interactive_active() is False
