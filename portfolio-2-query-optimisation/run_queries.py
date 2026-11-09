"""Run the clinic queries and capture plans before and after indexing."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import DB  # noqa: E402

HERE = Path(__file__).resolve().parent
QUERIES = HERE / "queries.sql"
INDEXES = HERE / "indexes.sql"
EVIDENCE = HERE / "evidence"


def load_queries() -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    name = None
    buf: list[str] = []
    for line in QUERIES.read_text(encoding="utf-8").splitlines():
        if line.startswith("-- QUERY:"):
            if name and buf:
                found.append((name, "\n".join(buf).strip()))
            name = line.split(":", 1)[1].strip()
            buf = []
        elif name and not line.startswith("--"):
            buf.append(line)
    if name and buf:
        found.append((name, "\n".join(buf).strip()))
    return found


def plan(con: sqlite3.Connection, sql: str) -> str:
    rows = con.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
    return "\n".join(f"    {row[3]}" for row in rows)


def render_result(con: sqlite3.Connection, sql: str, limit: int = 12) -> str:
    cur = con.execute(sql)
    headers = [d[0] for d in cur.description]
    rows = cur.fetchall()
    shown = rows[:limit]
    lines = [" | ".join(headers)]
    for row in shown:
        lines.append(" | ".join("" if value is None else str(value) for value in row))
    extra = len(rows) - len(shown)
    if extra:
        lines.append(f"... {extra} further row(s) not shown. Total rows: {len(rows)}.")
    elif not rows:
        lines.append("(no rows)")
    else:
        lines.append(f"Total rows: {len(rows)}.")
    return "\n".join(lines)


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    queries = load_queries()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    before: list[str] = []
    after: list[str] = []
    results: list[str] = []
    try:
        for name, sql in queries:
            before.append(f"## {name}\n{plan(con, sql)}\n")
        con.executescript(INDEXES.read_text(encoding="utf-8"))
        for name, sql in queries:
            after.append(f"## {name}\n{plan(con, sql)}\n")
            results.append(f"## {name}\n{render_result(con, sql)}\n")
        con.commit()
    finally:
        con.close()

    (EVIDENCE / "plans-before-indexes.txt").write_text("\n".join(before), encoding="utf-8")
    (EVIDENCE / "plans-after-indexes.txt").write_text("\n".join(after), encoding="utf-8")
    (EVIDENCE / "query-results.txt").write_text("\n".join(results), encoding="utf-8")
    print(f"Wrote query evidence to {EVIDENCE}")


if __name__ == "__main__":
    main()
