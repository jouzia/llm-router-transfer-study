# Evaluating Cross-Benchmark Transfer of a Lightweight LLM Router

**Author:** Shaik Jouzia Afreen H.
**Status:** Manuscript draft; regenerate and cross-check results against committed artifacts before submission.
**Repository:** [https://github.com/jouzia/llm-router-transfer-study](https://github.com/jouzia/llm-router-transfer-study)

## Abstract

Large language model (LLM) routers select a model for each input, aiming to exploit complementary model strengths. A router that performs well on source tasks may not retain its advantage on a different benchmark. This study evaluates a lightweight prompt-feature router trained using records from three ArenaHard domains—coding, creative writing, and mathematics—and tests transfer to GPQA and MMLU-Pro. The source extraction audit reports 750 prompts, 33 models, 11 prompt features, and no detected prompt-text, ground-truth, record-availability, or score-alignment inconsistencies. In the current reported evaluation, the router obtains a mean score of 0.8182 on 198 GPQA prompts, compared with 0.8485 for a fixed Gemini 2.5 Pro baseline (difference −3.03 percentage points; reported prompt-bootstrap 95% confidence interval [−7.07, +1.01] percentage points). On 3,000 MMLU-Pro test prompts, the router obtains a mean score of 0.8387, compared with 0.8567 for Gemini 2.5 Pro (difference −1.80 percentage points; reported interval [−2.50, −1.13] percentage points). A source-validation-selected baseline can be weaker: on MMLU-Pro, the router exceeds the selected Qwen3 Thinking baseline by 4.40 percentage points, but this does not establish superiority over the stronger fixed Gemini baseline. Repeated source-validation splits reuse the same target prompts and are sensitivity analyses, not independent replications. The current evidence supports a cautious empirical transfer study, but not a claim that the router outperforms the fixed Gemini baseline or establishes a novel routing algorithm. The score semantics, candidate-model eligibility rules, and correspondence between generated results and committed code must be confirmed before submission.

**Keywords:** large language models; model routing; cross-benchmark transfer; generalization; evaluation methodology; reproducibility

## 1. Introduction

LLM routing assigns each query to a model from a candidate pool. Its motivation is that different models may have complementary strengths, while routing may improve response quality, cost, or latency relative to always using one model. However, source-domain performance does not guarantee transfer to a held-out benchmark, and conclusions can change depending on the fixed-model baseline.

This study asks: **How well does a lightweight prompt-feature router trained on ArenaHard coding, creative-writing, and mathematics records transfer to GPQA and MMLU-Pro?** The aim is evaluation and transfer analysis, not a claim of a new state-of-the-art routing method.

Prior routing benchmarks make unified evaluation and simple baselines important. LLMRouterBench reports a benchmark and unified framework for evaluating LLM routing across many datasets and models [1]. RouterBench provides a framework for evaluating multi-LLM routing systems [2]. RouteLLM investigates routing using preference data and provides a related approach for comparing model-routing strategies [3]. Together, this prior work motivates explicit transfer protocols, transparent candidate pools, and strong baseline comparisons.

### Research questions

- **RQ1:** What is the router's performance on held-out GPQA and MMLU-Pro compared with a fixed strong model?
- **RQ2:** How sensitive are results to the source-validation seed, regularization selection, and fixed-model baseline selected using source validation?
- **RQ3:** Do the current experiments support reliable transfer or superiority over a strong fixed model?

## 2. Data and integrity checks

### 2.1 Source data

The source extraction audit reports 750 prompts across three domains.

| Source domain | Prompt count |
|---|---:|
| Coding | 253 |
| Creative writing | 250 |
| Mathematics | 247 |
| **Total** | **750** |

The extracted feature table contains 11 prompt features and records for 33 models. The local audit reports zero archive errors, prompt-text mismatches, ground-truth mismatches, missing model records, and score-alignment issues. These are checks reported by the project pipeline; they are not proof that every upstream dataset assumption is valid.

The benchmark archive SHA-256 recorded by the local audit is:

`b79f8cde1a6f029c2efa663a3a3b6f7748defb22341fe59f328cebef6648c8f1`

The hash identifies the inspected archive and supports reproducibility when the same archive is available. It does not independently establish the archive's completeness, license, or correctness.

### 2.2 Target benchmarks and candidate pools

The target evaluation comprises 198 GPQA prompts and 3,000 prompts from the `mmlupro/test_3000` split. The source extraction contains 33 models, while the reported Day 5 and Day 6 MMLU-Pro configurations use 13 candidate models. The Day 4 source-only configuration reports 33 source candidate models.

These counts describe different stages of the experimental pipeline and should not be interpreted as interchangeable candidate pools. The final reproducibility package must identify the exact candidate-model intersection used in each experiment, list the retained model names, and document any eligibility rules involving the availability of compatible source and target records.

The reported evaluation uses benchmark-provided scores. Its results are conditional on the selected benchmark release, retained prompts, available model outputs, candidate pool, and score conventions. The precise prompt-filtering and candidate-intersection procedures must be traceable to the corresponding experiment scripts, configuration files, and audit artifacts.

The terms *score* and *accuracy* are not automatically interchangeable. This manuscript uses *mean score* where the underlying metric semantics have not yet been independently confirmed. The final version should use *accuracy* only if the source records and evaluation scripts establish that the reported values represent correctness proportions under a consistent scoring definition.

### 2.3 Provenance and license caveat

The upstream benchmark repository is [LLMRouterBench](https://github.com/ynulihao/LLMRouterBench), and its associated paper appears in Findings of ACL 2026 [1].

The project's local provenance note reports that a maintainer described the repository source as intended to be MIT-licensed and the archive as usable for non-commercial academic research and reproduction. However, the formal license documentation and terms governing underlying datasets and providers were not fully confirmed in the local audit.

This does not establish blanket permission to redistribute the archive or every underlying record. Before public release, verify the current upstream license, release documentation, and applicable dataset and provider terms. Do not commit or redistribute the raw archive, restricted records, or other material whose redistribution rights remain unclear.

## 3. Method

### 3.1 Prompt-feature router

The router extracts 11 features from each prompt:

1. Character count.
2. Word count.
3. Line count.
4. Digit count.
5. Question-mark count.
6. Exclamation-mark count.
7. Code-symbol count.
8. Code-fence presence.
9. URL presence.
10. Equation-symbol presence.
11. Question-word presence.

Word counts use a regular-expression tokenizer. Binary indicators capture the presence of code fences, URL patterns, equation symbols, and selected question words. The implementation defines code symbols using occurrences of `{}`, `[]`, parentheses, semicolons, and angle brackets. Equation-symbol presence is detected through a regular expression covering selected arithmetic and equation-related symbols. The question-word indicator checks for selected terms, including “what,” “why,” “how,” “when,” “where,” “which,” “who,” “explain,” and “compare,” without regard to letter case.

The implementation trains a separate pipeline for each candidate model, comprising `StandardScaler` followed by Ridge regression. Each regressor predicts the candidate model's benchmark-provided score from the prompt features. The router selects the candidate with the highest predicted score.

The regularization parameter is selected from the candidate set `{0.1, 1, 10, 100}` using equal-weight average validation utility across the three source domains: ArenaHard coding, creative writing, and mathematics. The primary configuration uses seed 2026 and a validation fraction of 20% within each source domain. If validation utilities tie, the implementation prefers the larger alpha. After selecting alpha, the final per-model regressors are refitted using the complete source feature-and-score table.

Target scores are not used for source fitting or for selecting the regularization parameter in the documented source-only protocol. The final artifact audit should confirm that this separation holds for each reported experiment and that target outcomes were used only for evaluation.

The model-selection operation uses `argmax` over the predicted scores. In an exact prediction tie, this operation selects the first candidate in the model ordering supplied to it. The final implementation record should preserve the candidate ordering because it can affect tie resolution.

### 3.2 Baselines

Two comparisons must remain separate.

1. **Fixed strong baseline:** Gemini 2.5 Pro, used as a stable reference across target evaluations.
2. **Source-validation-selected baseline:** a candidate model selected using source-validation data only. Its identity can change with the validation split and it can be weaker than Gemini 2.5 Pro.

The selected-baseline comparison is informative about whether the router improves on a model chosen by the source-validation procedure. It is not interchangeable with the fixed-strong-baseline comparison. A gain against a validation-selected baseline does not establish that the router beats the strongest fixed model.

For reproducibility, each experiment should report the candidate pool, baseline-selection rule, selected baseline, validation utility, and seed. Any comparison across different candidate pools should be explicitly identified rather than treated as a like-for-like experiment.

### 3.3 Evaluation and uncertainty

Performance differences are computed as the router's prompt-level score minus the comparison baseline's score on the same target prompts. Positive differences favor the router; negative differences favor the baseline.

Confidence intervals are reported as percentile intervals obtained by resampling target prompts with replacement and calculating the mean paired difference for each bootstrap sample. The primary Day 4 evaluation uses 10,000 resamples with random seed 2026. The repeated source-validation analyses in Days 7 and 8 use 2,000 bootstrap resamples per comparison, with bootstrap seeds derived from each validation seed by adding 50,000.

Positive paired differences count as router wins, negative differences as losses, and exact zero differences as ties. Candidate selection by `argmax` is distinct from these post-evaluation win/tie/loss counts: the former selects a model based on predictions, whereas the latter summarizes observed paired score differences.

These intervals quantify uncertainty from resampling the observed target prompts under the evaluated setup. They do not capture variability across new target datasets, benchmark versions, model releases, or changes in candidate eligibility. Repeated source-validation seeds reuse the same target prompts and therefore represent sensitivity analyses rather than independent replications.

The final submission should verify that the interval endpoints in the manuscript exactly match the archived result files and the scripts that generated them. Bootstrap intervals should not be interpreted as evidence of broad transfer beyond the evaluated prompts.

## 4. Results

### 4.1 Held-out transfer against Gemini 2.5 Pro

The current reported results are summarized below. Values are presented as mean scores pending final confirmation of metric semantics.

| Target | Prompts | Router mean score | Gemini 2.5 Pro mean score | Difference (router − Gemini) | Reported 95% interval |
|---|---:|---:|---:|---:|---:|
| GPQA | 198 | 0.8182 | 0.8485 | −0.0303 | [−0.0707, +0.0101] |
| MMLU-Pro `test_3000` | 3,000 | 0.8387 | 0.8567 | −0.0180 | [−0.0250, −0.0113] |

For GPQA, the router is 3.03 percentage points below Gemini 2.5 Pro. The reported interval includes zero, so this result does not establish a statistically clear difference under the stated prompt-bootstrap procedure.

For MMLU-Pro, the router is 1.80 percentage points below Gemini 2.5 Pro. The reported interval is entirely negative, indicating lower router scores on the evaluated prompts under this procedure.

Taken together, these results do not support a claim of router superiority over the fixed Gemini baseline on either target benchmark.

### 4.2 Source-validation-selected baseline

On MMLU-Pro with validation seed 2026, the selected baseline is Qwen3 Thinking (`qwen3-235b-a22b-thinking-2507`). Its reported mean score is 0.7947. The router's reported mean score is 0.8387, yielding a difference of +0.0440, or +4.40 percentage points, with a reported 95% interval of [+0.0330, +0.0550].

This is not evidence that the router beats the strongest fixed model. Gemini 2.5 Pro scores 0.8567 on the same target prompts, above both the router and the selected Qwen3 Thinking baseline.

The result illustrates why baseline-selection protocols matter. A router can exceed a source-validation-selected model while still underperforming a strong fixed reference. The two comparisons answer different research questions and must be reported separately.

### 4.3 Repeated source-validation splits

Across validation seeds 2026–2035, the reported MMLU-Pro baseline-selection counts are:

| Selected baseline | Number of splits |
|---|---:|
| Gemini 2.5 Pro | 6 |
| Qwen3 Thinking | 2 |
| Intern-S1 | 1 |
| Kimi K2 | 1 |
| **Total** | **10** |

The mean router-minus-selected-baseline difference is reported as +0.35 percentage points, with a range from −1.83 to +4.40 percentage points. Against Gemini 2.5 Pro, the mean difference is approximately −1.80 percentage points.

For GPQA, the reported baseline-selection counts are the same. The mean router-minus-selected-baseline difference is reported as +1.21 percentage points, with a range from −3.03 to +16.16 percentage points. Against Gemini 2.5 Pro, the mean difference is approximately −2.78 percentage points.

Large positive differences occur on seeds where weaker baselines were selected and should not be interpreted as broad router superiority. The comparison against the fixed Gemini baseline remains negative on average for both target benchmarks.

Because the target prompts are reused across seeds, these summaries measure sensitivity to source validation and baseline selection. They are not independent replications across target datasets. The reported means, ranges, and selection frequencies should be checked against the complete Day 7 and Day 8 CSV artifacts before submission.

## 5. Discussion

The current evidence does not show that the router improves on Gemini 2.5 Pro in either target benchmark. It underperforms by 3.03 percentage points on GPQA and 1.80 percentage points on MMLU-Pro. The reported GPQA interval includes zero, while the reported MMLU-Pro interval is entirely negative.

The selected-baseline results illustrate why baseline policy matters. A router may exceed a model chosen by source validation while still underperforming a strong fixed reference. Both comparisons are useful, but they answer different questions. The fixed baseline assesses the router against a stable reference; the selected baseline assesses the effect of a particular source-validation selection procedure.

The repeated-split analyses further demonstrate that the selected baseline is sensitive to the validation split. The observed range of router-minus-selected-baseline differences is wide, especially on GPQA. Since the target prompts are held constant across these runs, this variation should be interpreted as sensitivity to the source-validation and baseline-selection procedure rather than independent evidence of transfer across new datasets.

The defensible contribution at this stage is a structured empirical evaluation of cross-benchmark transfer and baseline sensitivity for a lightweight prompt-feature router on two target benchmarks. The results do not establish algorithmic novelty, robust generalization across a broad benchmark suite, cost savings, or latency benefits. Cost and latency claims should remain excluded until their metric definitions, units, and comparability have been independently validated.

The study is also limited by the candidate pool, the available recorded model outputs, and the benchmark-specific scoring conventions. Any broader claim requires additional target datasets, transparent candidate eligibility, and comparisons against relevant published routing methods under a common evaluation protocol.

## 6. Limitations

1. **Limited target coverage:** Only GPQA and one MMLU-Pro test split are reported. The findings do not establish transfer to other benchmark families or deployment settings.

2. **Baseline dependence:** Conclusions differ between Gemini 2.5 Pro and a source-validation-selected model. A positive difference against a weaker selected baseline should not be treated as superiority over a strong fixed model.

3. **Repeated target reuse:** The ten source-validation seeds share the same target prompts. They are sensitivity analyses, not independent replications across target datasets.

4. **Candidate-pool differences:** The source extraction reports 33 models, whereas the MMLU-Pro configurations report 13 candidates. The final release must document the exact candidate intersection and eligibility rule for each experiment.

5. **Uncertainty scope:** Prompt-bootstrap intervals condition on the observed target prompts and do not quantify dataset-level transfer uncertainty, future model changes, or benchmark-version variation.

6. **Metric provenance:** Reported values are described as mean scores until the source records and evaluation scripts confirm the metric semantics. Cost and latency are excluded until definitions, units, and comparability are validated.

7. **Implementation transparency:** The router uses 11 prompt-level features, standardized Ridge regression, source-domain validation to select regularization, and maximum predicted score to select a candidate model. The primary configuration uses seed 2026, 20% validation data per source domain, and alpha candidates of 0.1, 1, 10, and 100. Reproducibility depends on retaining the corresponding scripts, feature-extraction code, candidate-model lists, configuration files, and compatible benchmark records.

8. **Result provenance:** The manuscript's reported numbers must be cross-checked against the exact generated result files and their generating scripts. The existence of a current script does not, by itself, prove that it generated an earlier result unless the script version or hash was recorded at experiment time.

9. **Novelty not established:** A complete related-work review and direct comparisons with relevant published baselines are required before making a novelty claim. This study should be positioned as an empirical transfer and evaluation study unless stronger evidence is obtained.

10. **Licensing and redistribution:** The source archive and underlying dataset/provider terms require final verification before redistribution. Raw archives or restricted records should not be included in the public repository unless the applicable permissions are clear.

## 7. Conclusion

The current experiments evaluate a lightweight prompt-feature router trained on ArenaHard coding, creative-writing, and mathematics records and tested on GPQA and MMLU-Pro. The reported results do not establish superiority over the fixed Gemini 2.5 Pro baseline. The router scores below Gemini on both GPQA and MMLU-Pro, with the reported MMLU-Pro interval entirely negative and the GPQA interval including zero.

Apparent gains against a source-validation-selected baseline depend on which baseline is selected and must be interpreted separately. Repeated source-validation runs reveal sensitivity to baseline selection, but reuse the same target prompts and do not constitute independent replications.

The appropriate conclusion is a cautious empirical study of transfer and evaluation methodology, not a state-of-the-art or novel-algorithm claim. Before submission, the reported scores, confidence intervals, candidate pools, score semantics, and provenance documentation should be reconciled with the committed experiment artifacts.

## References

[1] Hao Li, Yiqun Zhang, Zhaoyan Guo, Chenxu Wang, Shengji Tang, Qiaosheng Zhang, Yang Chen, Biqing Qi, Peng Ye, Lei Bai, Zhen Wang, and Shuyue Hu. “LLMRouterBench: A Massive Benchmark and Unified Framework for LLM Routing.” *Findings of the Association for Computational Linguistics: ACL 2026*, pp. 37733–37754, 2026. [https://aclanthology.org/2026.findings-acl.1881/](https://aclanthology.org/2026.findings-acl.1881/). DOI: [10.18653/v1/2026.findings-acl.1881](https://doi.org/10.18653/v1/2026.findings-acl.1881).

[2] Qitian Jason Hu, Jacob Bieker, Xiuyu Li, Nan Jiang, Benjamin Keigwin, Gaurav Ranganath, Kurt Keutzer, and Shriyash Kaustubh Upadhyay. “RouterBench: A Benchmark for Multi-LLM Routing System.” arXiv:2403.12031, 2024. [https://arxiv.org/abs/2403.12031](https://arxiv.org/abs/2403.12031).

[3] Isaac Ong, Amjad Almahairi, Vincent Wu, Wei-Lin Chiang, Tianhao Wu, Joseph E. Gonzalez, M. Waleed Kadous, and Ion Stoica. “RouteLLM: Learning to Route LLMs with Preference Data.” *International Conference on Learning Representations (ICLR)*, 2025. [Official proceedings page](https://proceedings.iclr.cc/paper_files/paper/2025/hash/5503a7c69d48a2f86fc00b3dc09de686-Abstract-Conference.html). Project repository: [https://github.com/lm-sys/RouteLLM](https://github.com/lm-sys/RouteLLM).
