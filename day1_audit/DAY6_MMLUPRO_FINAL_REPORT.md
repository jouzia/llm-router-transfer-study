# Day 6 — MMLU-Pro Held-Out Transfer Results

## Protocol

- Source: 750 ArenaHard rows across coding, creative writing, and math.
- Features: 11 lexical/structural prompt features.
- Candidate pool: 13 models shared between source data and MMLU-Pro `test_3000`.
- Alpha selected from [0.1, 1.0, 10.0, 100.0] using a domain-stratified 20% source validation split (seed 2026).
- Final router refit on all source rows after alpha selection.
- Target: 3,000 aligned MMLU-Pro prompts; target scores are evaluation-only.
- Global baseline selected by equal-weight mean performance across the source validation domains: `qwen3-235b-a22b-thinking-2507`.

## Results

| Metric | Result |
|---|---:|
| Router mean score | 83.8667% |
| Global baseline mean score | 79.4667% |
| Paired difference (router − baseline) | +4.400 percentage points |
| 95% prompt-bootstrap percentile interval | [+3.300, +5.500] percentage points |
| Router wins / ties / losses | 212 / 2708 / 80 |
| Selected alpha | 10.0 |

## Interpretation

This is one held-out benchmark transfer result, not evidence by itself of broad generalization or novelty. If the interval contains zero, the observed difference is not statistically distinguishable from zero under this prompt-bootstrap analysis. If the interval excludes zero, that is still limited to the benchmark and evaluation protocol used here.

Both the baseline model and Ridge alpha are selected using the same source-only validation split. The router is refit on all source rows after alpha selection. Reusing the validation split for both choices can still cause model-selection optimism; this result is conditional on the fixed split. The bootstrap does not capture variability from training choices, model versions, or benchmark construction. Cost and latency comparisons are omitted pending metric-semantics verification.

## Router model selection frequencies

- `claude-sonnet-4`: 0 prompts
- `deepseek-r1-0528`: 0 prompts
- `deepseek-v3.1-terminus`: 0 prompts
- `deepseek-v3-0324`: 0 prompts
- `gemini-2.5-flash`: 0 prompts
- `gemini-2.5-pro`: 2186 prompts
- `glm-4.6`: 0 prompts
- `gpt-5`: 0 prompts
- `gpt-5-chat`: 2 prompts
- `intern-s1`: 0 prompts
- `kimi-k2-0905`: 0 prompts
- `qwen3-235b-a22b-2507`: 0 prompts
- `qwen3-235b-a22b-thinking-2507`: 812 prompts

## Artifacts

- `DAY6_MMLUPRO_TRANSFER_RESULTS.txt`
- `DAY6_MMLUPRO_PER_PROMPT_RESULTS.csv`
- `DAY6_MMLUPRO_ROUTER_CONFIG.txt`
- `DAY6_MMLUPRO_FINAL_REPORT.md`
