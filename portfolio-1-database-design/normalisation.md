# Normalisation

**Student:** Asiya Ya'u (2026/A/MIT/0763)  
**Case study:** Amana Community Clinic

## The repeating visit sheet

A clinic that keeps one spreadsheet row per visit ends up with a table like this:

| scheduled_at | hospital_no | patient_name | patient_phone | doctor_name | department | department_location | drugs | invoice_total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

`drugs` holds several medicines in one cell, for example `Paracetamol x2; ORS x1`. The same patient phone is typed again on every visit. The department's room is stored on every row even though it depends on the department, not on the visit.

## First normal form

A column must hold one value. The drug list is split so that each prescribed medicine is its own row in `prescription_item`, with its own dose and quantity. Diagnosis codes are likewise one row in `diagnosis`, not a comma-separated list. After this step, every column is atomic.

## Second normal form

The visit sheet has no single clean key, but the facts in it are not all about the same thing. The patient's phone and address depend on the patient, not on a particular appointment. They are removed to `patient`. The doctor's name and licence depend on the staff member, not on the appointment, so they live in `staff`. An appointment row keeps only the foreign keys `patient_id` and `doctor_id`, plus the facts that truly belong to that booking: when it is, why the patient came, and whether it was completed.

`prescription_item` has a composite uniqueness rule of `(prescription_id, medication_id)`. Dose and quantity depend on that whole pair. They do not depend on the prescription alone or the medicine alone, so they stay on the item row.

## Third normal form

A non-key column must not depend on another non-key column. On the original sheet, `department_location` depends on `department`, and `department` depends on the doctor. That is a transitive dependency. Location is stored once in `department`. Staff points at `department_id`. Appointment also points at `department_id` because the booking is for a clinic session in that unit, and the department of the session is checked against the doctor's department in the way the seed data is built.

Medicine price does not belong on the prescription line as a copied master-data value that can drift. `medication.unit_price_kobo` is the current price. The invoice line stores the amount actually charged for that visit, because a later price change must not rewrite an old bill. Those are two different facts, so they are two columns.

## Keys and constraints that protect the normal form

- `patient.hospital_no`, `staff.licence_no`, `medication.name`, `lab_test.code`, and `payment.reference_no` are natural unique keys. Surrogate integer keys are used for joins.
- `UNIQUE (doctor_id, scheduled_at)` stops a double booking. Portfolio 3 shows the insert being rolled back.
- `encounter.appointment_id` is unique, so one booking produces at most one encounter.
- `CHECK` constraints keep status values, sex, stock, and money inside the set the clinic actually uses.
- Foreign keys stop an invoice, a diagnosis, or a stock issue from pointing at a patient or a drug that does not exist.
- Stock cannot go below zero. A dispense that would do so changes no row and is rolled back.

## What was deliberately not collapsed further

`invoice_line.description` repeats the medicine name as it was printed on the bill. That copy is the historical text of the invoice. The current name stays in `medication`. Deleting the text from the bill and always joining to the current name would make an old invoice change when a drug is renamed. The copy is there because the bill is a record of what was charged, not because the design failed 3NF.
