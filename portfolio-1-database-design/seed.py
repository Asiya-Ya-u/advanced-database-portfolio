"""Build the Amana Community Clinic database from schema.sql.

The sample is deterministic (seed 8103) so every query result in the portfolio
can be reproduced with `python run_all.py`.
"""

from __future__ import annotations

import datetime
import random
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import DB  # noqa: E402

SCHEMA = Path(__file__).with_name("schema.sql")

FIRST_F = ["Amina", "Fatima", "Hauwa", "Maryam", "Zainab", "Halima", "Nafisa", "Khadija", "Asma'u", "Safiya"]
FIRST_M = ["Musa", "Ibrahim", "Yusuf", "Ahmad", "Sadiq", "Usman", "Bashir", "Kabir", "Lawal", "Garba"]
LAST = ["Musa", "Bello", "Danladi", "Yusuf", "Sani", "Lawal", "Abubakar", "Umar", "Isa", "Haruna", "Tijjani", "Adamu", "Shehu", "Aliyu"]
AREAS = ["Gwale", "Nassarawa", "Tarauni", "Dala", "Fagge", "Kumbotso", "Ungogo"]
REASONS = [
    "Fever and headache",
    "Antenatal visit",
    "Child with cough",
    "Abdominal pain",
    "Follow-up of diabetes",
    "Skin rash",
    "Routine check",
    "Wound dressing",
]

DIAGNOSES = [
    ("B50.9", "Plasmodium falciparum malaria, unspecified"),
    ("J06.9", "Acute upper respiratory infection, unspecified"),
    ("A09", "Infectious gastroenteritis"),
    ("N39.0", "Urinary tract infection"),
    ("J45.9", "Asthma, unspecified"),
    ("E11.9", "Type 2 diabetes mellitus without complications"),
    ("Z34.9", "Supervision of normal pregnancy, unspecified"),
    ("L30.9", "Dermatitis, unspecified"),
]

# Opening quantities are high enough that the seeded dispenses cannot drive stock below zero.
# Reorder levels are calculated after dispensing so that a few items still need to be ordered.
MEDICATIONS = [
    ("Paracetamol 500 mg", "tablet", 2000, 800),
    ("Amoxicillin 250 mg", "capsule", 8000, 800),
    ("Artemether-Lumefantrine", "tablet", 15000, 800),
    ("Oral rehydration salts", "sachet", 3000, 800),
    ("Ferrous sulphate", "tablet", 2500, 800),
    ("Metronidazole 200 mg", "tablet", 4000, 800),
    ("Ibuprofen 200 mg", "tablet", 3000, 800),
    ("Zinc sulphate", "tablet", 3500, 800),
    ("Salbutamol inhaler", "inhaler", 25000, 800),
    ("Albendazole 400 mg", "tablet", 5000, 800),
    ("Folic acid 5 mg", "tablet", 2000, 800),
    ("Cough syrup", "bottle", 12000, 800),
]

LAB_TESTS = [
    ("MRDT", "Malaria rapid diagnostic test", 150000),
    ("PCV", "Packed cell volume", 100000),
    ("URINE", "Urinalysis", 120000),
    ("PT", "Pregnancy test", 100000),
    ("RBS", "Random blood sugar", 150000),
    ("FBC", "Full blood count", 350000),
    ("WIDAL", "Widal test", 200000),
    ("STOOL", "Stool microscopy", 150000),
]


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    return con


def seed(con: sqlite3.Connection) -> None:
    rng = random.Random(8103)

    departments = [
        (1, "General Outpatient", "Block A"),
        (2, "Maternal Health", "Block B"),
        (3, "Paediatrics", "Block B"),
        (4, "Laboratory", "Block C"),
        (5, "Pharmacy", "Block C"),
    ]
    con.executemany("INSERT INTO department VALUES (?, ?, ?)", departments)

    staff = [
        (1, 1, "Dr Hauwa Bello", "doctor", "MDCN-44120", "08030000001"),
        (2, 1, "Dr Musa Danladi", "doctor", "MDCN-44188", "08030000002"),
        (3, 2, "Dr Amina Yusuf", "doctor", "MDCN-45011", "08030000003"),
        (4, 2, "Dr Ibrahim Sani", "doctor", "MDCN-45090", "08030000004"),
        (5, 3, "Dr Fatima Lawal", "doctor", "MDCN-46201", "08030000005"),
        (6, 3, "Dr Yusuf Garba", "doctor", "MDCN-46277", "08030000006"),
        (7, 1, "Nurse Maryam Abubakar", "nurse", "NMCN-22001", "08030000007"),
        (8, 2, "Nurse Halima Umar", "nurse", "NMCN-22048", "08030000008"),
        (9, 5, "Pharm Sadiq Bala", "pharmacist", "PCN-11820", "08030000009"),
        (10, 5, "Pharm Zainab Isa", "pharmacist", "PCN-11864", "08030000010"),
        (11, 4, "Nafisa Haruna", "lab_scientist", "MLSCN-3301", "08030000011"),
        (12, 4, "Ahmad Tijjani", "lab_scientist", "MLSCN-3344", "08030000012"),
    ]
    con.executemany("INSERT INTO staff VALUES (?, ?, ?, ?, ?, ?)", staff)
    doctors = [row for row in staff if row[3] == "doctor"]

    patients = []
    # Patient 10 is fixed so the history query is stable. Her name is also used
    # by the full_name lookup, so it must stay unique in the generated list.
    used_names = {"Amina Musa"}
    for i in range(1, 121):
        if i == 10:
            full_name, sex = "Amina Musa", "F"
        else:
            sex = "F" if rng.random() < 0.58 else "M"
            while True:
                first = rng.choice(FIRST_F if sex == "F" else FIRST_M)
                full_name = f"{first} {rng.choice(LAST)}"
                if full_name not in used_names:
                    used_names.add(full_name)
                    break
        year = rng.randint(1972, 2022)
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        patients.append(
            (
                i,
                f"ACC-{i:04d}",
                full_name,
                sex,
                f"{year:04d}-{month:02d}-{day:02d}",
                f"080{rng.randint(10000000, 99999999)}",
                f"{rng.randint(1, 40)} {rng.choice(AREAS)}, Kano",
                f"2026-0{rng.randint(1, 8)}-{rng.randint(1, 28):02d}",
            )
        )
    con.executemany(
        "INSERT INTO patient VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        patients,
    )

    con.executemany(
        "INSERT INTO medication (medication_id, name, form, unit_price_kobo, stock_qty, reorder_level) "
        "VALUES (?, ?, ?, ?, ?, 0)",
        [(i, name, form, price, opening) for i, (name, form, price, opening) in enumerate(MEDICATIONS, start=1)],
    )
    con.executemany(
        "INSERT INTO stock_movement (medication_id, quantity_change, reason, occurred_at) "
        "VALUES (?, ?, 'opening', '2026-09-01')",
        [(i, opening) for i, (*_, opening) in enumerate(MEDICATIONS, start=1)],
    )

    con.executemany("INSERT INTO lab_test VALUES (?, ?, ?, ?)", [(i, *row) for i, row in enumerate(LAB_TESTS, start=1)])

    # Weekday clinic dates from 1 September to 20 November 2026.
    days = []
    for month, last in ((9, 30), (10, 31), (11, 20)):
        for day in range(1, last + 1):
            dt = datetime.date(2026, month, day)
            if dt.weekday() < 5:
                days.append(dt.isoformat())

    slots: dict[int, set[str]] = {d[0]: set() for d in doctors}

    def take_slot(doctor_id: int, day: str) -> str:
        hour, minute = 8, 0
        while True:
            stamp = f"{day} {hour:02d}:{minute:02d}"
            if stamp not in slots[doctor_id]:
                slots[doctor_id].add(stamp)
                return stamp
            minute += 20
            if minute >= 60:
                minute = 0
                hour += 1
                if hour > 15:
                    raise RuntimeError("doctor slot overflow")

    appointment_id = 0
    encounter_id = 0
    diagnosis_id = 0
    prescription_id = 0
    item_id = 0
    lab_order_id = 0
    invoice_id = 0
    line_id = 0
    payment_id = 0
    movement_id = con.execute("SELECT COALESCE(MAX(movement_id), 0) FROM stock_movement").fetchone()[0]

    doctor_by_dept = {}
    for d in doctors:
        doctor_by_dept.setdefault(d[1], []).append(d[0])

    for patient in patients:
        pid, sex = patient[0], patient[3]
        visits = rng.randint(2, 5)
        chosen_days = rng.sample(days, visits)
        chosen_days.sort()
        for day in chosen_days:
            if sex == "F" and rng.random() < 0.28:
                dept = 2
                reason = "Antenatal visit"
            elif rng.random() < 0.22:
                dept = 3
                reason = "Child with cough"
            else:
                dept = 1
                reason = rng.choice(REASONS)
            doctor_id = rng.choice(doctor_by_dept[dept])
            appointment_id += 1
            roll = rng.random()
            if roll < 0.62:
                status = "completed"
            elif roll < 0.74:
                status = "booked"
            elif roll < 0.82:
                status = "checked_in"
            elif roll < 0.92:
                status = "cancelled"
            else:
                status = "no_show"
            scheduled = take_slot(doctor_id, day)
            con.execute(
                "INSERT INTO appointment VALUES (?, ?, ?, ?, ?, ?, ?)",
                (appointment_id, pid, doctor_id, dept, scheduled, status, reason),
            )
            if status not in ("completed", "checked_in"):
                continue

            encounter_id += 1
            con.execute(
                "INSERT INTO encounter VALUES (?, ?, ?, ?, ?, ?)",
                (
                    encounter_id,
                    appointment_id,
                    pid,
                    doctor_id,
                    scheduled,
                    f"Seen in clinic. Presenting complaint: {reason.lower()}.",
                ),
            )
            diagnosis_id += 1
            if dept == 2:
                code, desc = DIAGNOSES[6]
            elif dept == 3:
                code, desc = rng.choice(DIAGNOSES[:3])
            else:
                code, desc = rng.choice(DIAGNOSES)
            con.execute(
                "INSERT INTO diagnosis VALUES (?, ?, ?, ?, 1)",
                (diagnosis_id, encounter_id, code, desc),
            )

            # Most completed visits receive a short prescription.
            if status == "completed" and rng.random() < 0.75:
                prescription_id += 1
                con.execute(
                    "INSERT INTO prescription VALUES (?, ?, ?, 'dispensed')",
                    (prescription_id, encounter_id, scheduled),
                )
                for med_id in rng.sample(range(1, len(MEDICATIONS) + 1), k=rng.randint(1, 2)):
                    qty = rng.randint(1, 3)
                    item_id += 1
                    dose = "one tablet three times daily for 3 days"
                    con.execute(
                        "INSERT INTO prescription_item VALUES (?, ?, ?, ?, ?)",
                        (item_id, prescription_id, med_id, dose, qty),
                    )
                    movement_id += 1
                    con.execute(
                        "INSERT INTO stock_movement (movement_id, medication_id, quantity_change, reason, occurred_at, prescription_id) "
                        "VALUES (?, ?, ?, 'dispense', ?, ?)",
                        (movement_id, med_id, -qty, scheduled, prescription_id),
                    )
                    con.execute(
                        "UPDATE medication SET stock_qty = stock_qty + ? WHERE medication_id = ?",
                        (-qty, med_id),
                    )

            if status == "completed" and rng.random() < 0.45:
                test_id = rng.randint(1, len(LAB_TESTS))
                lab_order_id += 1
                if rng.random() < 0.7:
                    lab_status, result, resulted = "resulted", "See laboratory worksheet", scheduled
                elif scheduled < "2026-10-01":
                    lab_status, result, resulted = "ordered", None, None
                else:
                    lab_status, result, resulted = "sample_taken", None, None
                con.execute(
                    "INSERT INTO lab_order VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (lab_order_id, encounter_id, test_id, scheduled, lab_status, result, resulted),
                )

            if status == "completed":
                invoice_id += 1
                paid = rng.random() < 0.78
                con.execute(
                    "INSERT INTO invoice VALUES (?, ?, ?, ?, ?)",
                    (invoice_id, pid, encounter_id, scheduled, "paid" if paid else "open"),
                )
                line_id += 1
                con.execute(
                    "INSERT INTO invoice_line VALUES (?, ?, ?, ?)",
                    (line_id, invoice_id, "Consultation", 250000),
                )
                items = con.execute(
                    "SELECT m.name, m.unit_price_kobo, pi.quantity "
                    "FROM prescription_item pi JOIN medication m ON m.medication_id = pi.medication_id "
                    "WHERE pi.prescription_id = (SELECT prescription_id FROM prescription WHERE encounter_id = ?)",
                    (encounter_id,),
                ).fetchall()
                total = 250000
                for name, price, qty in items:
                    line_id += 1
                    con.execute(
                        "INSERT INTO invoice_line VALUES (?, ?, ?, ?)",
                        (line_id, invoice_id, f"{name} x {qty}", price * qty),
                    )
                    total += price * qty
                tests = con.execute(
                    "SELECT t.name, t.price_kobo FROM lab_order lo "
                    "JOIN lab_test t ON t.lab_test_id = lo.lab_test_id WHERE lo.encounter_id = ?",
                    (encounter_id,),
                ).fetchall()
                for name, price in tests:
                    line_id += 1
                    con.execute(
                        "INSERT INTO invoice_line VALUES (?, ?, ?, ?)",
                        (line_id, invoice_id, name, price),
                    )
                    total += price
                if paid:
                    payment_id += 1
                    method = rng.choice(("cash", "transfer", "card"))
                    con.execute(
                        "INSERT INTO payment VALUES (?, ?, ?, ?, ?, ?)",
                        (payment_id, invoice_id, total, method, scheduled, f"RCPT-{payment_id:05d}"),
                    )

    # Keep the published queries from returning an empty illustration.
    doctor_day = con.execute(
        """
        SELECT COUNT(*) FROM appointment
        WHERE doctor_id = 1 AND scheduled_at >= '2026-10-06' AND scheduled_at < '2026-10-08'
        """
    ).fetchone()[0]
    if doctor_day == 0:
        con.execute(
            """
            UPDATE appointment
            SET scheduled_at = '2026-10-06 07:40', status = 'booked', reason = 'Fever and headache'
            WHERE appointment_id = (
                SELECT appointment_id FROM appointment WHERE doctor_id = 1 ORDER BY appointment_id LIMIT 1
            )
            """
        )
        con.execute(
            """
            UPDATE encounter SET started_at = '2026-10-06 07:40'
            WHERE appointment_id = (
                SELECT appointment_id FROM appointment WHERE scheduled_at = '2026-10-06 07:40'
            )
            """
        )
    if con.execute("SELECT COUNT(*) FROM encounter WHERE patient_id = 10").fetchone()[0] == 0:
        con.execute(
            """
            UPDATE appointment
            SET status = 'completed'
            WHERE appointment_id = (
                SELECT appointment_id FROM appointment WHERE patient_id = 10 ORDER BY scheduled_at LIMIT 1
            )
            """
        )
        appt = con.execute(
            "SELECT appointment_id, doctor_id, scheduled_at, reason FROM appointment WHERE patient_id = 10 ORDER BY scheduled_at LIMIT 1"
        ).fetchone()
        con.execute(
            "INSERT INTO encounter VALUES (NULL, ?, 10, ?, ?, ?)",
            (appt[0], appt[1], appt[2], f"Seen in clinic. Presenting complaint: {appt[3].lower()}."),
        )
        enc_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
        con.execute(
            "INSERT INTO diagnosis (encounter_id, icd_code, description, is_primary) VALUES (?, 'B50.9', ?, 1)",
            (enc_id, "Plasmodium falciparum malaria, unspecified"),
        )

    # Reorder levels are set from the balance that remains after dispensing,
    # so a few fast-moving items fall below the line and the rest do not.
    balances = con.execute("SELECT medication_id, stock_qty FROM medication ORDER BY medication_id").fetchall()
    for med_id, qty in balances:
        reorder = qty + 12 if med_id in (1, 3, 9) else max(5, qty // 5)
        con.execute("UPDATE medication SET reorder_level = ? WHERE medication_id = ?", (reorder, med_id))

    con.commit()


def main() -> None:
    con = connect(DB)
    try:
        seed(con)
        counts = {
            table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "department",
                "staff",
                "patient",
                "appointment",
                "encounter",
                "diagnosis",
                "medication",
                "prescription",
                "prescription_item",
                "lab_order",
                "invoice",
                "payment",
                "stock_movement",
            )
        }
    finally:
        con.close()
    print(f"Database written to {DB}")
    for table, count in counts.items():
        print(f"  {table:20} {count}")


if __name__ == "__main__":
    main()
