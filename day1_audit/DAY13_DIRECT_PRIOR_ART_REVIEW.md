# Day 13 — Direct Prior-Art Review and Contribution Boundary

**Review date:** 31 October 2026  
**Branch:** `research3-integrity-audit`  
**Scope:** Direct comparison of the current transfer study with the closest identified routing benchmark and risk/shift-aware routing papers.

## 1. Executive decision

**Conditional GO** remains appropriate for a carefully bounded empirical study of source-to-target benchmark transfer and baseline sensitivity.

**NO-GO** for claiming a novel routing algorithm, a new safety guarantee, broad robustness, or superiority over the best-performing fixed model.

The most consequential overlap is with **LLMRouterBench (Findings of ACL 2026)**. Its performance–cost setting uses the same 13-model flagship pool as the current Day 6/Day 9 experiments and includes ArenaHard (750 prompts), GPQA (198 prompts), and MMLU-Pro (3,000 prompts). These matching model-pool and dataset counts make it the closest benchmark-level comparator. The precise row-level identity and partition mapping still need to be verified against the released benchmark files; matching counts alone are not proof of identical prompt rows.

## 2. Direct comparison: LLMRouterBench

Paper: https://aclanthology.org/2026.findings-acl.1881/  
Code/data: https://github.com/ynulihao/LLMRouterBench

### What the paper covers

The paper introduces a unified benchmark with 13 flagship models in its performance–cost setting and 20 lightweight models in its performance-oriented setting. It evaluates nine representative routing methods with available open-source implementations, plus OpenRouter, and reports five-run results for dataset-level evaluations.

The performance–cost dataset table includes:
- ArenaHard: 750 prompts, categorized as instruction following and scored by an LLM judge.
- GPQA: 198 prompts, accuracy.
- MMLU-Pro: 3,000 prompts, accuracy.

The paper includes HybridLLM, FrugalGPT, RouteLLM, GraphRouter, Avengers-Pro, and OpenRouter in its performance–cost comparisons. It also defines Random Router, Best Single, and Oracle references. Its Best Single baseline is selected in hindsight using average accuracy across evaluation datasets; that is a benchmark reference, not a source-only deployable selection rule.

### Overlap with this repository

| Dimension | Current study | LLMRouterBench |
|---|---|---|
| Flagship candidate pool | 13 models in Days 6 and 9 | 13 flagship models in performance–cost setting |
| Source prompt count | 750 ArenaHard-derived prompts | ArenaHard, 750 prompts |
| GPQA target count | 198 | GPQA, 198 |
| MMLU-Pro target count | 3,000 | MMLU-Pro, 3,000 |
| Router | 11 lexical/structural features + standardized Ridge score predictors | Multiple published routers, including learned and clustering-based methods |
| Main protocol | Fit/select on ArenaHard source domains; evaluate on held-out GPQA and MMLU-Pro | Unified evaluation of routing methods with consistent train/test splits; per-dataset results and aggregate comparisons |
| Main baseline distinction | Source-validation-selected single model plus fixed Gemini reference | Random Router, hindsight Best Single, Oracle; performance–cost trade-off baselines |

### What is and is not established

The paper clearly establishes that these benchmark datasets and candidate models have already been assembled into a common routing evaluation suite. Therefore, merely evaluating a router on this model pool or reporting results on these three datasets is not a novel contribution.

The current repository's source-only cross-dataset training/evaluation question may still be methodologically distinct from the paper's reported per-dataset router evaluations. The full paper documents consistent train/test splits for routing methods, but the reviewed text did not establish that it evaluates the exact ArenaHard-to-GPQA/MMLU-Pro transfer protocol used here. This distinction must be verified against the released code and split adapters before any novelty claim.

The paper's Best Single baseline is selected in hindsight across the evaluation suite. It should not be conflated with the current source-validation-selected baseline, which is selected without target scores. Conversely, Gemini 2.5 Pro is a useful descriptive fixed-model reference, but if it was designated as the strongest fixed model after inspecting target outcomes, it must be labelled a retrospective benchmark reference—not a source-only selected deployment baseline.

### Official code and OOD-baseline feasibility check

A first direct inspection of the official LLMRouterBench repository confirms that its baseline data loader exposes `split_by_dataset_then_prompt(..., ood_datasets=...)`. The documented behavior is to split prompts within in-distribution datasets while placing every record from named OOD datasets in the test set. The Avengers-Pro adaptor exposes this option through `--ood-datasets`.

This is important: the official framework has an explicit code path for dataset-level OOD evaluation, so the current ArenaHard-to-GPQA/MMLU-Pro protocol should not be described as absent from the benchmark infrastructure. However, the existence of an OOD option does not prove that the published paper reports this exact source/target combination, nor that the current study has reproduced it.

Implementation caveats found:
- The official performance–cost config lists the 13 flagship models used by the current Day 6/Day 9 pool.
- That config uses dataset identifiers such as `arenahard`, `gpqa`, and `mmlupro`; the current feature table uses `arenahard_coding`, `arenahard_creative_writing`, and `arenahard_math`. The mapping and prompt identity must be verified before reusing the config unchanged.
- The Avengers-Pro adaptor supports the OOD argument, but its algorithm-level fairness, data requirements, model-pool ordering, and evaluation behavior still need review.
- The inspected GraphRouter adaptor currently calls the split function with `ood_datasets=None`; it does not expose the same OOD path without modification.
- The official framework's general adaptor documentation describes OOD support, but this does not mean every individual router adaptor implements it.

**Updated feasibility assessment:** at least one official baseline path (Avengers-Pro) appears technically adaptable to a source-to-target OOD evaluation without recollecting model outputs. A fair, reproducible baseline comparison is therefore plausible, but not yet demonstrated. Check the exact dataset mapping, split behavior, baseline implementation, dependency/resource requirements, and whether the method can be run without paid inference APIs before selecting it.

A further code inspection shows the Avengers-Pro router loads `baseline_scores` in its evaluation/reporting path after routing results have been computed; the adaptor generates that file from test records. This appears intended for post-hoc baseline comparison, but the complete execution path should be checked before ruling out any target-score influence.

The checked-in simple configuration uses a hosted embedding endpoint and an embedding model substantially larger than the current lexical-feature router. Thus, the official code path is not yet confirmed as zero-cost or suitable for the available CPU-only local environment. A local embedding backend or a different lightweight baseline may be needed. Do not start a paid embedding/API run.

### Immediate implication

A defensible comparison should:
1. Verify that the 750 source rows map exactly to the ArenaHard rows in the release, including the coding/creative-writing/math partition labels.
2. Verify the 13 candidate names and ordering against the benchmark's performance–cost pool.
3. Inspect the official adapters and reproduce at least the most relevant published baseline(s) on the same eligible rows and split conditions, if technically feasible.
4. Keep the current source-only selection protocol separate from hindsight Best Single and target-best fixed-model references.
5. Avoid claiming that matching dataset counts establish an independent benchmark replication.

## 3. Direct comparison: risk- and shift-aware methods

### RACER — ICML 2026

Paper: https://proceedings.mlr.press/v306/hao26c.html

RACER formulates routing as the **α-Valid Optimal Routing (α-VOR)** problem: minimize expected selected-model-set size while controlling the probability that the selected set excludes every ground-truth-correct model. It adds a virtual null model to represent cases where no candidate is correct, constructs nested model sets from an arbitrary base router's scores, calibrates a threshold on labelled calibration data using finite-sample concentration bounds, and can abstain or aggregate selected model outputs. Its distribution-free risk guarantee is explicitly conditional on exchangeability between calibration and test examples.

**Overlap:** calibrated risk-aware routing, model selection uncertainty, and fallback/abstention are already active research directions.

**Difference / feasibility:** the current project is a single-model argmax router and does not implement nested model sets or a risk-control guarantee. More importantly, RACER's calibration requires a ground-truth set of all candidate models that answer each calibration query correctly. The current ArenaHard source audit reports no independent ground-truth answers (0% coverage); its judge-derived ternary scores are not automatically equivalent to RACER's correctness sets. In addition, calibrating on ArenaHard and evaluating on GPQA/MMLU-Pro is precisely a cross-benchmark shift, so RACER's exchangeability condition cannot simply be assumed. A faithful distribution-free guarantee is therefore not supported by the current source data and transfer protocol. A static score matrix may support descriptive model-set analysis, but not the published guarantee without valid correctness labels and defensible calibration/test assumptions.

### LENS — UAI 2026

Paper: https://proceedings.mlr.press/v337/liu26b.html

LENS models latent precision in interaction-derived behavioral signals and uses probabilistic inference to reduce the influence of unreliable feedback under task and model shifts.

**Overlap:** reliability of router evidence and performance under task/model shift.

**Difference / feasibility:** the current archive is a static collection of prompt-level model scores; it does not appear to contain the longitudinal interaction feedback, selective logging, or temporal feedback-quality information central to LENS. Generic claims about shift adaptation are therefore not novel, but a faithful LENS reproduction is not currently supported by the known data.

### Conformal LLM Routing with Distribution-Free Safety Guarantees — ACL 2026 Student Research Workshop

Paper: https://aclanthology.org/2026.acl-srw.70/

This paper trains an input-only logistic gate on text embeddings and uses Clopper–Pearson calibration to bound the violation rate among queries routed to a cheaper model, under exchangeability between calibration and test data. Its safety label compares cheap- and expensive-model correctness against ground truth.

**Overlap:** input-based gating, calibrated fallback, and explicit safety criteria.

**Difference / feasibility:** the current archive audit found no ground-truth answers in the inspected records (0% ground-truth coverage). The recorded scores therefore cannot automatically be treated as the paper's independent binary correctness labels. A faithful safety guarantee cannot be claimed by simply thresholding the current score matrix; the label definition and exchangeability assumptions would need to be justified independently.

### How Robust Are Router-LLMs? — EACL 2026

Paper: https://aclanthology.org/2026.eacl-long.351/

This work introduces the DSC benchmark with categorized query types and evaluates routing behavior across code, translation, math, instruction, knowledge, jailbreak, privacy, and safety-related cases. It reports category-driven routing failures and risks.

**Overlap:** category-dependent router behavior and error analysis are already studied.

**Difference / feasibility:** the current source domains and two target benchmarks do not cover the full safety, privacy, or jailbreak scope. The current project should not use broad “router robustness” language without expanding and separately validating those dimensions.

## 4. Additional methodological issue: evaluator/metric shift

The official LLMRouterBench paper's dataset table describes ArenaHard as an instruction-following benchmark scored by an LLM judge, while GPQA and MMLU-Pro are scored using accuracy. The current source audit records a ternary ArenaHard score domain (0, 0.5, 1); the Day 9 GPQA script explicitly validates binary target scores (0, 1). The target MMLU-Pro score matrix is also treated as correctness/accuracy in the experiment reports.

Consequently, the current transfer experiment changes more than prompt domain or benchmark family. It also transfers a score predictor trained against a judge-derived, ternary source metric to targets evaluated with binary accuracy. This is a substantive **evaluator/metric shift**.

Implications:
- Do not attribute the observed performance gap solely to semantic benchmark-family shift.
- Describe the setup as joint task/benchmark and evaluator/score-semantic transfer unless the metric shift is separately controlled.
- The source archive's lack of independent ground-truth answers prevents a simple post-hoc conversion of ArenaHard judge scores into independently verified binary correctness labels.
- A stronger design would include an additional source/target pair scored under a common metric, or a controlled experiment that separates prompt-domain shift from evaluator/label shift.
- Any comparison with the conformal safety-gate paper must respect its binary correctness label definition; the current ternary judge scores are not automatically interchangeable.

## 5. Interpretation of the current results after this review

The Day 9 matched-pool GPQA run is an important protocol correction: it uses the same 13-model candidate pool as Day 6 and selects its global baseline from source validation only.

- GPQA router mean score: 0.818182.
- Source-selected Qwen3 Thinking baseline: 0.803030.
- Paired difference: +0.015152.
- 95% prompt-bootstrap interval: [−0.020202, +0.050505].
- Wins / ties / losses: 8 / 185 / 5.

This is an inconclusive positive point estimate, not evidence of established improvement. The interval includes zero. Against Gemini 2.5 Pro, the router remains 3.03 percentage points lower on this GPQA sample.

For MMLU-Pro Day 6, the router exceeds the source-selected Qwen3 Thinking baseline by 4.40 percentage points, but trails Gemini 2.5 Pro by 1.80 percentage points. These are different baseline questions and must remain separate.

The repeated source-validation splits reuse the same target prompts. They are selection-sensitivity analyses, not independent target replications.

## 6. Contribution boundary

### Supported at present

- A reproducibility and integrity-audited empirical evaluation of an 11-feature Ridge router trained on 750 ArenaHard-derived prompts.
- A source-only model/regularization selection protocol evaluated on GPQA and MMLU-Pro.
- A comparison showing that apparent router gains depend materially on the fixed-model baseline selection rule.
- A transparent negative/inconclusive result against a strong fixed-model reference.

### Not supported at present

- A novel routing algorithm.
- State-of-the-art routing performance.
- Superiority over the best-performing single model.
- A distribution-free risk or safety guarantee.
- Broad robustness across safety, privacy, jailbreak, or deployment settings.
- Cost or latency savings.
- Generalization to arbitrary benchmark families.

## 7. Required next steps

1. **Release identity check:** compare the local 750 ArenaHard prompt identifiers and exact prompt text with the official LLMRouterBench release; document the domain-partition mapping.
2. **Candidate-pool check:** compare all 13 names and their order with the official performance–cost model pool.
3. **Official-baseline feasibility:** inspect the benchmark's adapters and determine which published baseline can be run fairly without paid API calls or unavailable features. Record infeasible methods and why.
4. **Protocol audit:** confirm that target scores never enter feature design, alpha selection, model-pool selection, or source baseline selection.
5. **Inference audit:** preserve prompt-level paired uncertainty and state clearly that the bootstrap intervals condition on the observed prompts.
6. **Prior-art completion:** inspect the full RACER and LENS methods/supplements and the full DSC paper before marking the literature review complete.
7. **Manuscript synchronization:** update the references and contribution language only after the direct comparison is complete.

## 8. Review status

- [x] LLMRouterBench official paper reviewed directly, including model pools, dataset sizes, metrics, baseline definitions, and routing-baseline families.
- [x] Conformal LLM Routing paper reviewed directly for its gate, label definition, calibration, and exchangeability condition.
- [x] EACL robustness paper identified and its published abstract reviewed.
- [x] RACER official publication record and abstract reviewed.
- [x] LENS official publication record and abstract reviewed.
- [x] RACER full method reviewed directly; supplementary implementation remains to be inspected.
- [ ] LENS full method and supplement reviewed.
- [ ] DSC full method and supplement reviewed.
- [ ] Exact row-level ArenaHard release identity verified.
- [ ] Official baseline reproduction feasibility completed.
- [ ] Novelty decision finalized.

**Current decision:** retain the empirical transfer study as a conditional research direction. Do not present it as a novel routing method.