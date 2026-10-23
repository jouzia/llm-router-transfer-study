# Day 3 — Held-Out Benchmark Integrity Audit

## Objective

Assess whether GPQA and LiveCodeBench are structurally suitable
candidates for evaluating transfer of a prompt-feature-based model
router trained on ArenaHard-related source tasks.

This is a structural audit, not evidence of routing effectiveness,
benchmark validity, or generalization.

## 1. GPQA

- Metadata rows / model files inspected: 38
- Distinct JSON model names: 38
- Records per model: 198
- Total records: 7,524
- Distinct prompt-sequence signatures: 1
- Models matching the majority prompt sequence: 38/38
- Actual record-count mismatches: 0
- Missing CSV fingerprints: 0
- Missing JSON fingerprints: 0
- Nonempty CSV/JSON fingerprint mismatches: 0
- Records with missing prompt text: 0
- Records with missing or null scores: 0
- Records with null ground truth: 0
- Read errors: 0
- Score counts: 3,956 records scored 1.0; 3,568 scored 0.0

### Assessment

GPQA passes the inspected structural checks. All 38 model files
share the same ordered prompt sequence and have matching nonempty
CSV/JSON fingerprints. Every inspected record has prompt text,
a non-null score, and a non-null ground-truth value.

This supports selecting GPQA as the first held-out transfer
candidate. It does not independently validate the source benchmark,
scoring implementation, licensing, or scientific generalization.

## 2. LiveCodeBench

- Metadata rows / model files inspected: 38
- Distinct JSON model names: 38
- Records per model: 1,055
- Total records: 40,090
- Distinct prompt-sequence signatures: 1
- Models matching the majority prompt sequence: 38/38
- Actual record-count mismatches: 0
- Missing CSV fingerprints: 20
- Missing JSON fingerprints: 20
- Nonempty CSV/JSON fingerprint mismatches: 0
- Records with missing prompt text: 0
- Records with missing or null scores: 0
- Records with null ground truth: 40,090
- Read errors: 0
- Score counts: 20,533 records scored 0.0; 19,557 scored 1.0

### Assessment

LiveCodeBench passes the prompt-sequence, record-count, prompt-text,
and score-presence checks. However, 20 files have no fingerprint
in either the metadata CSV or the JSON result. This is missing
verification information, not a demonstrated fingerprint mismatch.

All records have null ground-truth values. Consequently, this field
cannot be used to independently validate reference answers. The
recorded scores may still be usable, but their scoring semantics
and provenance must be checked before interpreting them as verified
coding correctness.

LiveCodeBench remains a candidate pending these additional checks.

## 3. Interpretation and limitations

1. Matching prompt sequences establish structural alignment, not
   independent benchmark samples or independent model errors.
2. Non-null binary scores do not independently establish that the
   scoring code or benchmark answers are correct.
3. Missing fingerprints are not equivalent to conflicting
   fingerprints, but they reduce the available integrity evidence.
4. No held-out benchmark scores have been used here to select,
   tune, or validate the router.
5. Benchmark licenses, data provenance, and redistribution
   permissions remain separate unresolved questions.
6. No claim of statistically reliable improvement, unseen-domain
   generalization, or novel methodological contribution is made.

## 4. Recommended next experiment

Freeze the routing method and evaluation protocol before examining
GPQA target performance.

- Train the feature-based router using source benchmark data only.
- Restrict evaluation to model identities available in both source
  and target datasets, after verifying exact model-name mappings.
- Use only features computable from a target prompt at inference time.
- Never use a target prompt's score or ground truth to select its model.
- Compare the selected model's observed GPQA score with a global
  baseline chosen using source data only.
- Treat any target-informed best-model result as an oracle upper
  bound, not a deployable baseline.
- Report paired prompt-level differences, uncertainty intervals,
  and per-seed results; do not treat repeated seeds on the same
  target prompts as independent test samples.
- Keep GPQA untouched for feature, hyperparameter, and threshold
  selection.
- Resolve benchmark provenance and licensing before redistribution.

## Status

Structural audit: complete for the 76 inspected GPQA and
LiveCodeBench model files.

Held-out routing evaluation: not yet performed.

Generalization and novelty: not established.
