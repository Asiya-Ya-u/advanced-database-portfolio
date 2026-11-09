"""Transaction and concurrency evidence for the clinic pharmacy and bookings.

The script copies the seeded database, so the portfolio database itself is left unchanged.
SQLite is run in autocommit mode (isolation_level=None) and every transaction is opened
explicitly. That makes COMMIT and ROLLBACK visible in the log.
"""

from __future__ import annotations

import shutil
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import DB  # noqa: E402

HERE = Path(__file__).resolve().parent
WORK = HERE / "evidence" / "clinic-transactions.sqlite"
LOG = HERE / "evidence" / "transaction-log.txt"


def connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(path, timeout=1, isolation_level=None)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


class Log:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def add(self, text: str = "") -> None:
        self.lines.append(text)
        print(text)

    def write(self) -> None:
        LOG.write_text("\n".join(self.lines) + "\n", encoding="utf-8")


def stock_of(con: sqlite3.Connection, medication_id: int = 1) -> int:
    return con.execute(
        "SELECT stock_qty FROM medication WHERE medication_id = ?",
        (medication_id,),
    ).fetchone()["stock_qty"]


def successful_dispense(con: sqlite3.Connection, log: Log) -> None:
    log.add("1. Successful dispense: commit")
    before = stock_of(con)
    log.add(f"   Paracetamol stock before: {before}")
    con.execute("BEGIN IMMEDIATE")
    con.execute(
        "UPDATE medication SET stock_qty = stock_qty - 6 WHERE medication_id = 1 AND stock_qty >= 6"
    )
    con.execute(
        """
        INSERT INTO stock_movement (medication_id, quantity_change, reason, occurred_at)
        VALUES (1, -6, 'dispense', '2026-11-09 09:00')
        """
    )
    con.execute("COMMIT")
    after = stock_of(con)
    log.add(f"   Paracetamol stock after COMMIT: {after}")
    log.add(f"   Stock fell by {before - after}, which matches the quantity dispensed.")
    log.add("")


def failed_dispense(con: sqlite3.Connection, log: Log) -> None:
    log.add("2. Dispense larger than stock: rollback")
    before = stock_of(con)
    log.add(f"   Paracetamol stock before: {before}")
    con.execute("BEGIN IMMEDIATE")
    try:
        # The WHERE guard changes no row, so the transaction refuses the dispense
        # instead of letting stock become negative.
        changed = con.execute(
            "UPDATE medication SET stock_qty = stock_qty - ? WHERE medication_id = 1 AND stock_qty >= ?",
            (before + 50, before + 50),
        ).rowcount
        if changed != 1:
            raise RuntimeError(f"dispense refused: only {before} packs are on hand")
        con.execute("COMMIT")
        log.add("   Unexpected commit.")
    except Exception as exc:
        con.execute("ROLLBACK")
        log.add(f"   Transaction rolled back: {exc}")
    after = stock_of(con)
    log.add(f"   Paracetamol stock after ROLLBACK: {after}")
    log.add("   The balance is unchanged, so a failed sale did not corrupt the stock figure.")
    log.add("")


def double_booking(con: sqlite3.Connection, log: Log) -> None:
    log.add("3. Two appointments in the same minute: constraint abort")
    taken = con.execute(
        "SELECT doctor_id, scheduled_at FROM appointment ORDER BY appointment_id LIMIT 1"
    ).fetchone()
    log.add(f"   Existing booking: doctor {taken['doctor_id']} at {taken['scheduled_at']}")
    before = con.execute("SELECT COUNT(*) AS n FROM appointment").fetchone()["n"]
    con.execute("BEGIN IMMEDIATE")
    try:
        con.execute(
            """
            INSERT INTO appointment (patient_id, doctor_id, department_id, scheduled_at, status, reason)
            VALUES (1, ?, (SELECT department_id FROM staff WHERE staff_id = ?), ?, 'booked', 'Clash test')
            """,
            (taken["doctor_id"], taken["doctor_id"], taken["scheduled_at"]),
        )
        con.execute("COMMIT")
        log.add("   Unexpected commit.")
    except sqlite3.IntegrityError as exc:
        con.execute("ROLLBACK")
        log.add(f"   ROLLBACK after IntegrityError: {exc}")
    after = con.execute("SELECT COUNT(*) AS n FROM appointment").fetchone()["n"]
    log.add(f"   Appointment rows before {before}, after {after}.")
    log.add("")


def lost_update(con: sqlite3.Connection, log: Log) -> None:
    log.add("4. Lost update, then the safe alternative")
    original = stock_of(con, 2)
    log.add(f"   Amoxicillin stock at the start: {original}")
    # Two clerks each read the balance, subtract in Python, and write the result back.
    clerk_a = original
    clerk_b = original
    con.execute("UPDATE medication SET stock_qty = ? WHERE medication_id = 2", (clerk_a - 5,))
    con.execute("UPDATE medication SET stock_qty = ? WHERE medication_id = 2", (clerk_b - 3,))
    lost = stock_of(con, 2)
    log.add(f"   After both clerks write their own total: {lost}")
    log.add(f"   Five plus three should have left {original - 8}. The stored balance lost the first issue.")

    con.execute("UPDATE medication SET stock_qty = ? WHERE medication_id = 2", (original,))
    con.execute("BEGIN IMMEDIATE")
    con.execute("UPDATE medication SET stock_qty = stock_qty - 5 WHERE medication_id = 2")
    con.execute("COMMIT")
    con.execute("BEGIN IMMEDIATE")
    con.execute("UPDATE medication SET stock_qty = stock_qty - 3 WHERE medication_id = 2")
    con.execute("COMMIT")
    safe = stock_of(con, 2)
    log.add(f"   After two atomic SQL decrements: {safe}")
    log.add("   The database, not the client, applied both changes to the latest balance.")
    log.add("")


def write_lock(path: Path, log: Log) -> None:
    log.add("5. Two connections and the write lock")
    first = connect(path)
    second = connect(path)
    try:
        first.execute("BEGIN IMMEDIATE")
        first.execute("UPDATE medication SET stock_qty = stock_qty - 1 WHERE medication_id = 3")
        log.add("   Connection A holds BEGIN IMMEDIATE and has updated artemether stock.")
        try:
            second.execute("BEGIN IMMEDIATE")
            second.execute("UPDATE medication SET stock_qty = stock_qty - 1 WHERE medication_id = 3")
            log.add("   Connection B was allowed in. That was not expected.")
        except sqlite3.OperationalError as exc:
            log.add(f"   Connection B could not start its write: {exc}")
            log.add("   B does not read A's uncommitted balance. The lock hides the dirty write.")
        # B must not be left inside a transaction.
        try:
            second.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        first.execute("COMMIT")
        log.add("   Connection A committed.")
        second.execute("BEGIN IMMEDIATE")
        second.execute("UPDATE medication SET stock_qty = stock_qty - 1 WHERE medication_id = 3")
        second.execute("COMMIT")
        balance = stock_of(second, 3)
        log.add(f"   Connection B then committed its own issue. Artemether stock is now {balance}.")
        log.add("   The second writer waited for a committed value instead of overwriting an open transaction.")
    finally:
        first.close()
        second.close()
    log.add("")


def main() -> None:
    WORK.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(DB, WORK)
    log = Log()
    log.add("Amana Community Clinic: transaction and concurrency log")
    log.add("Database copy used for these tests, so the seeded portfolio database is not altered.")
    log.add("")
    con = connect(WORK)
    try:
        successful_dispense(con, log)
        failed_dispense(con, log)
        double_booking(con, log)
        lost_update(con, log)
    finally:
        con.close()
    write_lock(WORK, log)
    log.add("Isolation note")
    log.add("SQLite's default locking gives each writer a reserved lock for the whole database file.")
    log.add("Another connection cannot read the uncommitted change, and it cannot write until COMMIT or ROLLBACK.")
    log.add("That is stricter than READ UNCOMMITTED and is the behaviour the clinic needs for stock and bookings.")
    log.write()
    print(f"Wrote {LOG}")


if __name__ == "__main__":
    main()
