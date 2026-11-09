# Case study: Amana Community Clinic

**Student:** Asiya Ya'u  
**Registration number:** 2026/A/MIT/0763  
**Course:** MIT 8103 Advanced Database Systems  
**Session:** 2026/2027, First Semester

## Organisation

Amana Community Clinic is a simulated primary-care clinic in Kano. It is not a real hospital and the records in this portfolio are generated. The clinic is small enough to design completely, and busy enough to need appointments, drug stock, laboratory orders, and payments.

The clinic has five units: General Outpatient, Maternal Health, Paediatrics, Laboratory, and Pharmacy. A patient is registered once and keeps a folder number such as `ACC-0010`. Reception books the patient to one doctor at one time. The doctor records the visit, a primary diagnosis, and, when needed, a prescription or a laboratory test. Pharmacy issues the drugs only when the packs are on the shelf. Accounts raises one invoice for the visit and records a payment when the patient pays.

## Users

| User | What they do with the database |
| --- | --- |
| Receptionist | Register a patient and book or cancel an appointment |
| Doctor | Open the day's list, record the encounter and diagnosis |
| Pharmacist | Dispense a prescription and keep the stock balance correct |
| Laboratory scientist | Accept a sample and store the result |
| Accounts officer | Raise an invoice and record cash, transfer, or card |

## Data the database must keep

Patients, staff and their departments, appointments, encounters, diagnoses, medicines and stock movements, prescriptions, laboratory tests and orders, invoices, invoice lines, and payments.

## Operations the design has to support

- Register a patient and find that patient again by name or folder number.
- Book a doctor without giving the same doctor two patients in the same minute.
- Record a visit, one primary diagnosis, and the drugs or tests ordered from that visit.
- Dispense drugs as one transaction: the stock movement, the new balance, and the invoice either all stand or all fail.
- Show unpaid invoices, medicines that have fallen to the reorder level, and the laboratory work that is still waiting.
- Keep a clinical note whose shape changes by service. Antenatal visits carry gestation; paediatric visits carry weight; general visits carry vital signs. That part is handled in Portfolio 4, on the same patients.

The sample loaded by `seed.py` contains 120 patients, 428 appointments, 284 encounters, 252 invoices, and 194 payments, spread over weekdays from 1 September 2026 to 20 November 2026. Running `python run_all.py` from the portfolio root rebuilds that sample and every evidence file.
