"""FactBuilder — stage 2 of KD-10. **SQL computes; the LLM only phrases.**

Every figure the model is allowed to say comes from here. The journal context
lives under a 1,200-token budget: prompt evaluation measures 26-36 tok/s on this
host, so every 100 tokens of context costs ~3-4 s before generation starts. That
budget is load-bearing for 11.12 and must not be raised.
"""

from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass, field

from ..config import get_settings
from ..repo import expenses as expenses_repo
from ..repo import journal as journal_repo
from .router import Route

EXCERPT_CHARS_SUMMARY = 300
TOP_EXPENSES = 5
# Spanish averages a little under four characters per token on this tokenizer;
# 3.5 keeps the estimate conservative (over-counting shortens context, which is
# the safe direction for the deadline).
CHARS_PER_TOKEN = 3.5


def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text or "") / CHARS_PER_TOKEN))


@dataclass
class JournalExcerpt:
    written_at: str
    text: str


@dataclass
class FactSet:
    """Everything the prompt may state and NumericGuard will accept."""

    period_label: str
    period_start: str
    period_end: str
    period_assumed: bool
    domain: str
    total_cop: int | None = None
    expense_count: int | None = None
    distinct_days: int | None = None
    by_category: list[dict] | None = None
    by_payment_method: list[dict] | None = None
    top_expenses: list[dict] = field(default_factory=list)
    journal_entries_considered: int | None = None
    journal_entries_used: int | None = None
    journal_truncated: bool = False
    journal_excerpts: list[JournalExcerpt] = field(default_factory=list)

    def has_data(self) -> bool:
        return bool(self.expense_count or self.journal_entries_considered)

    def to_wire(self) -> dict:
        """Exactly the `facts` object of the Interface Contract — no more."""
        return {
            "period_label": self.period_label,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "period_assumed": self.period_assumed,
            "domain": self.domain,
            "total_cop": self.total_cop,
            "expense_count": self.expense_count,
            "by_category": (
                [
                    {
                        "name": item["name"],
                        "amount_cop": item["amount_cop"],
                        "percent": item["percent"],
                    }
                    for item in self.by_category
                ]
                if self.by_category is not None
                else None
            ),
            "journal_entries_considered": self.journal_entries_considered,
            "journal_entries_used": self.journal_entries_used,
            "journal_truncated": self.journal_truncated,
        }


def _finance_facts(conn: sqlite3.Connection, facts: FactSet) -> None:
    start, end = facts.period_start, facts.period_end
    totals = conn.execute(
        "SELECT COALESCE(SUM(amount_cop), 0) AS total, COUNT(*) AS n, "
        "COUNT(DISTINCT spent_on) AS days FROM expenses WHERE spent_on BETWEEN ? AND ?",
        (start, end),
    ).fetchone()
    facts.total_cop = int(totals["total"])
    facts.expense_count = int(totals["n"])
    facts.distinct_days = int(totals["days"])

    category_rows = conn.execute(
        """
        SELECT c.name AS name, SUM(e.amount_cop) AS amount
        FROM expenses e JOIN categories c ON c.id = e.category_id
        WHERE e.spent_on BETWEEN ? AND ?
        GROUP BY c.id, c.name ORDER BY amount DESC, c.name ASC
        """,
        (start, end),
    ).fetchall()
    amounts = [int(row["amount"]) for row in category_rows]
    percents = expenses_repo.largest_remainder_percents(amounts, facts.total_cop)
    facts.by_category = [
        {"name": row["name"], "amount_cop": int(row["amount"]), "percent": percents[i]}
        for i, row in enumerate(category_rows)
    ]

    method_rows = conn.execute(
        """
        SELECT p.name AS name, SUM(e.amount_cop) AS amount
        FROM expenses e JOIN payment_methods p ON p.id = e.payment_method_id
        WHERE e.spent_on BETWEEN ? AND ?
        GROUP BY p.id, p.name ORDER BY amount DESC, p.name ASC
        """,
        (start, end),
    ).fetchall()
    facts.by_payment_method = [
        {"name": row["name"], "amount_cop": int(row["amount"])} for row in method_rows
    ]

    top_rows = conn.execute(
        """
        SELECT e.amount_cop, e.spent_on, c.name AS category_name, e.description
        FROM expenses e JOIN categories c ON c.id = e.category_id
        WHERE e.spent_on BETWEEN ? AND ?
        ORDER BY e.amount_cop DESC, e.id DESC LIMIT ?
        """,
        (start, end, TOP_EXPENSES),
    ).fetchall()
    facts.top_expenses = [
        {
            "amount_cop": int(row["amount_cop"]),
            "spent_on": row["spent_on"],
            "category_name": row["category_name"],
            "description": (row["description"] or "")[:120],
        }
        for row in top_rows
    ]


def _journal_facts_question(
    conn: sqlite3.Connection, facts: FactSet, budget_tokens: int
) -> None:
    """Questions: entries in range, newest first, until the budget is spent."""
    entries = journal_repo.entries_in_range(
        conn, facts.period_start, facts.period_end, oldest_first=False
    )
    facts.journal_entries_considered = len(entries)
    spent = 0
    used: list[JournalExcerpt] = []
    for entry in entries:
        cost = estimate_tokens(entry["text"])
        if spent + cost > budget_tokens and used:
            break
        if spent + cost > budget_tokens and not used:
            trimmed = entry["text"][: int(budget_tokens * CHARS_PER_TOKEN)]
            used.append(JournalExcerpt(entry["written_at"], trimmed))
            spent = budget_tokens
            break
        used.append(JournalExcerpt(entry["written_at"], entry["text"]))
        spent += cost
    facts.journal_excerpts = used
    facts.journal_entries_used = len(used)
    facts.journal_truncated = len(used) < len(entries)


def _journal_facts_summary(
    conn: sqlite3.Connection, facts: FactSet, budget_tokens: int
) -> None:
    """Summaries: one excerpt per day, oldest first, spread across the month.

    Newest-first would make a summary of a month's writing into a summary of its
    last week (KD-10).
    """
    entries = journal_repo.entries_in_range(
        conn, facts.period_start, facts.period_end, oldest_first=True
    )
    facts.journal_entries_considered = len(entries)
    seen_days: set[str] = set()
    per_day: list[dict] = []
    for entry in entries:
        day = entry["written_at"][:10]
        if day in seen_days:
            continue
        seen_days.add(day)
        per_day.append(entry)

    spent = 0
    used: list[JournalExcerpt] = []
    for entry in per_day:
        text = entry["text"][:EXCERPT_CHARS_SUMMARY]
        cost = estimate_tokens(text)
        if spent + cost > budget_tokens:
            break
        used.append(JournalExcerpt(entry["written_at"], text))
        spent += cost
    facts.journal_excerpts = used
    facts.journal_entries_used = len(used)
    facts.journal_truncated = len(used) < len(entries)


def range_has_data(conn: sqlite3.Connection, start: str, end: str) -> bool:
    """Stage 3 of KD-10: the insufficiency pre-check, before any generation.

    Checked across both domains regardless of the routed one — with nothing
    recorded in the range there is nothing to say (11.3), and this costs no
    model call at all.
    """
    expenses = conn.execute(
        "SELECT COUNT(*) AS c FROM expenses WHERE spent_on BETWEEN ? AND ?", (start, end)
    ).fetchone()["c"]
    if expenses:
        return True
    return journal_repo.count_in_range(conn, start, end) > 0


def build_facts(
    conn: sqlite3.Connection, route: Route, *, kind: str = "question"
) -> FactSet:
    """`kind` is "question" or "summary" — journal selection differs (KD-10)."""
    settings = get_settings()
    facts = FactSet(
        period_label=route.period_label,
        period_start=route.period_start,
        period_end=route.period_end,
        period_assumed=route.period_assumed,
        domain=route.domain,
    )
    if route.domain in ("finances", "both"):
        _finance_facts(conn, facts)
    if route.domain in ("journal", "both"):
        if kind == "summary":
            _journal_facts_summary(conn, facts, settings.journal_context_tokens)
        else:
            _journal_facts_question(conn, facts, settings.journal_context_tokens)
    return facts
