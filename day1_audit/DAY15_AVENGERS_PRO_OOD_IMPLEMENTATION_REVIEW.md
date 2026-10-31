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
