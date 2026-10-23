# Day 3 — RACER, LENS, and Conformal Routing Comparison

## Purpose
Compare the closest approaches before choosing a research contribution.

## 1. RACER
Paper: https://proceedings.mlr.press/v306/hao26c.html
Preprint: https://arxiv.org/abs/2603.06616

- Formulates routing as an alpha-VOR problem.
- Outputs model sets rather than relying only on one selected model.
- Uses augmented scoring and nested sets.
- Calibrates thresholds using finite-sample concentration bounds.
- Supports variable set sizes and abstention.
- Claims distribution-free risk control under the paper's stated assumptions.

Overlap with Research 3:
A proposed uncertainty-aware router with a calibrated risk threshold, model sets, or abstention would overlap substantially.

Open question:
Which assumptions are needed for the guarantee, and what happens under genuine distribution shift rather than ordinary held-out evaluation?

## 2. LENS
Paper: https://proceedings.mlr.press/v337/liu26b.html

- Uses interaction feedback to form behavioral signatures.
- Explicitly models latent precision of feedback-derived signals.
- Uses probabilistic utility maximization under imprecise supervision.
- Uses variational inference.
- Evaluates routing under task and model shifts.

Overlap with Research 3:
A proposal based on adapting model selection as tasks change, or down-weighting unreliable feedback, overlaps substantially.

Open question:
Can the existing pilot provide the interaction feedback and repeated observations needed to evaluate a distinct method? The current static score matrix alone does not establish this.

## 3. Conformal LLM Routing with Distribution-Free Safety Guarantees
Paper: https://aclanthology.org/2026.acl-srw.70/
Code and experiment details: https://github.com/IqtedarU/conformal-llm-routing

- Uses a logistic-regression gate over text embeddings.
- Uses Clopper-Pearson calibration to choose a routing threshold.
- Targets a bound on the violation rate among queries routed to a cheaper model.
- Evaluates on GSM8K and MMLU with a cheaper/stronger model pair.
- Shows a trade-off between routing coverage, cost savings, and satisfying the target violation rate.

Overlap with Research 3:
A proposed thresholded router with a calibrated safety or failure-rate constraint would overlap substantially.

Open question:
Compare its guarantee, calibration sample requirements, and assumptions against RACER. Do not assume their guarantees are interchangeable.

## 4. What this comparison means

Already established:
- Routing to a model based on query characteristics.
- Quality-cost optimization.
- Uncertainty or risk-aware routing.
- Abstention and calibrated thresholds.
- Adaptation to task/model shifts.
- Evaluation on multiple benchmark families.

Not established by our pilot:
- A new routing objective or algorithm.
- Statistical superiority to strong routing methods.
- Generalization to an unseen benchmark family.
- Robust safety guarantees under distribution shift.
- A reproducible cost/latency advantage.

## 5. Candidate question for further investigation

Under a prespecified benchmark-family shift, how does the calibration of an existing router change, and can any proposed correction improve target violation-rate control without unacceptable loss of routing coverage?

This is a research question to investigate, not a novelty claim. It is only worth pursuing if a full-paper comparison shows that the exact shift protocol, failure analysis, or correction is not already covered by RACER, LENS, conformal routing, or other prior work.

## 6. Required decisions before implementation
- [ ] Read the full papers and supplementary material.
- [ ] Record each method's assumptions, calibration protocol, shift definitions, and metrics.
- [ ] Identify whether the released implementations can be run without paid APIs.
- [ ] Choose an independent held-out benchmark family.
- [ ] Define the primary metric and target constraint before looking at test results.
- [ ] Determine whether existing archived scores are sufficient for a fair comparison.
- [ ] Abandon or revise the candidate if the closest methods already cover it.

## Conclusion
The three methods substantially narrow the available novelty space. Combining uncertainty, shift adaptation, and fallback is not enough by itself. The next decision must be driven by a specific uncovered limitation and a feasible, leakage-resistant experiment.
