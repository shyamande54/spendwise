import csv
import io
from datetime import date

import pytest

from spendwise.cli import bar, run
from spendwise.store import Store


@pytest.fixture
def store():
    s = Store()
    yield s
    s.close()


def test_add_and_list(store):
    store.add(12.5, "Food", "lunch", date(2026, 1, 3))
    store.add(40, "travel", spent_on=date(2026, 1, 5))
    rows = store.list()
    assert [r.category for r in rows] == ["travel", "food"]  # newest first, normalised
    assert rows[1].note == "lunch"


def test_rejects_bad_input(store):
    with pytest.raises(ValueError):
        store.add(0, "food")
    with pytest.raises(ValueError):
        store.add(5, "   ")


def test_filters(store):
    store.add(10, "food", spent_on=date(2026, 1, 1))
    store.add(20, "food", spent_on=date(2026, 2, 1))
    store.add(30, "rent", spent_on=date(2026, 2, 2))
    assert len(store.list(month="2026-02")) == 2
    assert len(store.list(category="FOOD")) == 2
    assert len(store.list(limit=1)) == 1


def test_totals_and_budget(store):
    store.add(10.10, "food", spent_on=date(2026, 3, 1))
    store.add(20.20, "food", spent_on=date(2026, 3, 2))
    store.add(5, "fun", spent_on=date(2026, 3, 3))
    assert store.totals_by_category("2026-03") == [("food", 30.3), ("fun", 5.0)]
    assert store.total("2026-03") == 35.3
    assert store.get_budget("2026-03") is None
    store.set_budget("2026-03", 100)
    store.set_budget("2026-03", 50)  # upsert
    assert store.get_budget("2026-03") == 50


def test_delete(store):
    e = store.add(1, "misc")
    assert store.delete(e.id) is True
    assert store.delete(e.id) is False


def test_bar():
    assert bar(5, 10, width=10) == "█████░░░░░"
    assert bar(1, 0) == ""


def test_cli_end_to_end(tmp_path):
    db = str(tmp_path / "x.db")
    out = io.StringIO()
    assert run(["--db", db, "add", "250", "groceries", "-d", "2026-04-02", "-n", "weekly"], out) == 0
    assert run(["--db", db, "add", "90", "transport", "-d", "2026-04-03"], out) == 0
    assert run(["--db", db, "budget", "300", "-m", "2026-04"], out) == 0

    out = io.StringIO()
    run(["--db", db, "report", "-m", "2026-04"], out)
    text = out.getvalue()
    assert "groceries" in text and "340.00" in text and "over budget" in text

    csv_path = tmp_path / "out.csv"
    run(["--db", db, "export", str(csv_path)], io.StringIO())
    rows = list(csv.reader(csv_path.open(encoding="utf-8")))
    assert rows[0] == ["id", "date", "category", "amount", "note"]
    assert len(rows) == 3


def test_cli_rejects_bad_month(tmp_path):
    with pytest.raises(SystemExit):
        run(["--db", str(tmp_path / "x.db"), "report", "-m", "2026-13"], io.StringIO())
