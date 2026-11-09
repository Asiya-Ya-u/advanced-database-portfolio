-- MIT 8103 Portfolio 2
-- Student: Asiya Ya'u (2026/A/MIT/0763)
-- Queries against Amana Community Clinic. Literals match the seeded database.

-- QUERY: patient_by_name
-- A name lookup used at the reception desk. No index exists on full_name until Portfolio 2.
SELECT patient_id, hospital_no, full_name, phone
FROM patient
WHERE full_name = 'Amina Musa';

-- QUERY: doctor_day_list
-- The list a doctor opens at the start of a clinic session.
SELECT a.scheduled_at, a.status, p.hospital_no, p.full_name, a.reason
FROM appointment AS a
JOIN patient AS p ON p.patient_id = a.patient_id
WHERE a.doctor_id = 1
  AND a.scheduled_at >= '2026-10-06'
  AND a.scheduled_at < '2026-10-08'
ORDER BY a.scheduled_at;

-- QUERY: open_invoices
-- Accounts: who still owes the clinic, and how much.
SELECT p.hospital_no,
       p.full_name,
       i.invoice_id,
       i.issued_at,
       printf('NGN %.2f', SUM(l.amount_kobo) / 100.0) AS amount_due
FROM invoice AS i
JOIN patient AS p ON p.patient_id = i.patient_id
JOIN invoice_line AS l ON l.invoice_id = i.invoice_id
WHERE i.status = 'open'
GROUP BY i.invoice_id
ORDER BY i.issued_at;

-- QUERY: low_stock
-- Pharmacy reorder list.
SELECT name, form, stock_qty, reorder_level, (reorder_level - stock_qty) AS shortfall
FROM medication
WHERE stock_qty <= reorder_level
ORDER BY shortfall DESC;

-- QUERY: diagnosis_frequency
-- Which conditions the clinic is actually treating.
SELECT d.icd_code, d.description, COUNT(*) AS cases
FROM diagnosis AS d
WHERE d.is_primary = 1
GROUP BY d.icd_code, d.description
ORDER BY cases DESC;

-- QUERY: patient_history
-- Full clinical history for one folder number.
SELECT e.started_at,
       s.full_name AS doctor,
       d.icd_code,
       d.description,
       e.notes_summary
FROM encounter AS e
JOIN staff AS s ON s.staff_id = e.doctor_id
LEFT JOIN diagnosis AS d ON d.encounter_id = e.encounter_id AND d.is_primary = 1
WHERE e.patient_id = 10
ORDER BY e.started_at;

-- QUERY: monthly_revenue
-- Cash actually received, not invoices raised.
SELECT substr(paid_at, 1, 7) AS month,
       printf('NGN %.2f', SUM(amount_kobo) / 100.0) AS received
FROM payment
GROUP BY substr(paid_at, 1, 7)
ORDER BY month;

-- QUERY: lab_backlog
-- Tests ordered before 1 October 2026 that still have no result.
SELECT lo.lab_order_id, p.hospital_no, p.full_name, t.name AS test, lo.ordered_at, lo.status
FROM lab_order AS lo
JOIN lab_test AS t ON t.lab_test_id = lo.lab_test_id
JOIN encounter AS e ON e.encounter_id = lo.encounter_id
JOIN patient AS p ON p.patient_id = e.patient_id
WHERE lo.status IN ('ordered', 'sample_taken')
  AND lo.ordered_at < '2026-10-01'
ORDER BY lo.ordered_at;

-- QUERY: doctor_workload
-- Completed visits per doctor, for rota planning.
SELECT s.full_name, dep.name AS department, COUNT(e.encounter_id) AS encounters
FROM staff AS s
JOIN department AS dep ON dep.department_id = s.department_id
LEFT JOIN encounter AS e ON e.doctor_id = s.staff_id
WHERE s.role = 'doctor'
GROUP BY s.staff_id
ORDER BY encounters DESC;

-- QUERY: repeat_attenders
-- Patients with three or more completed or checked-in visits.
SELECT p.hospital_no, p.full_name, COUNT(e.encounter_id) AS visits
FROM patient AS p
JOIN encounter AS e ON e.patient_id = p.patient_id
GROUP BY p.patient_id
HAVING COUNT(e.encounter_id) >= 3
ORDER BY visits DESC, p.hospital_no;
