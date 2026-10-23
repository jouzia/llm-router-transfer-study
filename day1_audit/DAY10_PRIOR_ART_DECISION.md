# Research 3 — Day 10 Prior-Art Decision

Date: 2026-10-23

## 1. Current research status

The current method uses 11 lexical and structural prompt features and Ridge regression to predict per-model scores. It was trained on 750 ArenaHard prompts across coding, creative writing, and mathematics.

Transfer evaluations:
- GPQA: 198 prompts.
- MMLU-Pro test_3000: 3,000 prompts.
- Repeated source-validation splits: seeds 2026–2035.

Current evidence does not establish that the router outperforms the strongest fixed-model baseline.

## 2. Closest prior work and implications

### LLMRouterBench — Findings of ACL 2026
https://aclanthology.org/2026.findings-acl.1881/

The benchmark evaluates 10 routing baselines over 21 datasets and 33 models. Its results show that multiple routers do not reliably outperform a simple baseline.

Implication: a new benchmark comparison or another weak-router result is not sufficient novelty.

### RACER — ICML 2026
https://proceedings.mlr.press/v306/hao26c.html

RACER constructs nested model sets, calibrates thresholds, permits abstention, and targets distribution-free misrouting-risk control under stated assumptions.

Implication: calibrated fallback, abstention, or generic risk-aware routing is not novel by itself.

### LENS — UAI 2026
https://proceedings.mlr.press/v337/liu26b.html

LENS models the reliability of interaction-derived feedback and evaluates routing under task and model shifts.

Implication: generic adaptation to benchmark or model shift is not novel by itself.

### Conformal LLM Routing with Distribution-Free Safety Guarantees — ACL 2026
https://aclanthology.org/2026.acl-srw.70/

This work trains an embedding-based logistic gate and calibrates a routing threshold to control the violation rate among queries sent to a cheaper model, under stated assumptions.

Implication: an input-based calibrated safety gate overlaps with established work. Replacing embeddings with lexical features would not, by itself, establish novelty.

### How Robust Are Router-LLMs? — EACL 2026
https://aclanthology.org/2026.eacl-long.351/

This work examines routing weaknesses across query categories, including safety and privacy-related behavior.

Implication: a broad claim about router robustness or category-dependent errors is insufficient.

## 3. Existing empirical evidence

### MMLU-Pro
- Router: 83.8667%.
- Gemini 2.5 Pro: 85.6667%.
- Difference: -1.80 percentage points.
- The paired prompt-bootstrap interval for the difference excludes zero in the negative direction.

### GPQA
- Router: approximately 81.82% to 82.32% across source-validation splits.
- Gemini 2.5 Pro: 84.8485%.
- The router trails Gemini in all 10 repeated splits.
- The target set contains 198 prompts; uncertainty is substantial.

### Baseline-selection sensitivity
The router's apparent advantage changes when the validation-selected baseline changes. Across repeated splits, it trails Gemini consistently. Claims of superiority over the best fixed model are unsupported.

Repeated seeds reuse the same target prompts. They are not independent target samples.

## 4. Research decision

Decision: NO-GO for claiming a novel routing algorithm based on the current evidence.

Conditional GO for a rigorous empirical study of cross-benchmark transfer failure, provided it adds a clearly specified and reproducible analysis beyond reporting aggregate accuracy.

Provisional study question:

"How reliably does a lightweight lexical-feature router transfer across benchmark families, and which error patterns explain its performance gap relative to the strongest fixed-model baseline?"

This question is provisional and must be checked against the complete prior art before a novelty claim is made.

## 5. Next analysis — prespecified and diagnostic

1. Verify the router implementation, source split, validation selection, and target evaluation paths for leakage.
2. Recompute per-prompt paired outcomes against Gemini on GPQA and MMLU-Pro from the aligned score matrix.
3. Report accuracy, paired differences, confidence intervals, router-choice frequencies, and per-selected-model outcomes.
4. Keep benchmark-specific diagnostics descriptive unless a primary hypothesis and analysis plan are specified before examining subgroup results.
5. Do not select a new method, feature set, threshold, or subgroup based on target-test performance.
6. Verify score semantics, prompt alignment, archive provenance, and licensing before publication or redistribution.
7. Compare against released routing baselines only where implementation, inputs, labels, and evaluation protocol can be reproduced fairly.

## 6. Claims currently permitted

Supported:
- The evaluated lexical-feature Ridge router underperforms Gemini 2.5 Pro on the two reported held-out benchmarks.
- Apparent gains over a validation-selected baseline depend on which baseline is selected.
- The current experiments do not establish reliable superiority or generalization across benchmark families.

Not supported:
- The method is novel.
- The router outperforms the best fixed model.
- The router has distribution-free safety guarantees.
- The results prove that lexical-feature routing generally fails.
- The archive's licensing is verified.

## 7. Completion checklist

- [x] Initial baseline and repeated-split results exist.
- [x] Two held-out benchmark families evaluated.
- [x] Initial prior-art comparison recorded.
- [ ] Full implementation and leakage audit completed.
- [ ] Per-prompt paired analysis independently verified.
- [ ] Archive provenance and license status resolved.
- [ ] Final contribution and publication suitability decided.
