# Day 16 — Avengers-Pro input construction: schema and protocol gate

## Upstream contract inspected

At upstream LLMRouterBench revision `0b81ba3053fbb74828382690a883849e2443e2d8`, `AvengersProAdaptor` writes JSONL records with:
- `query`: prompt text;
- `dataset`: dataset identifier;
- `index`: record index;
- `records`: model-name-to-score mapping;
- `usages`: per-model `completion_tokens`, `cost`, and `prompt_tokens`.

The router's `SimpleClusterRouter._validate_data_item` actually requires only a non-empty `query` and a non-empty numeric `records` mapping. The adaptor's standard output nevertheless includes `usages`; the study builder retains them from archive records when available.

The upstream loader splits by dataset, then by prompt, keeps all model scores for each prompt together, uses `int(n_prompts * train_ratio)`, and sends designated OOD datasets entirely to test. Its default ratio is 0.8; this study uses 0.7 as an explicitly declared protocol variation.

## Important text-field distinction

The upstream `BaselineDataLoader` maps archive `prompt` into `BaselineRecord.prompt`, and the upstream Avengers-Pro adaptor groups and emits `record.prompt`.

This study's feature extractor instead selects `origin_query` when non-empty and falls back to `prompt`. The new study builder uses that same origin-query-first convention for `query`, so the embedding router receives the same text representation convention as the 11-feature analysis. This is an explicit adapter deviation from the upstream Avengers-Pro adaptor; results must be labelled as a study-specific Avengers-Pro adaptation, not an exact upstream reproduction.

The builder separately retains the archive's formatted `prompt` internally for duplicate/grouping checks, checks that it is consistent across all 13 candidate models, and rejects duplicate formatted prompts within a dataset because the upstream adaptor would merge such rows. It does not leak the internal split key into output JSONL.

## Builder added

`day1_audit/build_avengerspro_transfer_data.py`:
- uses the original ArenaHard JSONL plus the audited 750-row feature/score table;
- rechecks the 750-row positional mapping and all 11 feature values;
- reads archive records for the 13 selected models in the three source domains, GPQA, and MMLU-Pro;
- verifies source archive scores against the selected 13 score-table columns;
- verifies the source archive-selected query feature vectors against the audited 11-feature table;
- checks prompt/query consistency across models and rejects duplicate indices or duplicate prompts;
- writes one row per prompt with all 13 scores and per-model usage metadata;
- creates a seed-42, 70/30 source split and places GPQA (198) and MMLU-Pro (3,000) entirely in test;
- does not create target-informed baseline score files, call an embedding service, fit a router, or run target selection.

The split uses the upstream floor-count and seeded-shuffle mechanics with source datasets processed in sorted dataset-ID order. The output report records this ordering choice. The split ratio is a study protocol choice, not the upstream default.

## Expected partition sizes

For the three source domains:
- coding: 253 prompts → 177 train / 76 source holdout;
- creative writing: 250 prompts → 175 train / 75 source holdout;
- math: 247 prompts → 172 train / 75 source holdout.

Expected totals:
- source train: 524;
- source holdout in test: 226;
- OOD targets in test: GPQA 198 + MMLU-Pro 3,000;
- total test: 3,424;
- candidate models per prompt: exactly 13.

These are expected counts, not a claim that the local builder has already run.

## Execution gate

The builder requires `bench-release.tar.gz` in the repository root, `day1_audit/all_result_metadata.csv`, `day1_audit/prompt_feature_score_table.csv`, and the original ArenaHard JSONL. The last local path audit reported the archive missing from the checkout. Therefore no JSONL data has yet been generated or validated in this environment.

After restoring the original verified archive to the expected path, run:

```powershell
cd D:\Research3
python day1_audit\build_avengerspro_transfer_data.py
python day1_audit\day16_avengerspro_split_preflight.py --train day1_audit\avengerspro_transfer_seed42_split0.7\train.jsonl --test day1_audit\avengerspro_transfer_seed42_split0.7\test.jsonl --train-ratio 0.7
```

Do not proceed to embeddings/router execution until both commands pass and the build report is reviewed. Use a local embedding model or a local OpenAI-compatible endpoint only; do not invoke paid embedding APIs. Target scores must remain evaluation-only.
