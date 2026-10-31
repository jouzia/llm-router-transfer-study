# Day 15 follow-up — official Avengers-Pro OOD implementation review

## Upstream source reviewed

Repository: `ynulihao/LLMRouterBench`  
Reviewed revision: `0b81ba3053fbb74828382690a883849e2443e2d8`

Files reviewed:
- `baselines/AvengersPro/config.py`
- `baselines/AvengersPro/simple_cluster_router.py`
- `baselines/AvengersPro/balance_cluster_router.py`
- `baselines/data_loader.py`
- `baselines/README.md`
- `baselines/AvengersPro/config/simple_config.json`
- `config/embedding_config.yaml`

## Verified implementation facts

1. The official baseline loader supports `ood_datasets`; its documented behavior is to place the entire named dataset(s) in test. The loader splits by dataset and prompt so model records for a prompt remain together.
2. Avengers-Pro's simple and balance router configurations expose an `ood_datasets` list.
3. The simple router's training path builds embeddings, fits its normalizer/K-means model, and computes cluster-level model rankings from `train_data`. This is the intended point at which the source-only training boundary must be enforced.
4. The router uses the shared embedding generator. Its configuration requires a nonempty embedding API key and an embedding base URL/model name. The default configuration points to a hosted `gte_Qwen2-7B-instruct` endpoint.
5. The upstream embedding YAML enables a MySQL-backed cache by default, with connection details supplied via environment variables. That cache is not a zero-configuration local cache.
6. The baseline README documents the OOD loader and prompt-level split semantics. The config default shown in the simple router is not itself evidence that the requested OOD experiment has been executed.

## Protocol distinction

The official OOD split has a source `train_ratio` parameter strictly between zero and one; a 0.7 training fraction corresponds to a 30% source holdout and is consistent with the stated paper-style split. The existing Ridge analysis instead selected hyperparameters/baseline using source validation and then refit on all 750 source prompts. These are distinct training protocols.

For a fair report:
- Run the official Avengers-Pro baseline with a declared source-only training fraction and held-out `gpqa` / `mmlupro`.
- Keep all target prompts and target model scores out of cluster construction, ranking, and hyperparameter selection.
- Compare its results with the Ridge results as separate protocols, explicitly noting different source training sample sizes.
- Do not tune the embedding model or cluster parameters against target performance.

## Zero-cost embedding constraint

The checked-in upstream default is a hosted 7B embedding endpoint and a MySQL cache. It is not a verified free/local setup. No request has been sent to that endpoint and no paid API use has occurred.

A no-cost reproduction needs an explicitly documented local embedding implementation or local OpenAI-compatible embedding server, plus local caching. The paper's reported MiniLM ablation is a candidate sensitivity configuration, but using it would be an embedding-model deviation from the upstream default and must be labelled as such. The local CPU feasibility and exact compatibility remain unverified.

## Next verification gates

1. Inspect the full upstream embedding factory and supported generator types/dependencies.
2. Inspect the complete Avengers-Pro evaluation path to confirm baseline score files are used only for evaluation and cannot influence cluster construction.
3. Create a local, offline test fixture with synthetic source/target dataset IDs to validate the OOD split and router input files before processing benchmark data.
4. Decide whether CPU MiniLM can run on the available machine; estimate time/memory before downloading model weights.
5. Only then prepare the full 13-model, 70%-source-train OOD run. Do not start a remote embedding request.

## Status

The Claude discrepancy is documented separately as formatting-only. Official OOD capability is present in upstream code, but the no-cost embedding path and complete no-leakage execution path are not yet verified. No Avengers-Pro performance result has been generated.


## Follow-up audit: training/evaluation separation and embedding backend

Reviewed the upstream implementation at `ynulihao/LLMRouterBench` commit `0b81ba3053fbb74828382690a883849e2443e2d8`, including:

- `baselines/adaptors/avengerspro_adaptor.py`
- `baselines/AvengersPro/simple_cluster_router.py`
- `baselines/AvengersPro/config.py`
- `generators/factory.py`
- `generators/generator.py`
- `config/embedding_config.yaml`

### What the code establishes

1. **The route-fitting path is source-only when the split files are constructed correctly.** The runner loads the pre-split files, calls `build_cluster_model(train_data)`, then calls `evaluate_routing(test_data)`. Cluster embeddings, L2 normalization, K-means, and cluster-wise model rankings are fitted from `train_data`. The ranking computation reads model scores from training records only.
2. **OOD target labels are not used to choose a route.** `evaluate_routing` first routes the test queries via `route_queries_batch(queries)`; only afterwards does it inspect each selected model's score in that test row to calculate the evaluation outcome. The route method itself consumes query embeddings, fitted cluster centers, and training-derived rankings—not test-row scores.
3. **Target labels are nevertheless loaded into the evaluation process.** This is expected for scoring after the route is fixed. The adaptor also writes `baseline_scores.json` from test records only. The router loads this file after route evaluation for baseline comparison/reporting; it is not an input to cluster fitting or route selection.
4. **Important reporting caveat:** the upstream baseline comparison identifies the best model using each evaluation dataset's test scores. That is a hindsight/oracle comparator, not a source-selected deployable baseline. It must be labelled as an oracle/best-single-model-on-target comparison and must not be conflated with the user's source-validation-selected global baseline.
5. **Candidate-pool handling:** the adaptor obtains the list of model names from all loaded records before splitting, then fills absent model entries with score 0.0. This does not expose target score values to the fitting code, but it can alter evaluation if model records are missing. The current archive audit found complete model coverage for the selected 13-model pool; the prepared fixture must still assert exactly 13 observed scores per prompt and reject incomplete rows rather than silently rely on zero filling.
6. **The default embedding implementation is API-only.** The generator factory constructs `EmbeddingGenerator`, which uses the OpenAI client with configured `base_url` and `api_key`. The stock Avengers-Pro config and YAML point to a hosted embedding endpoint and a MySQL cache. There is no built-in sentence-transformers/local-model backend in this path. No network embedding call was made.
7. **A local embedding implementation is therefore a methodological adaptation.** It would require a small explicit adapter (or a local OpenAI-compatible embedding server) and a local cache. If using a different embedding model from the upstream `gte_Qwen2-7B-instruct`, the run must be reported as a local-model variant, not as an exact reproduction of the default Avengers-Pro embedding setup. A MiniLM-size model is a feasibility candidate only; it has not been tested on the user's machine.

### Remaining safeguards before any benchmark run

- Build a synthetic split fixture and assert that all GPQA/MMLU-Pro rows are test-only, all source prompt/model rows remain grouped, and no prompt crosses train/test.
- Assert the 13-model membership and exact 13-score coverage for every prompt; fail closed on missing/duplicate records.
- Persist route selections before loading or joining target score fields; evaluate only after route outputs are frozen.
- Keep target-derived best-single-model results explicitly labelled as oracle references.
- Verify local embedding dependency, model size, disk space, RAM and CPU runtime before downloading or embedding the real corpus.
- Do not use hosted endpoints, paid APIs, or the upstream MySQL cache.

### Audit status

**Training/evaluation separation: structurally supported by the reviewed code, conditional on correct split construction.** The key separation is explicit in the runner order and routing/evaluation methods. This is a source-code review, not a local execution or an independent proof of the user's eventual experiment pipeline.

**Embedding feasibility: not yet established.** No real-data run is authorized or recommended until the offline split fixture and local embedding feasibility gate pass.
