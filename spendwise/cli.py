"""Command-line interface for SpendWise."""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from datetime import date
from pathlib import Path

from . import __version__
from .store import Store

DEFAULT_DB = Path(os.environ.get("SPENDWISE_DB", Path.home() / ".spendwise" / "spendwise.db"))
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def month_arg(value: str) -> str:
    if not MONTH_RE.match(value):
        raise argparse.ArgumentTypeError("month must look like YYYY-MM")
    return value


def date_arg(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError("date must look like YYYY-MM-DD") from None


def positive(value: str) -> float:
    try:
        n = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be a number") from None
    if n <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return n


def money(n: float) -> str:
    return f"{n:,.2f}"


def bar(value: float, maximum: float, width: int = 24) -> str:
    if maximum <= 0:
        return ""
    filled = round(width * value / maximum)
    return "█" * filled + "░" * (width - filled)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="spendwise", description="Track expenses from your terminal.")
    p.add_argument("--db", type=Path, default=DEFAULT_DB, help=f"database file (default: {DEFAULT_DB})")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("add", help="record an expense")
    a.add_argument("amount", type=positive)
    a.add_argument("category")
    a.add_argument("-n", "--note", default="")
    a.add_argument("-d", "--date", type=date_arg, default=None, help="YYYY-MM-DD (default: today)")

    ls = sub.add_parser("list", help="list expenses")
    ls.add_argument("-m", "--month", type=month_arg)
    ls.add_argument("-c", "--category")
    ls.add_argument("-l", "--limit", type=int, default=20)

    rm = sub.add_parser("delete", help="delete an expense by id")
    rm.add_argument("id", type=int)

    r = sub.add_parser("report", help="spending by category with a budget check")
    r.add_argument("-m", "--month", type=month_arg, default=date.today().strftime("%Y-%m"))

    b = sub.add_parser("budget", help="set a monthly budget")
    b.add_argument("amount", type=positive)
    b.add_argument("-m", "--month", type=month_arg, default=date.today().strftime("%Y-%m"))

    e = sub.add_parser("export", help="export expenses to CSV")
    e.add_argument("file", type=Path)
    e.add_argument("-m", "--month", type=month_arg)
    return p


def run(argv: list[str] | None = None, out=sys.stdout) -> int:
    args = build_parser().parse_args(argv)
    store = Store(args.db)
    try:
        return COMMANDS[args.command](store, args, out)
    finally:
        store.close()


def cmd_add(store: Store, args, out) -> int:
    e = store.add(args.amount, args.category, args.note, args.date)
    print(f"✔ Added #{e.id}: {money(e.amount)} on {e.category} ({e.spent_on})", file=out)
    return 0


def cmd_list(store: Store, args, out) -> int:
    rows = store.list(args.month, args.category, args.limit)
    if not rows:
        print("No expenses found.", file=out)
        return 0
    print(f"{'ID':>4}  {'DATE':<10}  {'CATEGORY':<14}  {'AMOUNT':>10}  NOTE", file=out)
    print("─" * 60, file=out)
    for e in rows:
        print(f"{e.id:>4}  {e.spent_on.isoformat():<10}  {e.category:<14}  {money(e.amount):>10}  {e.note}", file=out)
    return 0


def cmd_delete(store: Store, args, out) -> int:
    if store.delete(args.id):
        print(f"✔ Deleted #{args.id}", file=out)
        return 0
    print(f"✘ No expense with id {args.id}", file=out)
    return 1


def cmd_report(store: Store, args, out) -> int:
    totals = store.totals_by_category(args.month)
    print(f"Spending report · {args.month}\n", file=out)
    if not totals:
        print("No expenses this month.", file=out)
        return 0
    top = totals[0][1]
    for cat, amt in totals:
        print(f"  {cat:<14} {bar(amt, top)} {money(amt):>10}", file=out)
    total = store.total(args.month)
    print(f"\n  {'TOTAL':<14} {'':<24} {money(total):>10}", file=out)

    budget = store.get_budget(args.month)
    if budget:
        pct = total / budget * 100
        status = "✔ within budget" if total <= budget else "⚠ over budget"
        print(f"  {'BUDGET':<14} {bar(min(total, budget), budget)} {money(budget):>10}  {pct:.0f}% used · {status}", file=out)
    return 0


def cmd_budget(store: Store, args, out) -> int:
    store.set_budget(args.month, args.amount)
    print(f"✔ Budget for {args.month} set to {money(args.amount)}", file=out)
    return 0


def cmd_export(store: Store, args, out) -> int:
    rows = store.list(args.month)
    with open(args.file, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "date", "category", "amount", "note"])
        for e in rows:
            w.writerow([e.id, e.spent_on.isoformat(), e.category, f"{e.amount:.2f}", e.note])
    print(f"✔ Exported {len(rows)} expenses to {args.file}", file=out)
    return 0


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "delete": cmd_delete,
    "report": cmd_report,
    "budget": cmd_budget,
    "export": cmd_export,
}


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(run())


if __name__ == "__main__":
    main()
