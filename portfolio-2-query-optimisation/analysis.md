# Query processing and optimisation

**Student:** Asiya Ya'u (2026/A/MIT/0763)  
**Engine:** SQLite, plans captured with `EXPLAIN QUERY PLAN`  
**Evidence:** `evidence/plans-before-indexes.txt`, `evidence/plans-after-indexes.txt`, `evidence/query-results.txt`

The ten queries are the ones reception, the doctors, pharmacy, the laboratory, and accounts actually run. Each plan was captured on the seeded database of 428 appointments and 284 encounters, then the indexes in `indexes.sql` were created and the plans were captured again.

## Where an index changed the plan

| Query | Before | After | What changed for the clinic |
| --- | --- | --- | --- |
| Patient lookup by full name | `SCAN patient` | `SEARCH patient USING INDEX idx_patient_name` | Reception finds Amina Musa, ACC-0010, without reading every folder |
| Open invoices | Scan of every invoice line, then a lookup of the invoice | `SEARCH invoice USING INDEX idx_invoice_status`, then `SEARCH invoice_line USING INDEX idx_invoice_line_invoice` | Accounts reads the open bills first. The sample has 58 open invoices |
| One patient's history | `SCAN encounter` | `SEARCH encounter USING INDEX idx_encounter_patient`, and a covering lookup of the diagnosis | ACC-0010's three visits are fetched by patient id |
| Laboratory backlog | `SCAN lab_order` | `SEARCH lab_order USING INDEX idx_lab_order_status_time (status, ordered_at)` | Eight tests ordered before 1 October 2026 are still waiting |
| Repeat attenders | Scan encounters, then look up the patient | Scan the smaller patient table and probe `idx_encounter_patient` | 52 patients have three or more recorded visits |
| Doctor workload | An automatic index built for that one query | `SEARCH encounter USING COVERING INDEX idx_encounter_doctor` | The permanent index replaces the temporary one. Dr Hauwa Bello has 101 encounters and Dr Musa Danladi has 98 |

## Where an index was already present, or was not worth adding

The doctor day-list was already a search, before any index in `indexes.sql`. `UNIQUE (doctor_id, scheduled_at)` creates `sqlite_autoindex_appointment_1`, and the plan uses it for `doctor_id` plus the time range. Dr Hauwa Bello's list for 6 and 7 October 2026 returns 7 appointments. A second index on the same two columns would make every new booking maintain two trees, so it was not created.

`idx_medication_stock` does not appear in the low-stock plan. The predicate is `stock_qty <= reorder_level`, which compares two columns of the same row. An index on `stock_qty` alone cannot satisfy that. The medication table has 12 rows, so a scan is the right plan. Paracetamol, artemether-lumefantrine, and salbutamol are the three items currently below their reorder level. This is kept in the evidence on purpose: an index that the planner ignores is not an optimisation.

Monthly revenue still scans `payment`. The report has to add every receipt and group it by month. An index does not reduce that to a few rows. The result is NGN 237,025.00 in September, NGN 232,410.00 in October, and NGN 185,350.00 in November. The index on `paid_at` would matter for a query that asked for one day, not for a total of the whole table.

Diagnosis frequency also reads every primary diagnosis. The plan becomes an index scan of `idx_diagnosis_code` rather than a table scan, which is a smaller structure, but it is still a full pass. Pregnancy supervision is the most common primary code in the sample (68), then gastroenteritis (43) and upper respiratory infection (42). A scan is acceptable for a report that must count every code.

## What this means in practice

Indexes were added for the predicates the screens use: a patient's name, a patient's encounters, a doctor's encounters, an invoice status, the lines of one invoice, and laboratory orders by status and date. Indexes were refused where a constraint already provided the access path, where the predicate could not use the index, or where the query must read the whole table anyway. The plans, not the number of `CREATE INDEX` statements, are the evidence.
