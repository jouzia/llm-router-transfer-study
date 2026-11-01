# Day 16 — ArenaHard prompt-to-feature alignment result

## Result

The original ArenaHard source file `repos/LLMRouterBench/data/ArenaHard/arena-hard-v2.jsonl` was compared against `day1_audit/prompt_feature_score_table.csv` using the repository's own `feature_row()` implementation and `FEATURE_NAMES` from `extract_prompt_features.py`.

The positional mapping tested was:

- Original JSONL records 1–253 → `arenahard_coding`
- Original JSONL records 254–500 → `arenahard_math`
- Original JSONL records 501–750 → `arenahard_creative_writing`

The domain assignment used each original record's `subcategory`; the table row was selected by the corresponding dataset key and 1-based original record position.

Observed result from the user's local PowerShell run:

- Original prompts checked: 750
- Rows compared: 750
- Rows with feature mismatches: 0
- Total mismatched feature cells: 0
- Exact 11-feature agreement: `True`

Thus, all 11 stored lexical/structural features are exactly reproduced for all 750 original ArenaHard prompt strings under the positional mapping and the committed extractor implementation.

## Interpretation

This is strong independent corroboration of the positional alignment between the original ArenaHard JSONL prompt records and the 750-row feature table. It materially strengthens the evidence beyond matching domain counts and contiguous index ranges alone.

It also supports using the original JSONL `prompt` field as a feature-source reconstruction for this table, because it reproduces every stored feature exactly.

## Remaining provenance limitation

This test does **not** establish byte-for-byte identity between the original JSONL `prompt` strings and the archive-selected strings used by the original extractor. The extractor selects `origin_query` when non-empty and otherwise `prompt`; the referenced archive members are not present in the local checkout and could not be directly compared.

Accordingly:

- Claim exact 11-feature-vector agreement for all 750 rows.
- Describe the original JSONL prompt-to-table positional alignment as strongly corroborated.
- Do not claim exact string identity with archive `origin_query` unless the archive text becomes available for direct comparison.
- Do not silently relabel the original strings as verified archive `origin_query` values.

## Reproducibility

The comparison imported `feature_row` and `FEATURE_NAMES` directly from `extract_prompt_features.py`, loaded the original JSONL and the existing feature table, and compared integer values for each of the 11 features on every mapped row. The feature table was not regenerated or modified by this check.

## Research consequence

The source feature table can be treated as aligned to the original ArenaHard prompt set for the 11-feature analysis, subject to the explicit archive-string provenance limitation above. This result does not change score semantics, establish independent ground truth, or resolve the separate source-to-target benchmark/evaluator shift.
