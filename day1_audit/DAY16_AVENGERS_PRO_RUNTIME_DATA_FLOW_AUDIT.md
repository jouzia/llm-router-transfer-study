# Day 16 — Avengers-Pro runtime data-flow audit

## Scope and pinned source

This review inspected the upstream LLMRouterBench implementation at commit
`0b81ba3053fbb74828382690a883849e2443e2d8`:

- `baselines/AvengersPro/simple_cluster_router.py`
- `baselines/AvengersPro/config.py`
- `generators/factory.py`
- `baselines/adaptors/avengerspro_adaptor.py`

This is a source-code review, not a local execution of the upstream runtime.

## Data-flow findings

1. `SimpleClusterRouter.run_routing()` calls `load_and_split_data()`, then
   `build_cluster_model(train_data)`, then `evaluate_routing(test_data)`.
2. `load_and_split_data()` reads the configured train and test JSONL files
   separately. It does not recompute the split.
3. `build_cluster_model()` embeds only train queries, fits the L2 normalizer
   and K-means model on those embeddings, and computes cluster rankings from
   train records only. The available model set is also discovered from
   training records.
4. `evaluate_routing()` first routes test queries using the already-fitted
   cluster model. Only after routing does it inspect each test item's
   `records` to calculate the selected model's score.
5. The test score lookup therefore acts as evaluation, not as a routing input,
   in the reviewed call path. The source/test split and OOD-only test placement
   remain essential preconditions; this review does not independently validate
   the prepared files beyond the separate local preflight result.

## Important evaluator semantics

- The evaluator initializes the selected-route score at 0.0 and takes the
  maximum score among selected models. It accumulates the original numeric
  score; it does not convert all scores to booleans.
- This retains ArenaHard's 0 / 0.5 / 1 score scale. The displayed metric is
  named "accuracy" in the upstream code, but for ternary judge scores it is
  more precisely mean selected-model score / expected reward, not binary
  accuracy.
- GPQA and MMLU-Pro use binary correctness scores in this archive, so the same
  calculation is binary accuracy for those target datasets.
- With `max_router > 1`, the evaluator scores the best-performing selected
  model on each test item (an oracle within the selected set), not the average
  of selected models. Keep `max_router=1` for the single-model routing
  experiment unless a multi-selection policy is explicitly pre-registered.

## Validation behavior and safeguards

- `_validate_data_item()` requires `query` and non-empty `records`, accepts
  numeric scores, converts booleans to 0/1, converts `null` to 0, and skips
  invalid JSON or invalid items with warnings. It does not enforce exactly 13
  candidate models, dataset/index uniqueness, or train/test disjointness.
- The local split preflight is therefore the stronger integrity gate and must
  pass before any runtime run. Do not treat runtime loading counts as a
  replacement for preflight.
- The runtime's model set is derived from training data. The prepared builder
  emits exactly 13 candidate models per prompt; verify that all 13 are present
  in the runtime's training model set before interpreting results.
- The default upstream configuration points to an embedding endpoint and
  requires an embedding API key. The embedding generator factory supports a
  configurable base URL; use a local OpenAI-compatible embedding service only.
  Do not send prompts to a paid or remote embedding API.

## Baseline-score file caveat

The reviewed config class requires `baseline_scores_path` to exist, and the
runtime loads that file for optional baseline comparisons. The prepared-data
builder currently emits train/test JSONL only. For a router-only run without
target-informed best-model comparisons, create an empty JSON object file
(e.g. `{}`) and point `baseline_scores_path` to it. Do not generate a
baseline score file from target test labels and then present its best-model
comparison as a deployable baseline; that is an oracle comparator.

## Execution status

- Local builder: PASSED (524 train; 3,424 test).
- Local split preflight: PASSED (70% source train per dataset; GPQA and
  MMLU-Pro test-only; no dataset/query crossing; exactly 13 models).
- Upstream runtime data-flow: source-reviewed as above.
- Upstream runtime execution with a local embedding endpoint: NOT YET RUN.
- No router result is claimed by this audit.

## Next gate

Before a full run:

1. Confirm the exact local embedding endpoint/model and verify it returns
   embeddings for a short test string.
2. Configure the upstream router to use the prepared train/test paths, an
   empty baseline-score JSON object, `max_router=1`, and the intended cluster
   hyperparameters.
3. Add a small runtime smoke test that loads both files and verifies 524/3,424
   rows and the 13-model training pool without fitting clusters or accessing
   target scores for model selection.
4. Only after these checks pass, run the full clustering/evaluation once and
   retain logs, config, package versions, embedding model identifier, and
   output hashes.
