
## MMLU-Pro split and duplicate-query follow-up — 2026-10-16

### Verified findings
- `test_1000`: 36 metadata entries, 36 distinct model names, 1,001 records per inspected file.
- All 36 `test_1000` model files have identical ordered prompt sequences; no read errors were detected.
- `test_3000`: the inspected representative file contains 3,000 records.
- The 998 distinct normalized `origin_query` strings in the inspected `test_1000` file all occur in the inspected `test_3000` file.
- The smaller split has three duplicate-query groups:
  - indices 16 and 338: "Who said that Jurisprudence is the eye of law"
  - indices 368 and 775: "Another name for the fallacy of accident is"
  - indices 835 and 982: a legal scenario involving a lease, a deceased landowner, and a bequest to the Girl Scouts of America
- Only 337 records match across the two inspected files by both index and normalized query. Indices are therefore not interchangeable between these split files.
- The two inspected files have different data fingerprints.

### Interpretation and limitations
- Within-split prompt alignment for `test_1000` passes.
- The 1,001-record count and three repeated query groups are documented anomalies; their origin is not established.
- Prompt-set containment is based on normalized `origin_query` strings from one representative file per split, not a full provenance audit.
- `test_1000` and `test_3000` overlap substantially and must not be treated as independent benchmarks.
- Preserve original records. Do not silently remove duplicate queries.
- If this dataset is used in evaluation, consider reporting record-weighted and deduplicated-query sensitivity results.
- These checks do not establish score equivalence, leakage-free generalization, statistical significance, or research novelty.

### Status
Targeted MMLU-Pro prompt-integrity follow-up complete. Further work should focus on benchmark selection, evaluation design, and a defensible held-out-benchmark experiment rather than repeating these checks.
