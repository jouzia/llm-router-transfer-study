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

### Archive identity and exact overlap

The repository README records the expected SHA-256 of the local `bench-release.tar.gz` as:

`B79F8CDE1A6F029C2EFA663A3A3B6F7748DEFB22341FE59F328CEBEF6648C8F1`

The official Hugging Face dataset `NPULH/LLMRouterBench` publishes the exact same SHA-256 and a 1.28 GB `bench-release.tar.gz`. The project history records that the local archive hash was verified. Therefore the local archive is byte-for-byte identical to the official LLMRouterBench release; this is stronger than a similarity inferred from matching dataset sizes.

The archive inventory in this repository contains:
- 27 top-level dataset directories.
- ArenaHard-derived source partitions `arenahard_coding`, `arenahard_creative_writing`, and `arenahard_math`, with 253, 250, and 247 prompts respectively (750 total), and 33 model files in each partition.
- GPQA test records with 198 prompts in the experiment's matched 13-model pool.
- MMLU-Pro `test_3000` records with 3,000 prompts in the experiment's matched 13-model pool.

The current Day 6/Day 9 candidate set is exactly the same 13-model membership as the official performance–cost pool. The list order differs from the upstream YAML order, but the names match.

**Novelty consequence:** the underlying benchmark records, model pool, and benchmark task selection are not new. The project must be framed as a secondary analysis / protocol-specific transfer evaluation over LLMRouterBench data, not as an independently assembled benchmark or new benchmark suite.

The archive also contains an `arenahard` directory in addition to the three subcategory directories. The 750-row sum of the subcategories matches the published ArenaHard count, but a row-by-row key and normalized-prompt comparison between the three subcategory tables and the aggregate `arenahard` directory has not yet been run. Do not claim that mapping is verified until that check passes.

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
- The official performance–cost config's 13-model membership matches the current Day 6/Day 9 pool exactly.
- The checked-in config whitelists `arenahard`, `gpqa`, and `mmlupro`, but not the three source IDs `arenahard_coding`, `arenahard_creative_writing`, and `arenahard_math`. A custom config is required to include the three source partitions and both targets.
- The loader's dataset-level OOD option can place all GPQA and MMLU-Pro records in test while retaining the ArenaHard subcategories for training. Its split operates on prompts and keeps all model records for a prompt together.
- The Avengers-Pro adaptor supports the OOD argument and writes test-set baseline scores separately for post-hoc reporting. Its router training method builds clusters and per-cluster model rankings from training records, then routes test prompts from their embeddings. The target score matrix is used for evaluation/reporting, not for the cluster ranking step, but the full execution should still be checked in an end-to-end run.
- The inspected GraphRouter adaptor currently calls the split function with `ood_datasets=None`; it does not expose the same OOD path without modification.
- The default Avengers-Pro simple config uses hosted `gte_Qwen2-7B-instruct` embeddings. The upstream paper reports an embedding ablation that includes `all-MiniLM-L6-v2`, but the checked-in router code expects an OpenAI-compatible embedding endpoint. A no-paid-API run would require a local compatible embedding service or a carefully documented local-backend adaptation. This has not yet been implemented or tested.

**Updated feasibility assessment:** the official archive and model pool are now identified exactly. The Avengers-Pro OOD path can be configured for the three ArenaHard source partitions and GPQA/MMLU-Pro targets, using only the pre-collected score matrix. However, a fair, reproducible run is not yet demonstrated: the config must be adapted, the local embedding backend must be implemented or served, and the resulting protocol must be compared against the paper's published configuration.

A further code inspection shows the Avengers-Pro router loads `baseline_scores` in its evaluation/reporting path after routing results have been computed; the adaptor generates that file from test records. This appears intended for post-hoc baseline comparison, but the complete execution path should be checked before ruling out any target-score influence.

The checked-in simple configuration uses a hosted embedding endpoint and an embedding model substantially larger than the current lexical-feature router. Thus, the official code path is not yet confirmed as zero-cost or suitable for the available CPU-only local environment. A local embedding backend or a different lightweight baseline may be needed. Do not start a paid embedding/API run.

### Immediate implication

A defensible comparison should:
1. Compare the three source partitions against the aggregate `arenahard` directory at row-key and normalized-prompt level; document any differences.
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

This paper trains an input-only logistic gate on BGE text embeddings and uses Clopper–Pearson calibration to bound, with confidence level 1−δ, the violation rate among queries routed to a cheaper model. Its binary safety label is 0 only when the cheap model is wrong and the expensive model is correct; it uses a held-out calibration set and requires exchangeability between calibration and test data. The experiments use four disjoint partitions (55/15/15/15%) for gate training, calibration, validation, and testing. The paper explicitly distinguishes its input-only conditional violation guarantee from RACER's output-dependent expected-risk/model-set guarantee.

**Overlap:** input-based gating, calibrated fallback, explicit safety criteria, and the model/task-dependent feasibility diagnostic.

**Difference / feasibility:** the current source audit found no independent ground-truth answers in the inspected ArenaHard records (0% source ground-truth coverage). Its ternary judge-derived scores are not automatically equivalent to independently verified correctness labels. Target GPQA/MMLU-Pro ground-truth availability has not yet been audited in this project. If target labels are available, a separate within-target conformal experiment may be feasible using a target-specific train/calibration/test split; that would not be source-only cross-benchmark transfer. Calibrating on ArenaHard and claiming a guarantee on GPQA/MMLU-Pro would require exchangeability across those benchmark/evaluator distributions, which is not established. Do not claim the paper's safety guarantee from the current source-to-target experiment.

### How Robust Are Router-LLMs? — EACL 2026

Paper: https://aclanthology.org/2026.eacl-long.351/

This work introduces the DSC benchmark with categorized query types and evaluates preference-based and commercial routers across code, translation, math, instruction, knowledge, jailbreak, privacy, and safety-related cases. It finds that routers can rely on category-level heuristics rather than query difficulty: in its tested setup, simple code/math queries were often sent to the stronger model. It also perturbs queries with category keywords and reports an average 98% routing-decision flipping rate for the tested keyword additions.

**Overlap:** category-dependent router behavior, routing concentration, and prompt-keyword sensitivity are already studied. This is particularly relevant because the current Ridge router uses lexical/structural prompt features. A prompt-feature perturbation audit is therefore a necessary robustness check. The current 11 features are counts and structural indicators (length, digits, punctuation, code symbols/fences, URLs, equation symbols, and a small question-word indicator), not semantic keyword embeddings. Test controlled additions/removals of neutral text, question words, code symbols/fences, equation markers, and URLs; report route-flip rates and score-prediction changes separately. This is a sensitivity audit, not proof that the underlying answer would remain unchanged.

**Difference / feasibility:** DSC evaluates preference-based pairwise routers and commercial routers on its own datasets; it does not establish the behavior of this 13-model, score-regression, source-to-target router. The current source domains and two target benchmarks also do not cover the full safety, privacy, or jailbreak scope. The current project should not use broad “router robustness” language without expanding and separately validating those dimensions.

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
- [x] Conformal LLM Routing full paper reviewed directly, including binary safety labels, four-way split, calibration guarantee, and exchangeability requirement.
- [x] EACL robustness paper reviewed directly, including methodology, keyword perturbation analysis, router types, and limitations.
- [x] RACER official publication record and abstract reviewed.
- [x] LENS official publication record and abstract reviewed.
- [x] RACER full method reviewed directly; supplementary implementation remains to be inspected.
- [ ] LENS full method and supplement reviewed.
- [x] DSC full paper reviewed; no separate supplementary package identified in the reviewed publication.
- [x] Local archive byte identity with official LLMRouterBench release verified via matching SHA-256; source-partition-to-aggregate ArenaHard row mapping still pending.
- [ ] Avengers-Pro OOD baseline adapted to the three source partitions and two target datasets, with a free local embedding backend.
- [ ] Novelty decision finalized.

**Current decision:** retain the empirical transfer study as a conditional research direction. Do not present it as a novel routing method.