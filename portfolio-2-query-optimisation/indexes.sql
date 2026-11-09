-- Indexes added after the baseline plans were captured.
-- Primary keys and UNIQUE constraints already have indexes; these cover filters and joins
-- that the clinic actually runs.

-- doctor_id + scheduled_at is already indexed by UNIQUE (doctor_id, scheduled_at).
-- A second index on the same columns would slow every booking down and is not created.

CREATE INDEX idx_appointment_patient
    ON appointment (patient_id);

CREATE INDEX idx_appointment_status
    ON appointment (status);

CREATE INDEX idx_encounter_patient
    ON encounter (patient_id);

CREATE INDEX idx_encounter_doctor
    ON encounter (doctor_id);

CREATE INDEX idx_diagnosis_code
    ON diagnosis (icd_code);

CREATE INDEX idx_diagnosis_encounter
    ON diagnosis (encounter_id, is_primary, icd_code, description);

CREATE INDEX idx_invoice_patient_status
    ON invoice (patient_id, status);

CREATE INDEX idx_invoice_status
    ON invoice (status);

CREATE INDEX idx_invoice_line_invoice
    ON invoice_line (invoice_id);

CREATE INDEX idx_payment_paid_at
    ON payment (paid_at);

CREATE INDEX idx_lab_order_status_time
    ON lab_order (status, ordered_at);

CREATE INDEX idx_patient_name
    ON patient (full_name);

CREATE INDEX idx_medication_stock
    ON medication (stock_qty);
