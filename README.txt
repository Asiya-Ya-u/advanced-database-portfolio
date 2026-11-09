MIT 8103 Advanced Database Systems
Individual Practical Database Portfolio

Student: Asiya Ya'u
Registration number: 2026/A/MIT/0763
Programme: Master of Information Technology
Session: 2026/2027, First Semester

GitHub profile: https://github.com/Asiya-Ya-u
Repository: https://github.com/Asiya-Ya-u/advanced-database-portfolio
Branch: master

Summary of the work

The case study used in every activity is Amana Community Clinic, a simulated primary-care clinic in Kano. The loaded sample has 120 patients, 428 appointments, 284 encounters, 252 invoices, and 194 payments.

Portfolio 1. Database design. The clinic is modelled in third normal form, with an entity-relationship diagram, keys, and constraints. A doctor cannot be booked twice in the same minute, and stock cannot fall below zero.

Portfolio 2. Query processing. Ten SQL queries were run, and the query plans were saved before and after indexes were added. Indexes were kept where the plan changed, and left out where a scan was already the right plan.

Portfolio 3. Transactions and concurrency. A drug issue was committed, an issue larger than the stock was rolled back, a double booking was rejected, a lost update was shown and then avoided, and a second connection was blocked by the write lock.

Portfolio 4. NoSQL and other models. Clinical notes are stored as documents because antenatal, paediatric, and general visits do not have the same fields. The same patients are also used for a key-value balance cache, a sparse laboratory sheet, and referral links between doctors.

Portfolio 5. Distributed and cloud databases. Patients are split across two shards by patient number. Each shard has a primary and a replica. The log shows replica lag, a count that has to ask both shards, and what still works when one primary is unavailable.

The longer written account, including the reflection, references, and AI-use declaration, is in documentation/lms-summary.pdf. Supporting screenshots of the query results, the plans, the transaction log, the NoSQL output, and the cluster log are in documentation/screenshots. Running "python run_all.py" rebuilds the database and the evidence files.
