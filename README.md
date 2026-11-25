<h1 align="center">💸 SpendWise</h1>

<p align="center">
  A tiny command-line expense tracker backed by SQLite. Pure Python, zero dependencies.
</p>

<p align="center">
  <a href="https://github.com/shyamande54/spendwise/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/shyamande54/spendwise/ci.yml?branch=main&style=for-the-badge&label=tests" alt="CI" /></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/storage-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
  <img src="https://img.shields.io/github/license/shyamande54/spendwise?style=for-the-badge&color=1e3a8a" alt="License" />
</p>

---

```text
$ spendwise report
Spending report · 2026-11

  rent           ████████████████████████   2,200.00
  groceries      ██████████████░░░░░░░░░░   1,250.00
  transport      █████░░░░░░░░░░░░░░░░░░░     450.00
  fun            ███░░░░░░░░░░░░░░░░░░░░░     300.00

  TOTAL                                     4,200.00
  BUDGET         ████████████████████████   4,000.00  105% used · ⚠ over budget
```

## ✨ Features

- ➕ **Add, list and delete** expenses with categories, notes and dates
- 🔎 **Filter** by month, category or count
- 📊 **Reports** with per-category terminal bar charts
- 🎯 **Monthly budgets** with an over/under indicator
- 📤 **CSV export** for spreadsheets
- 🧪 **Tested** with pytest on Python 3.10–3.13 via GitHub Actions

## Quick start

```bash
git clone https://github.com/shyamande54/spendwise.git
cd spendwise
pip install -e .

spendwise add 1250 groceries -n "weekly shop"
spendwise add 450 transport -d 2026-11-20
spendwise budget 4000
spendwise report
```

No install? Run it as a module: `python -m spendwise report`.

## 📖 Commands

| Command | What it does | Example |
|---|---|---|
| `add AMOUNT CATEGORY` | Record an expense (`-n` note, `-d` date) | `spendwise add 99 food -n pizza` |
| `list` | Show recent expenses (`-m` month, `-c` category, `-l` limit) | `spendwise list -m 2026-11 -c food` |
| `delete ID` | Remove an expense | `spendwise delete 4` |
| `report` | Category breakdown and budget check (`-m` month) | `spendwise report -m 2026-10` |
| `budget AMOUNT` | Set the monthly budget (`-m` month) | `spendwise budget 5000` |
| `export FILE` | Write expenses to CSV (`-m` month) | `spendwise export nov.csv -m 2026-11` |

Data is stored in `~/.spendwise/spendwise.db`. Override it with `--db PATH` or the `SPENDWISE_DB` environment variable.

## 🏗️ Design

```
spendwise/
├── store.py   # SQLite persistence: schema, queries, budgets
├── cli.py     # argparse CLI, formatting, terminal bar charts
└── __main__.py
tests/
└── test_spendwise.py
```

- **`Store`** owns every SQL query, so the CLI never touches the database directly. The tests run against an in-memory SQLite DB.
- Amounts are validated (`> 0`) in both the CLI and a database `CHECK` constraint.
- Budgets use an `UPSERT`, so setting one twice simply updates it.

## 🧪 Running tests

```bash
pip install -e ".[dev]"
pytest -v
```

## 📄 License

[MIT](LICENSE)
