-- 0001_init — the seven tables plus two alias tables (design: Data model).
-- Nothing is ever hard-deleted by the system: categories and payment methods
-- archive; expenses and journal entries go only by explicit user action (14.3).

CREATE TABLE meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    archived_at TEXT,
    created_at  TEXT    NOT NULL
);
-- Uniqueness on name among non-archived rows only (design: Data model).
CREATE UNIQUE INDEX ux_categories_active_name
    ON categories(name) WHERE archived_at IS NULL;

CREATE TABLE payment_methods (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    archived_at TEXT,
    created_at  TEXT    NOT NULL
);
CREATE UNIQUE INDEX ux_payment_methods_active_name
    ON payment_methods(name) WHERE archived_at IS NULL;

-- Alias tables: data, not code (R6). Every alias points at a row that exists,
-- which is what keeps 9.3 true by construction.
CREATE TABLE category_aliases (
    target_id INTEGER NOT NULL REFERENCES categories(id),
    alias     TEXT    NOT NULL,
    PRIMARY KEY (target_id, alias)
);
CREATE INDEX ix_category_aliases_alias ON category_aliases(alias);

CREATE TABLE payment_method_aliases (
    target_id INTEGER NOT NULL REFERENCES payment_methods(id),
    alias     TEXT    NOT NULL,
    PRIMARY KEY (target_id, alias)
);
CREATE INDEX ix_payment_method_aliases_alias ON payment_method_aliases(alias);

CREATE TABLE expenses (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    amount_cop        INTEGER NOT NULL CHECK (amount_cop > 0),
    category_id       INTEGER NOT NULL REFERENCES categories(id),
    payment_method_id INTEGER NOT NULL REFERENCES payment_methods(id),
    spent_on          TEXT    NOT NULL,  -- YYYY-MM-DD, local (APP_TZ)
    description       TEXT,
    source            TEXT    NOT NULL DEFAULT 'manual'
                              CHECK (source IN ('manual', 'voice')),
    created_at        TEXT    NOT NULL,
    updated_at        TEXT    NOT NULL
);
CREATE INDEX ix_expenses_spent_on ON expenses(spent_on DESC, created_at DESC);
CREATE INDEX ix_expenses_category ON expenses(category_id);
CREATE INDEX ix_expenses_method   ON expenses(payment_method_id);

CREATE TABLE journal_entries (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    text       TEXT NOT NULL,
    written_at TEXT NOT NULL,  -- ISO-8601 local with offset
    source     TEXT NOT NULL DEFAULT 'manual'
                    CHECK (source IN ('manual', 'voice')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX ix_journal_written_at ON journal_entries(written_at DESC, id DESC);

CREATE TABLE summaries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    period_kind     TEXT NOT NULL DEFAULT 'month' CHECK (period_kind = 'month'),
    period_key      TEXT NOT NULL UNIQUE,          -- YYYY-MM
    -- No 'pending' status: a month that should have a summary and has no row
    -- *is* pending, which is what the catch-up scan looks for (KD-12).
    status          TEXT NOT NULL
                         CHECK (status IN ('generating', 'ready', 'empty', 'failed')),
    text            TEXT,
    facts_json      TEXT,
    model           TEXT,
    error_code      TEXT,
    generated_at    TEXT,
    attempts        INTEGER NOT NULL DEFAULT 0,
    last_attempt_at TEXT,
    created_at      TEXT NOT NULL
);

CREATE TABLE insight_jobs (
    id             TEXT PRIMARY KEY,               -- uuid
    question       TEXT NOT NULL,
    source         TEXT NOT NULL DEFAULT 'text' CHECK (source IN ('text', 'voice')),
    status         TEXT NOT NULL
                        CHECK (status IN ('queued', 'running', 'done', 'failed', 'cancelled')),
    partial_answer TEXT,
    answer         TEXT,
    facts_json     TEXT,
    error_code     TEXT,
    created_at     TEXT NOT NULL,
    started_at     TEXT,
    finished_at    TEXT
);
CREATE INDEX ix_insight_jobs_status ON insight_jobs(status);
