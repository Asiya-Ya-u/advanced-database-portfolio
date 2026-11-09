# MIT 8103 Advanced Database Systems

**Student:** Asiya Ya'u  
**Registration number:** 2026/A/MIT/0763  
**Programme:** Master of Information Technology  
**Session:** 2026/2027, First Semester  
**Assessment:** Individual Practical Database Portfolio (40 marks)

The case study used in every activity is **Amana Community Clinic**, a simulated primary-care clinic in Kano. Patients, staff, and visits are generated. They are not records of a real clinic.

## How to rebuild the evidence

Python 3.10 or newer is enough. No extra packages are required.

```text
python run_all.py
```

That command rebuilds `data/amana_clinic.sqlite` and rewrites the evidence files under each portfolio folder.

## Layout

| Path | Portfolio activity | Marks in the brief |
| --- | --- | --- |
| `portfolio-1-database-design/` | Case study, ER diagram, relational schema, keys, constraints, normalisation | 7 |
| `portfolio-2-query-optimisation/` | Ten SQL queries, results, plans before and after indexes, written analysis | 7 |
| `portfolio-3-transactions-concurrency/` | Commit, rollback, lost update, and a write lock between two connections | 7 |
| `portfolio-4-nosql/` | Document notes, plus key-value, column, and graph examples on the same patients | 7 |
| `portfolio-5-distributed-cloud/` | Two shards, each with a primary and a replica; outage and consistency choices | 6 |
| `documentation/lms-summary.pdf` | Two-to-three page summary, reflection, references, and the AI-use declaration | 6 |

The course brief is in `documentation/MIT8103-CA-brief.pdf`.

## What a marker can open first

1. `documentation/lms-summary.pdf` for the short account of all five activities.
2. `portfolio-1-database-design/schema.sql` and `er-diagram.svg` for the design.
3. `portfolio-2-query-optimisation/evidence/` for the plans and the result tables.
4. `portfolio-3-transactions-concurrency/evidence/transaction-log.txt` for commit, rollback, and the lock.
5. `portfolio-4-nosql/evidence/nosql-results.txt` for the document, key-value, column, and graph output.
6. `portfolio-5-distributed-cloud/evidence/cluster-log.txt` for placement, replica lag, and the shard outage.

## AI-use declaration

An AI assistant in Cursor (Grok) was used to draft the schema, the seed and test scripts, the diagrams, and the written explanations. The scripts were then run on this machine. The files in each `evidence` folder are the output of those runs, not text composed by hand. The design choices recorded in the analysis files, including indexes that the planner did not use, follow those outputs. Asiya Ya'u remains responsible for reading the schema, the queries, and the explanations, and for being able to walk through them if the work is selected for verification.

## References

Elmasri, R. and Navathe, S. B. *Fundamentals of Database Systems*. Pearson.

Silberschatz, A., Korth, H. F. and Sudarshan, S. *Database System Concepts*. McGraw-Hill.

SQLite documentation: query planning with `EXPLAIN QUERY PLAN`, and transactions and the reserved lock. https://www.sqlite.org/docs.html

MongoDB documentation: data modelling for document collections. https://www.mongodb.com/docs/manual/data-modeling/

Brewer, E. "CAP twelve years later: how the rules have changed." *Computer*, 2012.

Miva Open University. MIT 8103 Advanced Database Systems, First Semester Continuous Assessment, 2026/2027. The brief distributed to the September cohort.
