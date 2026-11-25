"""Persistence layer: all SQLite access lives here."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS expenses (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    amount    REAL    NOT NULL CHECK (amount > 0),
    category  TEXT    NOT NULL,
    note      TEXT    NOT NULL DEFAULT '',
    spent_on  TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_expenses_spent_on ON expenses (spent_on);
CREATE TABLE IF NOT EXISTS budgets (
    month   TEXT PRIMARY KEY,   -- YYYY-MM
    amount  REAL NOT NULL CHECK (amount > 0)
);
"""


@dataclass(frozen=True)
class Expense:
    id: int
    amount: float
    category: str
    note: str
    spent_on: date


class Store:
    def __init__(self, path: str | Path = ":memory:") -> None:
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    # --- expenses ---------------------------------------------------------
    def add(self, amount: float, category: str, note: str = "", spent_on: date | None = None) -> Expense:
        if amount <= 0:
            raise ValueError("amount must be positive")
        category = category.strip().lower()
        if not category:
            raise ValueError("category is required")
        spent_on = spent_on or date.today()
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO expenses (amount, category, note, spent_on) VALUES (?, ?, ?, ?)",
                (round(amount, 2), category, note.strip(), spent_on.isoformat()),
            )
        return Expense(cur.lastrowid, round(amount, 2), category, note.strip(), spent_on)

    def delete(self, expense_id: int) -> bool:
        with self.conn:
            cur = self.conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        return cur.rowcount > 0

    def list(self, month: str | None = None, category: str | None = None, limit: int | None = None) -> list[Expense]:
        sql = "SELECT * FROM expenses WHERE 1=1"
        args: list = []
        if month:
            sql += " AND substr(spent_on, 1, 7) = ?"
            args.append(month)
        if category:
            sql += " AND category = ?"
            args.append(category.strip().lower())
        sql += " ORDER BY spent_on DESC, id DESC"
        if limit:
            sql += " LIMIT ?"
            args.append(limit)
        return [self._row(r) for r in self.conn.execute(sql, args)]

    def totals_by_category(self, month: str | None = None) -> list[tuple[str, float]]:
        sql = "SELECT category, ROUND(SUM(amount), 2) AS total FROM expenses"
        args: list = []
        if month:
            sql += " WHERE substr(spent_on, 1, 7) = ?"
            args.append(month)
        sql += " GROUP BY category ORDER BY total DESC"
        return [(r["category"], r["total"]) for r in self.conn.execute(sql, args)]

    def total(self, month: str | None = None) -> float:
        return round(sum(t for _, t in self.totals_by_category(month)), 2)

    # --- budgets ----------------------------------------------------------
    def set_budget(self, month: str, amount: float) -> None:
        if amount <= 0:
            raise ValueError("budget must be positive")
        with self.conn:
            self.conn.execute(
                "INSERT INTO budgets (month, amount) VALUES (?, ?) "
                "ON CONFLICT(month) DO UPDATE SET amount = excluded.amount",
                (month, round(amount, 2)),
            )

    def get_budget(self, month: str) -> float | None:
        row = self.conn.execute("SELECT amount FROM budgets WHERE month = ?", (month,)).fetchone()
        return row["amount"] if row else None

    @staticmethod
    def _row(r: sqlite3.Row) -> Expense:
        return Expense(r["id"], r["amount"], r["category"], r["note"], date.fromisoformat(r["spent_on"]))
