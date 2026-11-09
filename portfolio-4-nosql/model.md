# NoSQL and advanced data models

**Student:** Asiya Ya'u (2026/A/MIT/0763)  
**Evidence:** `evidence/nosql-results.txt` and `evidence/encounter_notes.json`  
**Script:** `encounter_notes.py`  
**MongoDB form of the same queries:** `mongodb_examples.js`

The relational schema in Portfolio 1 is the system of record for identity, bookings, stock, and money. Clinical notes do not fit that discipline. A general visit stores temperature, pulse, and blood pressure. An antenatal visit stores gestation and whether the fetal heart was heard. A paediatric visit stores weight. Forcing those into one `encounter` row would mean a wide table of nulls, and every new service would be another `ALTER TABLE`.

## Document model

`encounter_notes.py` reads 24 real encounters from the SQLite database and writes one JSON document per visit. The document always has the patient folder number, the author, the department, and the assessment. It then carries one of `vitals`, `antenatal`, or `growth`, depending on the department. Three of the 24 notes (encounters 8, 11, and 22) contain an `antenatal` object. The others do not have the field at all.

A document query for `vitals.temperature_c >= 38.0` returns four notes: encounters 5, 10, 15, and 20, each at 38.1 C, for folders ACC-0003, ACC-0004, ACC-0006, and ACC-0009. Notes that have no `vitals` object are simply skipped. That is the practical difference from a nullable SQL column: the field is absent, not stored as null, and the query expresses that directly.

The same queries are written in `mongodb_examples.js` for a collection named `encounter_notes`, including an index on `patient.hospital_no` and `recorded_at`. They were not executed on a MongoDB server. The executed evidence is the Python document store, which applies the same model to the clinic's own encounters. The two stay aligned by `encounter_id` and `hospital_no`, so a note can be opened from the relational visit.

## Key-value

The amount a patient still owes is a join of open invoices and their lines. Reception looks that figure up many times and does not need the line detail. The script builds a map from folder number to kobo outstanding. The sample holds 47 keys. `ACC-0009` maps to NGN 3,605.00. This is a cache. The invoice tables remain the source of the figure, and the cache is something to rebuild, not a second ledger.

## Column family

Laboratory results are sparse. One visit may have a malaria test, another a pregnancy test, and most visits have no test. The script lays the first results out as a row key (the encounter id) and a column per test code. Encounter 4 has `WIDAL`, encounter 5 has `MRDT`, and encounter 6 has `PT`. Empty tests are not stored. That is the column-family shape: the row key is stable and the columns present on a row are allowed to differ.

## Graph

A referral is a relationship, not an attribute of the patient. The script treats a later visit outside General Outpatient, after a general visit, as a `REFERRED` edge from one doctor to another. Eight such edges are in the evidence. One of them is Ahmad Haruna (ACC-0011), seen by Dr Hauwa Bello on 3 September 2026 and later by Dr Yusuf Garba in Paediatrics on 25 September 2026. A graph store would query "who was this patient sent to?" by walking edges. The relational tables can answer it with a self-join, which is what the script does, but the result is naturally a graph.

## Why the clinic should not move everything

Patients, stock, and payments stay relational because they need unique folder numbers, a non-negative balance, and a transaction around money. Notes, the balance cache, the sparse laboratory sheet, and referrals are the parts whose shape or access path is different. Using four models for their fit, on one case study, is the point of this portfolio activity.
