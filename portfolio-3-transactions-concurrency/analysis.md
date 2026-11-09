# Transactions and concurrency

**Student:** Asiya Ya'u (2026/A/MIT/0763)  
**Evidence:** `evidence/transaction-log.txt`  
**Script:** `transactions.py`, run against a copy of the clinic database so the seeded figures used in Portfolio 2 stay intact.

The clinic cannot treat stock, bookings, and payments as three independent updates. SQLite is used here in autocommit mode, and every test opens its own `BEGIN IMMEDIATE` so the commit or the rollback is visible in the log.

## Commit

Six packs of paracetamol were dispensed inside one transaction, together with a stock movement. The balance moved from 744 to 738 and the transaction committed. The movement row and the balance were written together.

## Rollback

A second dispense asked for 50 packs more than the 738 on hand. The `UPDATE` is guarded by `stock_qty >= ?`, so it changes no row when the shelf cannot cover the issue. The script treats that as a failure and executes `ROLLBACK`. The balance is still 738. A failed sale does not leave a movement without a matching balance, or a balance without a movement.

The same pattern protects the appointment book. Inserting a second patient for doctor 2 at 2026-09-03 08:00 raises `UNIQUE constraint failed: appointment.doctor_id, appointment.scheduled_at`. The transaction rolls back and the appointment count stays 428.

## Lost update

Two clerks each read an amoxicillin balance of 734. One subtracts 5 in application code and writes 729. The other subtracts 3 from the balance he originally read and writes 731. The first issue has disappeared. The shelf is 5 packs higher than the issues can explain.

Repeating the work as `UPDATE medication SET stock_qty = stock_qty - ?` inside two committed transactions leaves 726, which is 734 minus 5 minus 3. The subtraction is applied to the stored value, not to a copy held by a clerk.

## Two connections and the lock

Connection A starts `BEGIN IMMEDIATE` and updates the artemether balance. Connection B, with a one-second timeout, cannot start its own immediate transaction: SQLite returns `database is locked`. B therefore cannot read A's uncommitted figure and write over it. After A commits, B runs its own issue and commits. The lock is pessimistic and covers the database file. That is stricter than a row lock, and it is stricter than READ UNCOMMITTED. For this clinic the strict behaviour is the right one: a payment and a stock issue are safer if they wait than if they run on a dirty balance.

SQLite will not show a dirty read across these two connections. The log records the lock instead of pretending a dirty value was observed. On a larger engine the same requirement would be expressed as at least READ COMMITTED for stock, and as `SELECT ... FOR UPDATE` or an equivalent atomic decrement so that two dispenses cannot lose an update.

## What the clinic should wrap in one transaction

Booking a visit is one transaction because the unique slot must fail cleanly. Dispensing is one transaction because the movement, the balance, the prescription status, and the charge must agree. Recording a payment and marking the invoice paid is one transaction. Writing a clinical note can sit outside that money transaction: a delay in the note must not roll back a payment the patient has already made. That split is used again in Portfolio 5.
