# Day 16 — source-table schema audit and data-preparation gate

## Inspected local artifact

The user inspected `day1_audit/prompt_feature_score_table.csv` locally on 2026-10-31.

Observed shape: **750 rows × 47 columns**.

Columns:
- 3 identifiers/provenance fields: `dataset`, `index`, `prompt_text_source`
- 11 prompt-derived features: `char_count`, `word_count`, `line_count`, `digit_count`, `question_mark_count`, `exclamation_count`, `code_symbol_count`, `contains_code_fence`, `contains_url`, `contains_equation_symbol`, `contains_question_word`
- 34 model-score columns.

Source-domain counts:
- `arenahard_coding`: 253
- `arenahard_creative_writing`: 250
- `arenahard_math`: 247

The inspected CSV had zero missing values overall. The 13-model study pool is represented among the 34 score columns:
`claude-sonnet-4`, `deepseek-r1-0528`, `deepseek-v3.1-terminus`, `deepseek-v3-0324`, `gemini-2.5-flash`, `gemini-2.5-pro`, `glm-4.6`, `gpt-5`, `gpt-5-chat`, `intern-s1`, `kimi-k2-0905`, `qwen3-235b-a22b-2507`, `qwen3-235b-a22b-thinking-2507`.

## Critical limitation

The sample value in `prompt_text_source` is the literal string:

`origin_query when available, otherwise prompt`

It is a provenance description, not the actual query text. Therefore, the feature-score CSV is sufficient for the existing tabular Ridge analysis and score-coverage checks, but **is not sufficient by itself to create Avengers-Pro JSONL inputs**. Avengers-Pro requires the actual query string to generate embeddings.

Do not:
- pass the provenance placeholder as a query;
- reconstruct prompts from the 11 aggregate features;
- silently use a different benchmark or model pool;
- treat the CSV's feature values as embeddings.

## Upstream input contract confirmed

At upstream revision `0b81ba3053fbb74828382690a883849e2443e2d8`, `baselines/adaptors/avengerspro_adaptor.py` documents JSONL rows with:
- `query`: actual prompt text;
- `dataset`: dataset identifier;
- `index`: record index;
- `records`: model-name-to-score mapping;
- `usages`: per-model usage metadata.

The router's loader consumes `query` and `records`. The upstream adaptor groups model records by dataset and prompt, preserving prompt-level grouping. Its default split ratio is 0.8; the study's proposed 0.7 source-train split is a declared protocol variation and must not be described as the upstream default.

## Existing Day 16 preflight status

`day16_avengerspro_split_preflight.py` validates already-prepared JSONL train/test files. It does not convert the feature-score CSV into JSONL and does not retrieve prompt text. Its 0.7 default is a study-specific setting. It must only be run after valid JSONL files have been created from verified original prompt records.

The local checkout inspection found:
- `repos/LLMRouterBench/results` contains only `download.md`;
- `baselines/AvengersPro/results` contains only `.gitkeep`;
- no generated Avengers-Pro train/test artifacts were present in those locations.

## Next required gate

Locate the original archived benchmark records that contain the actual prompt strings and the corresponding selected 13 model scores. Match them to the audited source table using dataset identifier and record index, then verify:
1. one unique prompt per source key;
2. exact prompt-text consistency across model records;
3. exactly the selected 13 model scores per prompt, with no missing or duplicate model records;
4. score equality against the audited CSV for every matched dataset/index/model;
5. no source/target prompt leakage after the split.

Only after these checks pass should an offline adapter write Avengers-Pro JSONL. Target datasets must remain test-only, and their scores must not be used for embedding, clustering, ranking, or route selection. Keep target-derived best-model figures labelled as oracle comparisons.

## Status

**Source score table: structurally suitable. Actual prompt text: not yet located in the inspected table. Avengers-Pro JSONL preparation: blocked pending verified prompt recovery. No router run or embedding/API request has been made.**
