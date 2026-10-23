# Day 9 — Prior-Art Matrix and Research Decision

## Current method

- Source: 750 ArenaHard prompts across coding, creative writing, and mathematics.
- Features: 11 lexical and structural prompt features.
- Model: Ridge regression predicting per-model scores.
- Evaluation: held-out GPQA and MMLU-Pro, plus repeated source-validation splits.
- Current result: the router trails Gemini 2.5 Pro on both target benchmarks.
- Novelty status: not established.

## Closest prior work

### LLMRouterBench — Findings of ACL 2026
Official paper: https://aclanthology.org/2026.findings-acl.1881/

Scope:
- More than 400K instances, 21 datasets, and 33 models.
- Ten representative routing baselines.
- Performance and performance-cost evaluation.
- Reports that several routers do not reliably outperform Best Single.

Required comparison:
- Establish whether the current data and score semantics match the released benchmark.
- Identify which baselines can be evaluated fairly using archived per-prompt scores.
- Document any differences in candidate models, splits, and metrics.

### RACER — ICML 2026
Official paper: https://proceedings.mlr.press/v306/hao26c.html

Scope:
- Risk-aware routing that produces model sets.
- Threshold calibration and abstention.
- Distribution-free risk-control claims under stated assumptions.

Required comparison:
- Inspect the precise risk definition, calibration protocol, and assumptions.
- Determine whether the available score matrix supports a fair reproduction.

### LENS — UAI 2026
Official paper: https://proceedings.mlr.press/v337/liu26b.html

Scope:
- Models latent precision in interaction-derived feedback.
- Studies routing under task and model shifts.

Required comparison:
- Inspect the feedback requirements, inference procedure, shift protocols, and baselines.
- Determine whether static archived scores are sufficient.

### Conformal LLM Routing with Distribution-Free Safety Guarantees — ACL 2026
Official paper: https://aclanthology.org/2026.acl-srw.70/

Scope:
- Embedding-based logistic gate.
- Clopper-Pearson calibration of a routing threshold.
- Controls a violation rate among queries routed to a cheaper model, under exchangeability assumptions.

Required comparison:
- Inspect calibration sample requirements and feasibility conditions.
- Distinguish its conditional violation-rate guarantee from ordinary accuracy optimization.
- Do not assume the guarantee survives arbitrary distribution shift.

## Candidate research question — provisional

Can a routing system detect when its policy becomes unreliable under benchmark-family shift and identify when adaptive routing should be replaced by a fixed-model fallback?

This is a hypothesis for investigation, not an established novelty claim.

## Go/no-go criteria

Proceed only if:
1. The closest papers and supplements are reviewed directly.
2. A precise gap not already covered by those methods is identified.
3. The available data support a leakage-resistant experiment.
4. The primary metric, baseline, and decision criteria are specified before target evaluation.
5. The archive's provenance, licensing, and score semantics are documented.

Otherwise, revise the question or retain the current work as a rigorous negative-result study.

## Status

- [x] Initial comparison based on official publication records and abstracts.
- [ ] Full method and supplement review completed for all four papers.
- [ ] Fair baseline feasibility established.
- [ ] Archive provenance and licensing resolved.
- [ ] Research question accepted or rejected.
