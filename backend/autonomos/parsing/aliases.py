"""Alias matching for categories and payment methods (9.3, 9.7).

Matching is against the user's *actual* rows plus the seeded alias table, so a
suggestion can only ever be an existing category (9.3) and a payment method is
never invented (9.7). Longest phrase wins; a tie between two different targets
is an ambiguity and yields nothing, per 9.2.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field

from .text import normalize


@dataclass(frozen=True)
class Target:
    id: int
    name: str


@dataclass
class Vocabulary:
    """Normalised phrase -> target, for one lookup table."""

    targets: dict[int, Target] = field(default_factory=dict)
    phrases: dict[str, int] = field(default_factory=dict)

    def add(self, target: Target, phrase: str) -> None:
        key = normalize(phrase)
        if not key:
            return
        self.targets.setdefault(target.id, target)
        # A phrase already claimed by another target is ambiguous: drop both
        # claims rather than let insertion order decide (9.2).
        existing = self.phrases.get(key)
        if existing is not None and existing != target.id:
            self.phrases[key] = -1
            return
        self.phrases[key] = target.id

    def match(self, text: str) -> Target | None:
        haystack = f" {normalize(text)} "
        best_len = 0
        best_ids: set[int] = set()
        for phrase, target_id in self.phrases.items():
            if target_id < 0:
                continue
            if f" {phrase} " in haystack:
                if len(phrase) > best_len:
                    best_len = len(phrase)
                    best_ids = {target_id}
                elif len(phrase) == best_len:
                    best_ids.add(target_id)
        if len(best_ids) != 1:
            return None
        return self.targets[next(iter(best_ids))]


def _load(
    conn: sqlite3.Connection, table: str, alias_table: str
) -> Vocabulary:
    vocab = Vocabulary()
    rows = conn.execute(
        f"SELECT id, name FROM {table} WHERE archived_at IS NULL ORDER BY sort_order, id"
    ).fetchall()
    by_id = {row["id"]: Target(row["id"], row["name"]) for row in rows}
    for target in by_id.values():
        vocab.add(target, target.name)
    for alias_row in conn.execute(
        f"SELECT target_id, alias FROM {alias_table}"
    ).fetchall():
        target = by_id.get(alias_row["target_id"])
        if target is not None:  # aliases pointing at archived rows are inert
            vocab.add(target, alias_row["alias"])
    return vocab


def category_vocabulary(conn: sqlite3.Connection) -> Vocabulary:
    return _load(conn, "categories", "category_aliases")


def payment_method_vocabulary(conn: sqlite3.Connection) -> Vocabulary:
    return _load(conn, "payment_methods", "payment_method_aliases")
