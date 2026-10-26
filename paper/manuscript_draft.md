# Evaluating Cross-Benchmark Transfer of a Lightweight LLM Router

**Author:** Shaik Jouzia Afreen H.
**Status:** Manuscript draft; regenerate and cross-check results against committed artifacts before submission.
**Repository:** https://github.com/jouzia/llm-router-transfer-study

## Abstract

Large language model (LLM) routers select a model for each input, aiming to exploit complementary model strengths. A router that performs well on source tasks may not retain its advantage on a different benchmark. This study evaluates a lightweight prompt-feature router trained using records from three ArenaHard domains—coding, creative writing, and mathematics—and tests transfer to GPQA and MMLU-Pro. The source extraction audit reports 750 prompts, 33 models, 11 prompt features, and no detected prompt-text, ground-truth, record-availability, or score-alignment inconsistencies. In the current reported evaluation, the router achieves 81.82% on 198 GPQA prompts versus 84.85% for a fixed Gemini 2.5 Pro baseline (difference −3.03 percentage points; prompt-bootstrap 95% interval [−7.07, +1.01] points). On 3,000 MMLU-Pro test prompts, it achieves 83.87% versus 85.67% for Gemini 2.5 Pro (difference −1.80 points; reported interval [−2.50, −1.13] points). A source-validation-selected baseline can be weaker: on MMLU-Pro, the router exceeds the selected Qwen3 Thinking baseline by 4.40 points, but this does not establish superiority over the strongest fixed model. Repeated source-validation splits reuse the same target prompts and are sensitivity analyses, not independent replications. Current evidence supports a cautious empirical transfer study, but not a claim that the router outperforms the strongest fixed-model baseline or establishes a novel routing algorithm.

**Keywords:** large language models; model routing; cross-benchmark transfer; generalization; evaluation methodology; reproducibility

## 1. Introduction

LLM routing assigns each query to a model from a candidate pool. Its motivation is that different models may have complementary strengths, while routing may improve quality, cost, or latency relative to always using one model. However, source-domain performance does not guarantee transfer to a held-out benchmark, and conclusions can change depending on the fixed-model baseline.

This study asks: **how well does a lightweight prompt-feature router trained on ArenaHard coding, creative-writing, and mathematics records transfer to GPQA and MMLU-Pro?** The aim is evaluation and transfer analysis, not a claim of a new state-of-the-art routing method.

Prior routing benchmarks make unified evaluation and simple baselines important. LLMRouterBench reports a benchmark with over 400,000 instances across 21 datasets and 33 models, and finds that methods can perform similarly under unified evaluation and may not reliably outperform simple baselines [1]. RouterBench provides a broad framework for evaluating multi-LLM routing [2]. These findings motivate explicit transfer protocols and strong baseline comparisons.

### Research questions
- **RQ1:** What is router performance on held-out GPQA and MMLU-Pro compared with a fixed strong model?
- **RQ2:** How sensitive are results to source-validation seed, regularization selection, and the fixed-model baseline selected using source validation?
- **RQ3:** Do current experiments support reliable transfer or superiority over a strong fixed model?

## 2. Data and integrity checks

### 2.1 Source data

The source extraction audit reports 750 prompts across three domains:

| Source domain | Prompt count |
|---|---:|
| Coding | 253 |
| Creative writing | 250 |
| Mathematics | 247 |
| **Total** | **750** |

The extracted feature table contains 11 prompt features and records for 33 models. The audit reports zero archive errors, prompt-text mismatches, ground-truth mismatches, missing model records, and score-alignment issues. The benchmark archive SHA-256 recorded by the local audit is:

`b79f8cde1a6f029c2efa663a3a3b6f7748defb22341fe59f328cebef6648c8f1`

These are checks reported by the project pipeline; they are not proof that every upstream dataset assumption is valid.

### 2.2 Target benchmarks
- **GPQA:** 198 target prompts in the current evaluation.
- **MMLU-Pro:** 3,000 prompts from `mmlupro/test_3000`.

The final paper must document target split provenance, candidate-model intersection, prompt filtering, and score conventions directly from the scripts and generated configuration files.

### 2.3 Provenance and license caveat

The upstream benchmark repository is https://github.com/ynulihao/LLMRouterBench and its paper appears in Findings of ACL 2026 [1]. The project's local provenance note reports that a maintainer described the repository source as MIT-intended and the archive as usable for non-commercial academic research/reproduction, while formal documentation and underlying dataset/provider terms were not fully confirmed. This does not establish blanket permission to redistribute the archive or all underlying records. Before release, verify the current upstream license, release documentation, and terms for underlying datasets and providers. Do not commit or redistribute the raw archive or restricted records unless permission is clear.

## 3. Method

### 3.1 Router

The current implementation uses 11 extracted prompt-level features and a regularized lightweight router. The regularization parameter is selected from `{0.1, 1, 10, 100}` using source-domain validation. Day 4 and Day 5 runs report alpha `10.0` with validation seed `2026`. The final paper must specify the exact model class, feature definitions, scaling, label construction, training objective, tie handling, and candidate pool from the committed source code; these details should not be inferred from this summary alone.

### 3.2 Baselines

Two comparisons must remain separate:

1. **Fixed strong baseline:** Gemini 2.5 Pro, used as a stable reference.
2. **Source-validation-selected baseline:** the candidate model selected using source validation only. This can change with validation seed and can be weaker than Gemini 2.5 Pro.

The selected-baseline comparison is informative about whether the router improves on a model chosen by source validation. It is not interchangeable with the fixed-strong-baseline comparison.

### 3.3 Evaluation and uncertainty

The project reports prompt-level mean scores and paired prompt-bootstrap percentile confidence intervals. The final manuscript must document the number of bootstrap resamples, random seed, resampling unit, score pairing, treatment of ties, and whether intervals are for paired differences or separate means. Reported intervals condition on observed target prompts; they do not capture variation across new target datasets or future model releases.

Repeated source-validation splits use seeds 2026–2035 and reuse the same target prompts. They are **source-validation sensitivity analyses**, not ten independent test replications. No seed should be selected based on target outcomes.

## 4. Results

### 4.1 Held-out transfer against Gemini 2.5 Pro

| Target | Prompts | Router score | Gemini 2.5 Pro | Difference (router − Gemini) | Reported 95% interval |
|---|---:|---:|---:|---:|---:|
| GPQA | 198 | 0.8182 | 0.8485 | −0.0303 | [−0.0707, +0.0101] |
| MMLU-Pro test_3000 | 3,000 | 0.8387 | 0.8567 | −0.0180 | [−0.0250, −0.0113] |

For GPQA, the router is 3.03 percentage points below Gemini 2.5 Pro and the reported interval includes zero. For MMLU-Pro, the router is 1.80 percentage points below Gemini and the reported interval is entirely negative. These results do not support a superiority claim.

### 4.2 Source-validation-selected baseline

On MMLU-Pro with validation seed 2026, the selected baseline is Qwen3 Thinking, with reported mean score 0.7947. The router's reported score is 0.8387, a difference of +0.0440 (4.40 percentage points), with a reported 95% interval of [+0.0330, +0.0550].

This is not evidence that the router beats the strongest fixed model: Gemini 2.5 Pro scores 0.8567 on the same target prompts, above both the router and selected Qwen3 Thinking baseline. The baseline-selection rule must be described transparently.

### 4.3 Repeated source-validation splits

Across seeds 2026–2035, MMLU-Pro baseline-selection counts are reported as Gemini 2.5 Pro (6), Qwen3 Thinking (2), Intern-S1 (1), and Kimi K2 (1). The mean router-minus-selected-baseline difference is reported as +0.35 percentage points, ranging from −1.83 to +4.40 points. Against Gemini 2.5 Pro, the mean difference is approximately −1.80 points.

For GPQA, the reported baseline-selection counts are the same. The mean router-minus-selected-baseline difference is reported as +1.21 percentage points, ranging from −3.03 to +16.16 points. Against Gemini 2.5 Pro, the mean difference is approximately −2.78 points. Large positive differences occur on seeds where weaker baselines were selected and should not be interpreted as broad router superiority.

Because target prompts are reused across seeds, these summaries measure sensitivity to source validation and baseline selection. They are not independent replications.

## 5. Discussion

The current evidence does not show that the router improves on Gemini 2.5 Pro in either target benchmark. It underperforms by 3.03 percentage points on GPQA and 1.80 points on MMLU-Pro. The GPQA interval includes zero, while the MMLU-Pro interval reported by the current run is negative.

The selected-baseline results illustrate why baseline policy matters. A router may exceed a model chosen by source validation while still underperforming a strong fixed reference. Both comparisons are useful, but they answer different questions.

The defensible contribution at this stage is a reproducible evaluation of cross-benchmark transfer and baseline sensitivity for a lightweight prompt-feature router on two target benchmarks. Current evidence does not establish algorithmic novelty, robust generalization across a broad benchmark suite, cost savings, or latency benefits. Exclude cost and latency claims until metric semantics, units, and comparability are independently validated.

## 6. Limitations

1. **Limited target coverage:** only GPQA and one MMLU-Pro test split are reported.
2. **Baseline dependence:** conclusions differ between Gemini 2.5 Pro and a source-validation-selected model.
3. **Repeated target reuse:** ten source-validation seeds share target prompts and are not independent replications.
4. **Implementation transparency:** the final submission must document feature definitions, scaling, training target, model class, selection rule, and candidate pool from source code.
5. **Uncertainty scope:** prompt-bootstrap intervals condition on the observed target prompts and do not quantify dataset-level transfer uncertainty.
6. **Metric provenance:** cost and latency are excluded until definitions and units are validated.
7. **External validity:** results depend on benchmark release, candidate models, recorded outputs, and scoring conventions.
8. **Novelty not established:** a related-work review and direct comparison with published baselines are required before any novelty claim.
9. **Licensing:** source archive and underlying dataset/provider terms require final verification before redistribution.

## 7. Conclusion

The current experiments show that a lightweight prompt-feature router can be evaluated on two held-out benchmarks, but the reported results do not establish superiority over a strong fixed model. The router scores below Gemini 2.5 Pro on both GPQA and MMLU-Pro. Apparent gains against a source-validation-selected baseline depend on which baseline is selected and must be interpreted separately. The appropriate conclusion is a cautious transfer and evaluation study, not a state-of-the-art or novel-algorithm claim.

## References

[1] Hao Li, Yiqun Zhang, Zhaoyan Guo, Chenxu Wang, Shengji Tang, Qiaosheng Zhang, Yang Chen, Biqing Qi, Peng Ye, Lei Bai, Zhen Wang, and Shuyue Hu. “LLMRouterBench: A Massive Benchmark and Unified Framework for LLM Routing.” *Findings of the Association for Computational Linguistics: ACL 2026*, pp. 37733–37754, 2026. https://aclanthology.org/2026.findings-acl.1881/. DOI: 10.18653/v1/2026.findings-acl.1881.

[2] Qitian Jason Hu, Jacob Bieker, Xiuyu Li, Nan Jiang, Benjamin Keigwin, Gaurav Ranganath, Kurt Keutzer, and Shriyash Kaustubh Upadhyay. “RouterBench: A Benchmark for Multi-LLM Routing System.” arXiv:2403.12031, 2024. https://arxiv.org/abs/2403.12031.

[3] Isaac Ong, Amjad Almahairi, Vincent Wu, Wei-Lin Chiang, Tianhao Wu, Joseph E. Gonzalez, M. Waleed Kadous, and Ion Stoica. “RouteLLM: Learning to Route LLMs with Preference Data.” Project: https://github.com/lm-sys/RouteLLM. Verify the final bibliographic version and publication details before submission.
