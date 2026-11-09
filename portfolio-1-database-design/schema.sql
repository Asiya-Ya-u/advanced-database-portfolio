-- MIT 8103 Advanced Database Systems
-- Student: Asiya Ya'u    Registration number: 2026/A/MIT/0763
-- Case study: Amana Community Clinic (simulated primary-care clinic, Kano)
-- Portfolio 1: logical schema in Third Normal Form
--
-- Money is stored in kobo (1 naira = 100 kobo) so totals do not use floating-point values.
-- Dates and times are ISO-8601 text, which SQLite compares correctly in lexical order.

PRAGMA foreign_keys = ON;

CREATE TABLE department (
    department_id   INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL UNIQUE,
    location        TEXT    NOT NULL
);

CREATE TABLE staff (
    staff_id        INTEGER PRIMARY KEY,
    department_id   INTEGER NOT NULL REFERENCES department (department_id),
    full_name       TEXT    NOT NULL,
    role            TEXT    NOT NULL CHECK (role IN (
                        'doctor', 'nurse', 'pharmacist', 'lab_scientist', 'receptionist'
                    )),
    licence_no      TEXT    UNIQUE,
    phone           TEXT    NOT NULL
);

CREATE TABLE patient (
    patient_id      INTEGER PRIMARY KEY,
    hospital_no     TEXT    NOT NULL UNIQUE,
    full_name       TEXT    NOT NULL,
    sex             TEXT    NOT NULL CHECK (sex IN ('F', 'M')),
    date_of_birth   TEXT    NOT NULL,
    phone           TEXT    NOT NULL,
    address         TEXT    NOT NULL,
    registered_on   TEXT    NOT NULL
);

-- One doctor cannot have two appointments in the same minute.
CREATE TABLE appointment (
    appointment_id  INTEGER PRIMARY KEY,
    patient_id      INTEGER NOT NULL REFERENCES patient (patient_id),
    doctor_id       INTEGER NOT NULL REFERENCES staff (staff_id),
    department_id   INTEGER NOT NULL REFERENCES department (department_id),
    scheduled_at    TEXT    NOT NULL,
    status          TEXT    NOT NULL CHECK (status IN (
                        'booked', 'checked_in', 'completed', 'cancelled', 'no_show'
                    )),
    reason          TEXT    NOT NULL,
    UNIQUE (doctor_id, scheduled_at)
);

-- A completed or checked-in visit has exactly one clinical encounter.
CREATE TABLE encounter (
    encounter_id    INTEGER PRIMARY KEY,
    appointment_id  INTEGER NOT NULL UNIQUE REFERENCES appointment (appointment_id),
    patient_id      INTEGER NOT NULL REFERENCES patient (patient_id),
    doctor_id       INTEGER NOT NULL REFERENCES staff (staff_id),
    started_at      TEXT    NOT NULL,
    notes_summary   TEXT    NOT NULL
);

CREATE TABLE diagnosis (
    diagnosis_id    INTEGER PRIMARY KEY,
    encounter_id    INTEGER NOT NULL REFERENCES encounter (encounter_id),
    icd_code        TEXT    NOT NULL,
    description     TEXT    NOT NULL,
    is_primary      INTEGER NOT NULL CHECK (is_primary IN (0, 1))
);

CREATE TABLE medication (
    medication_id   INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL UNIQUE,
    form            TEXT    NOT NULL,
    unit_price_kobo INTEGER NOT NULL CHECK (unit_price_kobo >= 0),
    stock_qty       INTEGER NOT NULL CHECK (stock_qty >= 0),
    reorder_level   INTEGER NOT NULL CHECK (reorder_level >= 0)
);

-- Opening quantity plus later receipts and issues. stock_qty on medication is the balance.
CREATE TABLE stock_movement (
    movement_id     INTEGER PRIMARY KEY,
    medication_id   INTEGER NOT NULL REFERENCES medication (medication_id),
    quantity_change INTEGER NOT NULL,
    reason          TEXT    NOT NULL CHECK (reason IN ('opening', 'receipt', 'dispense', 'adjustment')),
    occurred_at     TEXT    NOT NULL,
    prescription_id INTEGER REFERENCES prescription (prescription_id)
);

CREATE TABLE prescription (
    prescription_id INTEGER PRIMARY KEY,
    encounter_id    INTEGER NOT NULL REFERENCES encounter (encounter_id),
    prescribed_at   TEXT    NOT NULL,
    status          TEXT    NOT NULL CHECK (status IN ('pending', 'dispensed', 'cancelled'))
);

CREATE TABLE prescription_item (
    prescription_item_id INTEGER PRIMARY KEY,
    prescription_id      INTEGER NOT NULL REFERENCES prescription (prescription_id),
    medication_id        INTEGER NOT NULL REFERENCES medication (medication_id),
    dose                 TEXT    NOT NULL,
    quantity             INTEGER NOT NULL CHECK (quantity > 0),
    UNIQUE (prescription_id, medication_id)
);

CREATE TABLE lab_test (
    lab_test_id     INTEGER PRIMARY KEY,
    code            TEXT    NOT NULL UNIQUE,
    name            TEXT    NOT NULL,
    price_kobo      INTEGER NOT NULL CHECK (price_kobo >= 0)
);

CREATE TABLE lab_order (
    lab_order_id    INTEGER PRIMARY KEY,
    encounter_id    INTEGER NOT NULL REFERENCES encounter (encounter_id),
    lab_test_id     INTEGER NOT NULL REFERENCES lab_test (lab_test_id),
    ordered_at      TEXT    NOT NULL,
    status          TEXT    NOT NULL CHECK (status IN (
                        'ordered', 'sample_taken', 'resulted', 'cancelled'
                    )),
    result_value    TEXT,
    resulted_at     TEXT
);

CREATE TABLE invoice (
    invoice_id      INTEGER PRIMARY KEY,
    patient_id      INTEGER NOT NULL REFERENCES patient (patient_id),
    encounter_id    INTEGER REFERENCES encounter (encounter_id),
    issued_at       TEXT    NOT NULL,
    status          TEXT    NOT NULL CHECK (status IN ('open', 'paid', 'void'))
);

CREATE TABLE invoice_line (
    invoice_line_id INTEGER PRIMARY KEY,
    invoice_id      INTEGER NOT NULL REFERENCES invoice (invoice_id),
    description     TEXT    NOT NULL,
    amount_kobo     INTEGER NOT NULL CHECK (amount_kobo >= 0)
);

CREATE TABLE payment (
    payment_id      INTEGER PRIMARY KEY,
    invoice_id      INTEGER NOT NULL REFERENCES invoice (invoice_id),
    amount_kobo     INTEGER NOT NULL CHECK (amount_kobo > 0),
    method          TEXT    NOT NULL CHECK (method IN ('cash', 'transfer', 'card')),
    paid_at         TEXT    NOT NULL,
    reference_no    TEXT    NOT NULL UNIQUE
);
