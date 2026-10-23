# Research 3 — Consolidated Research Assessment

Date: 2026-10-23

## Decision

CONDITIONAL GO for an empirical study of cross-benchmark routing transfer.
NO-GO for claiming a novel routing algorithm or superiority over the strongest
fixed-model baseline on the evidence currently available.

## Research question

How reliably does a lightweight lexical-feature router transfer across
benchmark families, and which error patterns explain its performance gap
relative to the strongest fixed-model baseline?

This question is provisional. Novelty is not established until the closest
prior work and supplementary materials have been reviewed in full.

## Method

- Source data: 750 ArenaHard prompts across coding, creative writing, and math.
- Features: 11 lexical and structural prompt features.
- Router: Ridge regression predicting per-model scores.
- Source tuning: source-domain validation; selected regularization varies
  across repeated validation splits.
- Target evaluations: GPQA and MMLU-Pro test_3000.
- Candidate pool: Day 4 uses 33 models; Days 5–8 use 13.
- Repeated splits: seeds 2026–2035; target prompts are reused across seeds.

## Main results

### MMLU-Pro

- Router accuracy: 83.8667%.
- Gemini 2.5 Pro: 85.6667%.
- Difference: -1.80 percentage points.
- Paired prompt-bootstrap 95% CI: [-2.50, -1.133] percentage points
  in the Day 5 report's rounded values.
- The router trails Gemini across all ten Day 7 source-validation splits.

### GPQA

- Day 4 router: 81.8182%.
- Gemini 2.5 Pro: 84.8485%.
- Day 4 difference: -3.0303 percentage points.
- Day 4 paired prompt-bootstrap 95% CI:
  [-7.0707, +1.0101] percentage points.
- Across Day 8 source-validation splits, the router trails Gemini by
  approximately 2.53–3.03 percentage points.

### Baseline sensitivity

The apparent advantage changes with the source-validation-selected
baseline. The positive Day 6 comparison is against Qwen3 Thinking, not
Gemini 2.5 Pro. It does not establish superiority over the strongest
fixed-model reference.

The repeated seeds share the same target prompts and are not independent
target replications.

## Permitted conclusions

- The evaluated lexical-feature Ridge router underperformed Gemini 2.5 Pro
  on the two held-out benchmarks reported here.
- Apparent gains over a source-validation-selected baseline depend on
  which baseline is selected.
- The current evidence does not establish reliable superiority, broad
  cross-benchmark generalization, or a novel routing contribution.
- The results may motivate a careful empirical study of routing failure
  under benchmark-family shift.

## Limitations and unresolved work

1. Complete direct review of the closest papers and supplementary materials.
2. Resolve archive provenance, dataset terms, licenses, and redistribution rights.
3. Verify the semantics of archived scores and keep cost/latency claims excluded
   until aggregation and units are validated.
4. Audit source selection, feature construction, prompt alignment, and target
   evaluation paths across all scripts.
5. Recompute paired results from the aligned per-prompt score matrices where
   needed and document the analysis protocol.
6. Define any subgroup or error analysis before inspecting subgroup outcomes;
   treat exploratory analyses as descriptive.
7. Compare against published routing baselines only where a fair and reproducible
   comparison is feasible.

## Reproducibility note

The Day 4 feature-column ordering was hardened after the saved Day 4 run.
The corrected script passed Python syntax validation, but the experiment was
not rerun. The saved Day 4 results therefore remain the output of the original
execution. The current extractor's feature order matches the explicit FEATURES
list, so the change is defensive rather than evidence of a known result error.

The Day 8 script heading was corrected after the summary artifact was generated.
The summary heading correction is documentation-only and does not change results.

## Final recommendation

Do not add another experiment until the provenance and prior-art blockers
are resolved and a specific, preregisterable analysis is defined. If those
checks reveal no defensible gap, retain this work as a transparent negative
result and research-portfolio artifact rather than claiming a novel method.
