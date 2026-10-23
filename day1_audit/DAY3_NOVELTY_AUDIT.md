# Research 3 — Day 3 Novelty Audit

## Objective
Identify a defensible research contribution by comparing the proposed model-selection/router study with the closest prior work.

## Existing pilot
- 750 prompts across ArenaHard Coding, Creative Writing, and Math
- 33 models
- 11 lightweight prompt features
- Ridge-regression score prediction
- Global-model and domain-aware baselines
- Five split seeds
- Preliminary feature-router gains are descriptive; paired confidence intervals include zero

## First-pass prior-art findings

### 1. LLMRouterBench — Findings of ACL 2026
Paper: https://aclanthology.org/2026.findings-acl.1881/
Code: https://github.com/ynulihao/LLMRouterBench

Overlap:
- Same benchmark ecosystem as this pilot
- 33 models and more than 21 datasets
- Ten routing baselines
- Performance-only and performance-cost evaluation
- Model complementarity and oracle-gap analysis

Consequence:
A claim based only on domain specialization or beating a single global model is insufficient.

Required next check:
Read the full paper's experimental protocol, split definitions, baselines, metrics, and limitations. Compare our exact feature-router setup against the closest baselines.

### 2. RACER — ICML 2026
Paper: https://proceedings.mlr.press/v306/hao26c.html

Overlap:
- Risk-aware routing
- Calibration and misrouting-risk control
- Candidate model sets and abstention
- Guarantees evaluated on unseen test data

Consequence:
Uncertainty scores or abstention alone cannot establish novelty.

Required next check:
Determine exactly how its risk guarantee, assumptions, calibration data, and evaluation differ from any proposed method.

### 3. LENS — UAI 2026
Paper: https://proceedings.mlr.press/v337/liu26b.html

Overlap:
- Reliability of feedback-derived signals
- Adaptive routing
- Task and model shifts

Consequence:
Distribution-shift adaptation is not a new claim by itself.

Required next check:
Compare its shift definitions, feedback assumptions, router design, and metrics with the proposed evaluation.

### 4. RouteLLM
Paper: https://arxiv.org/abs/2406.18665
Code: https://github.com/lm-sys/RouteLLM

Overlap:
- Learned model routing
- Quality-cost trade-offs
- Preference-based training and transfer evaluation

Required next check:
Compare training labels, model-pair setup, transfer conditions, and baselines.

### 5. EmbedLLM — ICLR 2025
Paper: https://proceedings.iclr.cc/paper_files/paper/2025/hash/bf5e4b85d203481d6e37bd32d9600162-Abstract-Conference.html

Overlap:
- Learned representations for routing
- Model performance prediction across benchmarks
- Investigation of model specialization

Required next check:
Compare representations, training data, transfer settings, and computational cost.

## Preliminary conclusion
Novelty is NOT established.

The following are not sufficient contributions by themselves:
- Choosing models by domain
- Using prompt features to select a model
- Optimizing quality and cost
- Adding uncertainty estimation or abstention
- Evaluating under task or model shift

## Candidate hypothesis — not yet accepted
A lightweight routing policy may be able to maintain a prespecified quality target under a held-out benchmark-family shift by combining calibrated uncertainty with an explicit fallback decision.

This is only a hypothesis. RACER, LENS, and additional prior work may already cover substantial parts of it.

## Day 3 remaining work
- [ ] Read the closest papers in full.
- [ ] Extract exact methods, data splits, baselines, metrics, assumptions, and limitations.
- [ ] Verify which methods can be reproduced using the existing local results without paid APIs.
- [ ] Define an evaluation split that holds out an entire benchmark family.
- [ ] Determine whether a genuinely distinct and testable contribution remains.
- [ ] Revise the research question before starting new experiments.

## Decision rule
Do not claim novelty based on a new combination of familiar components. Proceed with a proposed contribution only when the closest prior work has been directly compared and a testable distinction remains.

## Day 3 detailed comparison update — LLMRouterBench
- [x] Recorded direct overlap between the benchmark paper and the current pilot.
- [x] Documented missing comparisons against published router baselines.
- [x] Flagged that the current ArenaHard splits do not establish cross-benchmark generalization.
- [x] Added conformal routing with distribution-free safety guarantees as additional close prior art.
- [ ] Inspect the full paper's exact protocols and baseline configurations.
- [ ] Verify the archive's provenance relative to the paper's released data.
- [ ] Select an independent benchmark-family holdout.
- [ ] Finalize the research question only after direct comparison with the closest methods.

## Day 3 comparison update — RACER, LENS, conformal routing
- [x] Compared the primary objectives and mechanisms at a high level.
- [x] Recorded the overlap with uncertainty-aware routing and abstention.
- [x] Flagged that distribution-free guarantees depend on stated assumptions.
- [ ] Complete full-paper and supplement review.
- [ ] Verify exact shift protocols and calibration assumptions.
- [ ] Identify a distinct research question supported by an appropriate dataset.
