# Related Work and Claim Boundaries

## Published context

### LLMRouterBench (Findings ACL 2026)
Li et al. describe a unified benchmark with over 400,000 instances across 21 datasets and 33 models, evaluate 10 routing baselines, and report that methods can perform similarly under unified evaluation and may not reliably outperform simple baselines. This motivates strong fixed-model baselines and cautious claims.
Source: https://aclanthology.org/2026.findings-acl.1881/

### RouterBench (2024)
Hu et al. introduce a benchmark and evaluation framework for multi-LLM routing, with over 405,000 inference outcomes, and discuss performance/cost trade-offs.
Source: https://arxiv.org/abs/2403.12031

### RouteLLM
Ong et al. present preference-data-based routing methods and an open-source framework emphasizing quality/cost trade-offs.
Project: https://github.com/lm-sys/RouteLLM
Overview: https://sky.cs.berkeley.edu/project/routellm/

## Implication for this study
LLM routing and benchmark-based router comparison are established research areas. Applying a lightweight router to held-out benchmarks can be useful as a transfer/reproducibility analysis, but the experiment alone does not establish algorithmic novelty.

## Defensible claims from current run summaries
- The pipeline reports an integrity audit over 750 source prompts, 33 models, and 11 features.
- The router was evaluated on GPQA (198 prompts) and MMLU-Pro test_3000 (3,000 prompts).
- In current reported runs, the router scored below Gemini 2.5 Pro on both targets.
- Source-validation-selected baseline results vary with the selected baseline.
- Repeated source-validation seeds reused the same target prompts and are sensitivity analyses, not independent replications.

## Claims to avoid without new evidence
- “The router outperforms the best model.”
- “The method is state-of-the-art.”
- “The router generalizes broadly to unseen tasks.”
- “The router reduces cost or latency.”
- “The method is novel” without a sharper contribution and direct related-work comparison.

## Recommended scientific upgrade
Define a sharper transfer question and conduct a clean evaluation with a frozen source-only selection protocol, explicit fixed-strong and source-selected baselines, a target set untouched by feature/threshold choices, an additional independent target benchmark, paired prompt-level uncertainty, and transparent failure analysis.
