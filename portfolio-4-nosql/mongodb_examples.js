// Equivalent MongoDB commands for the clinical-note collection.
// The portfolio runs the same queries in encounter_notes.py, because a local
// MongoDB server is not required to mark the evidence. These commands are the
// production form of that model.

// db.encounter_notes.insertMany([ ... documents from evidence/encounter_notes.json ... ])

// Notes for one folder number
db.encounter_notes.find({ "patient.hospital_no": "ACC-0010" })

// Febrile patients. The field exists only on general-clinic notes.
db.encounter_notes.find({ "vitals.temperature_c": { $gte: 38.0 } })

// Antenatal notes. Documents without this object are simply not returned.
db.encounter_notes.find({ antenatal: { $exists: true } })

// Suggested index once the collection is large
db.encounter_notes.createIndex({ "patient.hospital_no": 1, recorded_at: -1 })
