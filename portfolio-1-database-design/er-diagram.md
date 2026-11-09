# Entity-relationship diagram

**Student:** Asiya Ya'u (2026/A/MIT/0763)

The drawing is in [er-diagram.svg](er-diagram.svg). The cardinalities are:

```mermaid
erDiagram
    DEPARTMENT ||--o{ STAFF : employs
    DEPARTMENT ||--o{ APPOINTMENT : hosts
    PATIENT ||--o{ APPOINTMENT : books
    STAFF ||--o{ APPOINTMENT : sees
    APPOINTMENT ||--o| ENCOUNTER : produces
    ENCOUNTER ||--o{ DIAGNOSIS : records
    ENCOUNTER ||--o{ PRESCRIPTION : writes
    PRESCRIPTION ||--o{ PRESCRIPTION_ITEM : contains
    MEDICATION ||--o{ PRESCRIPTION_ITEM : dispensed_as
    MEDICATION ||--o{ STOCK_MOVEMENT : tracks
    ENCOUNTER ||--o{ LAB_ORDER : requests
    LAB_TEST ||--o{ LAB_ORDER : defines
    PATIENT ||--o{ INVOICE : billed
    ENCOUNTER ||--o{ INVOICE : charges
    INVOICE ||--o{ INVOICE_LINE : itemises
    INVOICE ||--o{ PAYMENT : settles
```

An appointment may exist with no encounter yet, which is why the encounter side is optional. A prescription item always names one medicine. A payment always belongs to one invoice. Clinical notes that do not have a fixed shape are not forced into this diagram; they are the document collection in Portfolio 4, joined back by `encounter_id` and `hospital_no`.
