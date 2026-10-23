# Day 4 — Held-Out GPQA Transfer Evaluation

## Objective
Evaluate whether a prompt-feature-based model router selected using
source-domain data transfers to a held-out GPQA benchmark better than
a single global model selected on the source domains.

## Source data and selection
- Source domains: ArenaHard coding, creative writing, and mathematics.
- Source prompts: 750.
- Candidate models: 33.
- Prompt features: 11 lexical and structural features.
- Alpha candidates: 0.1, 1.0, 10.0, and 100.0.
- Selected alpha: 10.0, chosen using source validation utility.
- Global baseline: gemini-2.5-pro, selected using source-domain performance.

## Held-out evaluation
- Benchmark: GPQA.
- Evaluation prompts: 198.
- Models represented in the audited GPQA pool: 38.
- Primary comparison pool: the 33 models shared with the source candidate pool.
- Evaluation scores: benchmark-provided binary scores.

## Results
- Router mean score: 0.818182 (81.82%).
- Global baseline mean score: 0.848485 (84.85%).
- Paired difference (router minus baseline): -0.030303
  (-3.03 percentage points).
- 95% prompt-bootstrap percentile confidence interval:
  [-0.070707, 0.010101] (-7.07 to +1.01 percentage points).
- Prompt wins / ties / losses: 6 / 180 / 12.
- Bootstrap resamples: 10,000.
- Bootstrap seed: 2026.

## Router selections on GPQA
- qwen3-235b-a22b-thinking-2507: 126 prompts.
- gemini-2.5-pro: 71 prompts.
- gpt-5-chat: 1 prompt.

## Interpretation
The router did not outperform the source-selected global baseline on
this GPQA sample. The point estimate favors the global baseline, while
the confidence interval includes zero. These results do not establish
a reliable performance difference, improved transfer, broad-domain
generalization, or a novel contribution.

The result is an initial held-out transfer evaluation. It should be
reported as inconclusive with respect to a reliable difference, not as
evidence that feature-based routing is superior.

## Limitations
1. The held-out evaluation contains 198 prompts from one target benchmark.
2. Prompt-level bootstrap intervals do not account for every possible
   source of uncertainty, including model and benchmark selection.
3. The feature set is limited to 11 lexical and structural features.
4. Benchmark score semantics and the provenance and licensing of the
   source archive require continued documentation.
5. One held-out transfer result is insufficient to establish broad
   generalization or publication-level novelty.

## Reproducibility artifacts
- day4_gpqa_transfer.py
- DAY4_GPQA_TRANSFER_RESULTS.txt
- DAY4_GPQA_PER_PROMPT_RESULTS.csv
- DAY4_GPQA_ROUTER_CONFIG.txt
- DAY4_GPQA_RUN_LOG.txt

## Day 4 conclusion
The held-out transfer run completed successfully. The observed router
score was lower than the global baseline by 3.03 percentage points.
No reliable router advantage was established. Further research should
focus on rigorous baselines, leakage prevention, uncertainty analysis,
and independent evaluation rather than claiming superiority from this
pilot.
