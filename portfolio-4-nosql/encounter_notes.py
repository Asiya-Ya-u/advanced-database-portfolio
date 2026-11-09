"""NoSQL models for the same clinic, using the patients already stored in SQLite.

The document collection is the main implementation. Key-value, column, and graph
examples are smaller and use the same case, because a clinic does not keep every
fact in one model.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import DB  # noqa: E402

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"


def build_documents(con: sqlite3.Connection) -> list[dict]:
    rows = con.execute(
        """
        SELECT e.encounter_id, e.started_at, e.notes_summary,
               p.hospital_no, p.full_name, p.sex, p.date_of_birth,
               s.full_name AS doctor, dep.name AS department,
               d.icd_code, d.description
        FROM encounter e
        JOIN patient p ON p.patient_id = e.patient_id
        JOIN staff s ON s.staff_id = e.doctor_id
        JOIN department dep ON dep.department_id = s.department_id
        LEFT JOIN diagnosis d ON d.encounter_id = e.encounter_id AND d.is_primary = 1
        ORDER BY e.encounter_id
        LIMIT 24
        """
    ).fetchall()
    documents = []
    for index, row in enumerate(rows):
        note = {
            "encounter_id": row["encounter_id"],
            "recorded_at": row["started_at"],
            "patient": {
                "hospital_no": row["hospital_no"],
                "full_name": row["full_name"],
                "sex": row["sex"],
            },
            "author": row["doctor"],
            "department": row["department"],
            "presenting_complaint": row["notes_summary"],
            "assessment": [{"icd_code": row["icd_code"], "text": row["description"]}],
        }
        if row["department"] == "Maternal Health":
            note["antenatal"] = {
                "gestation_weeks": 12 + (index % 20),
                "fundal_height_cm": 14 + (index % 16),
                "fetal_heart_heard": True,
            }
        elif row["department"] == "Paediatrics":
            note["growth"] = {"weight_kg": round(8 + (index % 12) * 0.7, 1), "muac_cm": 13}
        else:
            note["vitals"] = {
                "temperature_c": 36.5 + (index % 5) * 0.4,
                "pulse": 72 + index % 20,
                "blood_pressure": "118/76",
            }
        documents.append(note)
    return documents


def key_value_balances(con: sqlite3.Connection) -> dict[str, int]:
    """Reception cache: hospital number -> unpaid kobo. A key-value lookup, not a join."""
    rows = con.execute(
        """
        SELECT p.hospital_no, COALESCE(SUM(l.amount_kobo), 0) AS due
        FROM patient p
        JOIN invoice i ON i.patient_id = p.patient_id AND i.status = 'open'
        JOIN invoice_line l ON l.invoice_id = i.invoice_id
        GROUP BY p.hospital_no
        """
    ).fetchall()
    return {row["hospital_no"]: row["due"] for row in rows}


def column_lab_results(con: sqlite3.Connection) -> dict[str, dict[str, str]]:
    """One row-key (the encounter) and a changing set of test columns."""
    rows = con.execute(
        """
        SELECT lo.encounter_id, t.code, COALESCE(lo.result_value, lo.status) AS cell
        FROM lab_order lo
        JOIN lab_test t ON t.lab_test_id = lo.lab_test_id
        ORDER BY lo.encounter_id
        LIMIT 40
        """
    ).fetchall()
    table: dict[str, dict[str, str]] = {}
    for row in rows:
        table.setdefault(str(row["encounter_id"]), {})[row["code"]] = row["cell"]
    return table


def referral_graph(con: sqlite3.Connection) -> list[dict]:
    """A patient seen in General Outpatient and later in another department is a referral edge."""
    rows = con.execute(
        """
        SELECT p.hospital_no, p.full_name,
               e1.started_at AS from_visit, s1.full_name AS from_doctor,
               e2.started_at AS to_visit, s2.full_name AS to_doctor, d2.name AS to_department
        FROM encounter e1
        JOIN encounter e2 ON e2.patient_id = e1.patient_id AND e2.started_at > e1.started_at
        JOIN patient p ON p.patient_id = e1.patient_id
        JOIN staff s1 ON s1.staff_id = e1.doctor_id
        JOIN staff s2 ON s2.staff_id = e2.doctor_id
        JOIN department d1 ON d1.department_id = s1.department_id
        JOIN department d2 ON d2.department_id = s2.department_id
        WHERE d1.name = 'General Outpatient' AND d2.name <> 'General Outpatient'
        ORDER BY e2.started_at
        LIMIT 8
        """
    ).fetchall()
    return [
        {
            "from": f"{row['from_doctor']} ({row['from_visit']})",
            "edge": "REFERRED",
            "to": f"{row['to_doctor']} / {row['to_department']} ({row['to_visit']})",
            "patient": f"{row['hospital_no']} {row['full_name']}",
        }
        for row in rows
    ]


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    documents = build_documents(con)
    balances = key_value_balances(con)
    columns = column_lab_results(con)
    graph = referral_graph(con)
    con.close()

    (EVIDENCE / "encounter_notes.json").write_text(
        json.dumps(documents, indent=2), encoding="utf-8"
    )

    febrile = [
        {
            "encounter_id": doc["encounter_id"],
            "patient": doc["patient"]["hospital_no"],
            "temperature_c": doc["vitals"]["temperature_c"],
        }
        for doc in documents
        if "vitals" in doc and doc["vitals"]["temperature_c"] >= 38.0
    ]
    antenatal = [doc["encounter_id"] for doc in documents if "antenatal" in doc]
    sample_key = next(iter(balances)) if balances else None

    lines = [
        "NoSQL evidence for Amana Community Clinic",
        "",
        f"Document collection size: {len(documents)}",
        f"Notes that carry an antenatal object: {antenatal}",
        f"Notes with temperature at or above 38.0 C: {febrile}",
        "",
        "The antenatal and paediatric notes do not have the same fields as a general note.",
        "A relational table would have needed nullable columns, or a new table, for each service.",
        "",
        f"Key-value cache holds {len(balances)} open balances.",
    ]
    if sample_key:
        naira = balances[sample_key] / 100
        lines.append(f"Lookup {sample_key} -> NGN {naira:.2f} without joining invoice tables again.")
    lines.append("")
    lines.append(f"Column-family style lab sheet, first three row keys:")
    for key in list(columns)[:3]:
        lines.append(f"  encounter {key}: {columns[key]}")
    lines.append("")
    lines.append(f"Referral graph edges found from the visit sequence: {len(graph)}")
    for edge in graph[:5]:
        lines.append(f"  {edge['patient']}: {edge['from']} -[{edge['edge']}]-> {edge['to']}")
    text = "\n".join(lines) + "\n"
    (EVIDENCE / "nosql-results.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
