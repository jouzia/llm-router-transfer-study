# Evaluating Cross-Benchmark Transfer of a Lightweight LLM Router

**Research type:** Empirical evaluation and reproducibility study  
**Status:** Experimental results available; broader generalization and algorithmic novelty not established

## Overview

Large language model (LLM) routing selects a model for a given prompt from a pool of candidate models. A router may use prompt characteristics to make this decision, with the goal of balancing response quality, model capability, and inference cost.

This project investigates whether a lightweight router built from lexical prompt features can transfer across benchmark families, and how its performance compares with fixed-model baselines.

The study evaluates a Ridge-based prompt-feature router on source benchmark data and examines transfer to GPQA and MMLU-Pro. It also investigates how the choice of fixed-model baseline changes the interpretation of routing performance.

The central focus is **empirical transfer, baseline selection, and evaluation reliability**, rather than claiming a novel routing algorithm.

## Research Question

How reliably does a lightweight lexical-feature router transfer across benchmark families, and which evaluation choices explain its performance gap relative to fixed-model baselines?

### Research objectives

- Evaluate a lexical-feature Ridge router on held-out benchmark prompts.
- Compare transfer performance against a strong fixed-model baseline.
- Examine the sensitivity of comparisons to source-validation baseline selection.
- Quantify uncertainty using paired differences and bootstrap confidence intervals.
- Assess whether the available evidence supports claims of reliable transfer or generalization.

## Methodology

### Router

The experimental router uses lexical features extracted from prompts and a Ridge-based prediction approach to select a model from a candidate pool.

The router is evaluated against fixed-model baselines. The experiments distinguish comparisons against a globally selected model, such as Gemini 2.5 Pro, from comparisons against a model selected using source-validation data.

### Evaluation protocol

The experiments include:

1. **Source-data audit:** Inspect benchmark coverage, model pools, record schemas, score distributions, and metric consistency.
2. **Initial transfer evaluation:** Evaluate on GPQA and MMLU-Pro target prompts.
3. **Baseline analysis:** Compare the router with a fixed global baseline and a validation-selected baseline.
4. **Repeated source-validation splits:** Repeat baseline selection to investigate the sensitivity of results to the source-validation split.
5. **Provenance and prior-work review:** Audit data provenance, licensing caveats, related work, and the strength of potential research claims.

Repeated source-validation splits reuse the same target prompts. They therefore measure sensitivity to the selection procedure and should not be interpreted as independent replications across target datasets.

## Experimental Results

The following results summarize the completed transfer experiments.

| Experiment | Router accuracy | Baseline accuracy | Difference |
|---|---:|---:|---:|
| GPQA transfer | 81.82% | 84.85% (Gemini 2.5 Pro) | −3.03 percentage points |
| MMLU-Pro transfer | 83.87% | 85.67% (Gemini 2.5 Pro) | −1.80 percentage points |
| MMLU-Pro, validation-selected baseline | 83.87% | 79.47% (Qwen3 Thinking) | +4.40 percentage points |

### GPQA

The router achieved a mean score of 0.8182, compared with 0.8485 for Gemini 2.5 Pro.

- Paired difference: −3.03 percentage points.
- 95% bootstrap confidence interval: −7.07 to +1.01 percentage points.
- Interpretation: The experiment does not establish superiority over the fixed Gemini baseline.

### MMLU-Pro

The router achieved a mean score of 0.8387, compared with 0.8567 for Gemini 2.5 Pro.

- Paired difference: −1.80 percentage points.
- 95% bootstrap confidence interval: −2.50 to −1.13 percentage points.
- Interpretation: The router underperformed Gemini 2.5 Pro on this evaluation.

Against the validation-selected Qwen3 Thinking baseline, the router scored 4.40 percentage points higher, with a reported 95% confidence interval of +3.3 to +5.5 percentage points.

This result illustrates why baseline-selection protocols matter: the conclusion changes depending on which fixed model is used for comparison.

### Repeated baseline-selection experiments

Across ten source-validation splits on the same target prompts:

- **MMLU-Pro:** The mean difference against the selected baseline was +0.35 percentage points, with a range from −1.83 to +4.40 points.
- **GPQA:** The mean difference against the selected baseline was +1.21 percentage points, with a range from −3.03 to +16.16 points.
- Gemini 2.5 Pro was selected as the baseline in six of the ten splits.

The results demonstrate sensitivity to baseline selection. Because the target prompts are reused across splits, these figures do not establish independent cross-dataset replication.

## Main Findings

1. **Transfer performance depends on the comparison baseline.** A router may outperform a source-validation-selected model in a particular experiment while underperforming a stronger fixed baseline.
2. **The router did not outperform Gemini 2.5 Pro on either reported target benchmark.** The observed differences were −3.03 percentage points on GPQA and −1.80 percentage points on MMLU-Pro.
3. **Baseline selection is unstable across source-validation splits.** The selected fixed model varies, affecting the measured routing advantage.
4. **Broad generalization remains unestablished.** The completed experiments do not demonstrate reliable superiority across independent target datasets.
5. **Algorithmic novelty has not been established.** The current evidence supports an empirical evaluation of transfer behavior and baseline sensitivity, not a claim of a new state-of-the-art routing method.

## Repository Structure

The repository contains experiment scripts, audit utilities, and research reports.

```text
llm-router-transfer-study/
├── day1_audit/
│   ├── DAY10_PRIOR_ART_DECISION.md
│   ├── DAY11_FINAL_RESEARCH_ASSESSMENT.md
│   ├── DAY12_DATA_PROVENANCE_AND_LICENSE.md
│   └── ...
├── *.py
├── .gitignore
└── README.md
```

The exact set of tracked files may evolve as the reproducibility package is refined. Experiment outputs and raw benchmark records are not assumed to be part of the public repository.

## Reproducibility

### Environment

From the repository root, install the pinned dependencies in a virtual environment:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Required inputs

The Day 4–6 transfer scripts require the benchmark archive, feature extractor, and prepared source tables. Obtain source data separately under the applicable terms. Do not commit the raw archive or potentially restricted prompt-level records.

Verify the local archive with:

```powershell
Get-FileHash .\bench-release.tar.gz -Algorithm SHA256
```

Expected SHA-256:

`B79F8CDE1A6F029C2EFA663A3A3B6F7748DEFB22341FE59F328CEBEF6648C8F1`

### Run the transfer experiments

Run from the repository root after preparing the required inputs:

```powershell
.\.venv\Scripts\python.exe .\day1_audit\day4_gpqa_transfer.py
.\.venv\Scripts\python.exe .\day1_audit\day5_mmlupro_transfer.py
.\.venv\Scripts\python.exe .\day1_audit\day6_fair_baseline_transfer.py
```

Inspect the generated reports, configurations, and per-prompt outputs under `day1_audit/`.

### Reproducibility status and limitations

Local runs and checks of reported means against per-prompt outputs do not establish complete independent reproduction of every experiment. Confirm that the final Day 4 script version has been rerun before treating its saved result as verified against the corrected feature-column ordering.

Repeated validation splits reuse the same target prompts and are not independent target replications. The results do not establish broad cross-benchmark generalization, superiority to Gemini 2.5 Pro, or a novel routing contribution.

## Data Provenance and Licensing

The project uses benchmark-derived records associated with LLMRouterBench.

The repository includes a provenance and licensing assessment. The maintainer indicated in GitHub issue [#5](https://github.com/ynulihao/LLMRouterBench/issues/5) that the MIT license was intended for the top-level source and discussed non-commercial academic research and reproduction. The scope of the formal licensing documentation has not been conclusively verified here.

Consequently:

- Do not interpret this discussion as blanket permission for commercial use.
- Do not assume raw benchmark archives, prompts, ground-truth answers, or model outputs can be redistributed without restriction.
- Review the upstream repository's current license and data terms before reuse or redistribution.
- Prefer reporting derived aggregate results where permitted, and preserve appropriate attribution.

## Limitations

- The evaluation covers a limited set of target benchmark families.
- Repeated validation splits reuse target prompts and are not independent target replications.
- Baseline selection changes the apparent performance advantage.
- The experiments do not establish superiority over the strongest fixed-model baseline.
- Cost and latency comparisons are excluded from the conclusions because metric semantics and units require further validation.
- Broader generalization and algorithmic novelty remain open questions.
- Complete end-to-end reproducibility and the redistribution rights for all underlying benchmark records have not been established.

## Conclusion

This study evaluates the transfer behavior of a lightweight lexical-feature LLM router and examines the effect of fixed-model baseline selection.

The completed results show that the router underperformed Gemini 2.5 Pro on both GPQA and MMLU-Pro, while comparisons against validation-selected baselines varied across experiments. These findings highlight the importance of baseline selection, paired evaluation, uncertainty quantification, and careful interpretation of repeated-split experiments.

The current contribution is best characterized as an **empirical transfer and evaluation study**. Establishing a novel routing algorithm, reliable generalization, or consistent superiority over strong fixed-model baselines requires further evidence.

## Citation

If you use or build on this work, cite the repository:

**Shaik Jouzia Afreen H.** *Evaluating Cross-Benchmark Transfer of a Lightweight LLM Router.* GitHub repository: https://github.com/jouzia/llm-router-transfer-study

*This citation identifies the project repository; it is not a substitute for a formal publication citation.*

## Acknowledgements

This work builds on publicly available benchmark resources and research on LLM routing and model selection. Please consult the relevant upstream sources and their license terms before reusing benchmark data.
