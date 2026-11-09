"""Two shards, each with a primary and a replica, for Amana Community Clinic.

Patients are placed by patient_id modulo 2. A payment stays on the patient's shard,
so the money update does not need a distributed transaction. A clinic-wide count
has to ask both shards. The replica is deliberately left behind for one write so
the log shows eventual consistency, then it is caught up.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import DB  # noqa: E402

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"

DDL = """
CREATE TABLE patient (
    patient_id INTEGER PRIMARY KEY,
    hospital_no TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL
);
CREATE TABLE payment (
    payment_id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    amount_kobo INTEGER NOT NULL,
    reference_no TEXT NOT NULL UNIQUE
);
"""


class Node:
    def __init__(self, path: Path) -> None:
        if path.exists():
            path.unlink()
        self.con = sqlite3.connect(path)
        self.con.executescript(DDL)

    def close(self) -> None:
        self.con.close()


class Shard:
    def __init__(self, name: str, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        self.name = name
        self.primary = Node(folder / f"{name}-primary.sqlite")
        self.replica = Node(folder / f"{name}-replica.sqlite")
        self.pending: list[tuple[str, tuple]] = []
        self.online = True

    def write(self, sql: str, params: tuple = ()) -> None:
        if not self.online:
            raise RuntimeError(f"{self.name} primary is unavailable")
        self.primary.con.execute(sql, params)
        self.primary.con.commit()
        self.pending.append((sql, params))

    def catch_up(self) -> int:
        applied = len(self.pending)
        for sql, params in self.pending:
            self.replica.con.execute(sql, params)
        self.replica.con.commit()
        self.pending.clear()
        return applied

    def read_primary(self, sql: str, params: tuple = ()) -> list[tuple]:
        if not self.online:
            raise RuntimeError(f"{self.name} primary is unavailable")
        return self.primary.con.execute(sql, params).fetchall()

    def read_replica(self, sql: str, params: tuple = ()) -> list[tuple]:
        return self.replica.con.execute(sql, params).fetchall()

    def close(self) -> None:
        self.primary.close()
        self.replica.close()


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    folder = EVIDENCE / "nodes"
    shards = [Shard("shard-0", folder), Shard("shard-1", folder)]
    lines: list[str] = []

    def say(text: str = "") -> None:
        lines.append(text)
        print(text)

    source = sqlite3.connect(DB)
    source.row_factory = sqlite3.Row
    patients = source.execute(
        "SELECT patient_id, hospital_no, full_name FROM patient ORDER BY patient_id"
    ).fetchall()
    payments = source.execute(
        """
        SELECT pay.payment_id, i.patient_id, pay.amount_kobo, pay.reference_no
        FROM payment pay
        JOIN invoice i ON i.invoice_id = pay.invoice_id
        ORDER BY pay.payment_id
        """
    ).fetchall()
    source.close()

    say("Placement of the first eight patients")
    for patient in patients:
        shard = shards[patient["patient_id"] % 2]
        shard.write(
            "INSERT INTO patient VALUES (?, ?, ?)",
            (patient["patient_id"], patient["hospital_no"], patient["full_name"]),
        )
        if patient["patient_id"] <= 8:
            say(
                f"  {patient['hospital_no']} {patient['full_name']} -> {shard.name}"
            )
    for shard in shards:
        applied = shard.catch_up()
        say(f"{shard.name} replica caught up {applied} patient writes.")

    say("")
    say("A new patient is written to the primary and is not yet on the replica")
    shards[0].write(
        "INSERT INTO patient VALUES (?, ?, ?)",
        (5001, "ACC-5001", "Test Patient Holding"),
    )
    primary_count = shards[0].read_primary("SELECT COUNT(*) FROM patient")[0][0]
    replica_count = shards[0].read_replica("SELECT COUNT(*) FROM patient")[0][0]
    say(f"  shard-0 primary count: {primary_count}")
    say(f"  shard-0 replica count: {replica_count}")
    say("  The replica is behind by one row. A report that reads the replica is stale.")
    caught = shards[0].catch_up()
    replica_count = shards[0].read_replica("SELECT COUNT(*) FROM patient")[0][0]
    say(f"  After applying {caught} pending write(s), replica count: {replica_count}")

    say("")
    say("Payments stay on the shard that holds the patient")
    for payment in payments:
        shard = shards[payment["patient_id"] % 2]
        shard.write(
            "INSERT INTO payment VALUES (?, ?, ?, ?)",
            (payment["payment_id"], payment["patient_id"], payment["amount_kobo"], payment["reference_no"]),
        )
    for shard in shards:
        shard.catch_up()
        total = shard.read_primary("SELECT COALESCE(SUM(amount_kobo), 0) FROM payment")[0][0]
        say(f"  {shard.name} holds NGN {total / 100:.2f} of recorded receipts.")

    say("")
    say("Scatter-gather: how many patients does the clinic have?")
    # The holding patient is a demonstration row, so the clinical count uses hospital numbers
    # that came from the original register.
    total_patients = 0
    for shard in shards:
        count = shard.read_primary(
            "SELECT COUNT(*) FROM patient WHERE hospital_no NOT LIKE 'ACC-5%'"
        )[0][0]
        say(f"  {shard.name} answers {count}")
        total_patients += count
    say(f"  Combined answer: {total_patients}")

    say("")
    say("Shard-1 primary is taken offline")
    shards[1].online = False
    try:
        shards[1].read_primary("SELECT COUNT(*) FROM patient")
        say("  Shard-1 still answered. That was not expected.")
    except RuntimeError as exc:
        say(f"  {exc}")
    still = shards[0].read_primary("SELECT COUNT(*) FROM patient")[0][0]
    say(f"  Shard-0 still answers. Its primary count is {still}.")
    say("  Patients on shard-1 cannot pay or be registered until that primary returns,")
    say("  but the outage does not stop the other half of the register.")
    replica_answer = shards[1].read_replica("SELECT COUNT(*) FROM patient")[0][0]
    say(f"  Shard-1 replica can still be read for enquiry: {replica_answer} patients.")
    say("  Those reads may be stale, so the replica is not used to take a payment.")

    for shard in shards:
        shard.close()

    text = "\n".join(lines) + "\n"
    (EVIDENCE / "cluster-log.txt").write_text(text, encoding="utf-8")
    print(f"Wrote {EVIDENCE / 'cluster-log.txt'}")


if __name__ == "__main__":
    main()
