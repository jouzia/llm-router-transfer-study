# Day 3 — Detailed Paper Comparison 1

## Paper
Hao Li et al. (2026), "LLMRouterBench: A Massive Benchmark and Unified Framework for LLM Routing."
Venue: Findings of the Association for Computational Linguistics (ACL) 2026.
Paper: https://aclanthology.org/2026.findings-acl.1881/
PDF: https://aclanthology.org/2026.findings-acl.1881.pdf
Repository: https://github.com/ynulihao/LLMRouterBench

## What the paper establishes
The paper consolidates 33 models, 21+ datasets, and 10 representative routing methods in a common evaluation framework. It studies performance-oriented and performance-cost routing, and evaluates simple baselines such as random selection, best single model, and an oracle upper bound. It reports that leading routers can have similar performance, some do not reliably outperform a simple baseline, and a gap remains between practical routing and oracle selection.

The paper also discusses model complementarity, model-recall failures, diminishing returns from larger model pools, and latency-aware analysis.

## Direct overlap with our pilot

Our pilot:
- Uses result records from the LLMRouterBench archive.
- Uses 750 prompts across ArenaHard Coding, Creative Writing, and Math subsets.
- Evaluates 33 models.
- Builds 11 lexical/structural prompt features.
- Uses ridge regression to predict model scores and selects the predicted best model.
- Compares against a global-model baseline and a domain-aware baseline.

Overlap:
1. Selecting a model per prompt is the central task of LLM routing.
2. Model complementarity and task-dependent model performance are already established.
3. Comparing a router with a global best model and an oracle is already established.
4. Performance-cost routing and latency-aware routing are already established.
5. The paper evaluates numerous stronger routing baselines that our pilot has not yet reproduced or compared against.

## What our pilot has NOT demonstrated
- Superiority over the published routing methods in LLMRouterBench.
- Generalization to an independent benchmark family.
- Reliable statistical improvement over the simple baselines.
- Valid cost or latency optimization, because archived aggregate cost fields are inconsistent and field semantics remain unresolved.
- Novelty of the 11-feature ridge router.
- A novel uncertainty, calibration, abstention, or shift-handling method.

## Important evaluation issue
The three ArenaHard subsets are closely related. Random train/validation/test splits within these subsets measure held-out prompt performance within this benchmark setting, not cross-benchmark generalization.

Before using the phrase "unseen-domain generalization", the evaluation must hold out a complete benchmark family or another defensibly independent source. The split must be designed to prevent the same source prompts or duplicated items from appearing in training and test data.

## Additional close prior art
"Iqtedar Uddin and André Bauer (2026), Conformal LLM Routing with Distribution-Free Safety Guarantees."
Paper: https://aclanthology.org/2026.acl-srw.70/

This work directly studies input-based routing with a calibrated constraint on the violation rate among routed queries. It is a strong warning against claiming novelty from uncertainty estimation, a threshold, or abstention alone.

## Current conclusion
The pilot is a useful feasibility experiment, but it does not establish a novel routing method. A contribution must be defined by a specific, testable distinction from prior methods and then evaluated against those methods under a defensible protocol.

## Required next actions
1. Extract the exact routing algorithms and configurations evaluated by LLMRouterBench.
2. Read the full paper's experimental setup, split protocol, metrics, and limitations.
3. Inspect the implementation of the closest available baselines.
4. Verify the archive's relationship to the paper's released benchmark outputs.
5. Identify a genuinely independent benchmark-family holdout.
6. Compare the proposed research question against RACER, LENS, and conformal routing work.
7. Only then decide whether a new method is warranted.

## References
- LLMRouterBench paper: https://aclanthology.org/2026.findings-acl.1881/
- LLMRouterBench code: https://github.com/ynulihao/LLMRouterBench
- Conformal LLM Routing: https://aclanthology.org/2026.acl-srw.70/
- RACER: https://proceedings.mlr.press/v306/hao26c.html
- LENS: https://proceedings.mlr.press/v337/liu26b.html
- RouteLLM: https://arxiv.org/abs/2406.18665
- EmbedLLM: https://proceedings.iclr.cc/paper_files/paper/2025/hash/bf5e4b85d203481d6e37bd32d9600162-Abstract-Conference.html
