# Distributed and cloud database

**Student:** Asiya Ya'u (2026/A/MIT/0763)  
**Executed evidence:** `evidence/cluster-log.txt`, produced by `simulate_cluster.py`  
**Node files:** `evidence/nodes/`

## How the clinic data would be split

Almost every operational question is about one patient: the folder, the visits, the unpaid bill, the drugs just dispensed. The shard key is therefore `patient_id`. Shard 0 takes even ids and shard 1 takes odd ids. A payment is written to the shard that already holds that patient, so taking money does not need a two-phase commit across shards.

Sharding by department was rejected. One patient's antenatal visit and her later general visit would land on different nodes, and the history screen would always be a scatter-gather. Sharding by month was rejected for the same reason: a patient's history grows across months.

The simulation loads the 120 registered patients. ACC-0001 goes to shard-1, ACC-0002 to shard-0, and so on. Each shard ends with 60 patients. Receipts follow the patient: shard-0 holds NGN 289,430.00 and shard-1 holds NGN 365,355.00.

A clinic-wide count cannot be answered by one node. The script asks both shards and adds the answers, 60 plus 60, to reach 120. That is the cost of the shard key. It is acceptable because the count is a report, not the screen a nurse opens while the patient is standing at the desk.

## Replication and consistency

Each shard has a primary and a replica. Writes go to the primary and are listed as pending. Until `catch_up` runs, the replica does not have them.

The log shows this directly. After the initial load, a demonstration patient ACC-5001 is inserted on the shard-0 primary. The primary count becomes 61 and the replica count stays 60. After the one pending write is applied, both counts are 61. A report that reads the replica during that gap is stale. The script therefore does not take payments from the replica.

This is a deliberate consistency choice, not an accident of the prototype:

- Stock and payments are strongly consistent. They run on the primary, inside the local transaction from Portfolio 3. Losing an update or reading an uncommitted balance is worse than making the pharmacist wait.
- Clinical notes, from Portfolio 4, can be eventually consistent. A note that appears on the replica a second later does not mis-charge the patient.
- If the two conflict, the payment wins. The note is not part of the payment transaction.

In CAP terms the payment path chooses consistency over availability for that shard. The enquiry path can keep answering from a replica and accepts being briefly behind.

## What an outage does

The script then marks the shard-1 primary unavailable. A read or a registration on shard-1 fails with `shard-1 primary is unavailable`. Shard-0 still answers, with 61 rows on its primary because it still holds the demonstration patient. Patients whose id falls on shard-0 can still be registered and can still pay. Patients on shard-1 cannot pay until that primary returns. The shard-1 replica can still be read for enquiry and reports 60 patients, with the warning that the read may be stale and must not be used to take a payment.

The failure is partial. That is the availability gain of the shard. It is also the reason the shard key has to be something the application knows before it opens a connection. The folder number decides the node. There is no safe way to "try the other shard" for a payment.

## Cloud deployment this design maps to

The local files are the executed evidence. A production deployment of the same design would be:

| Workload | Service | Layout |
| --- | --- | --- |
| Patients, bookings, stock, invoices, payments | Managed PostgreSQL | One primary and one synchronous replica in a second availability zone. This is the system of record. |
| Clinical notes | MongoDB replica set, or a managed document service | Three members so a note write survives the loss of one node. Reads of a note may use a secondary. |
| Balance cache | Key-value store with a short time-to-live | Rebuilt from the open-invoice query. Not a ledger. |
| Shard growth | Range or hash partition on `patient_id` | Only when one primary can no longer hold the working set. The clinic sample does not need this yet. |

The application, not the user, chooses the shard from `patient_id`. Backups of the PostgreSQL primary are the recovery point for money. A replica is for availability and for heavy read reports, not a substitute for that backup. No cloud account was created for this portfolio; the placement, the lag, the scatter-gather count, and the partial outage were all run locally and written to `cluster-log.txt`.
