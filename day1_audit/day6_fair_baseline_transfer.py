import ast
import csv
import json
import math
import re
import tarfile
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "day1_audit"
ARCHIVE = ROOT / "bench-release.tar.gz"
SOURCE_CSV = AUDIT / "prompt_feature_score_table.csv"
META_CSV = AUDIT / "all_result_metadata.csv"
EXTRACTOR = ROOT / "extract_prompt_features.py"

OUT_TXT = AUDIT / "DAY6_MMLUPRO_TRANSFER_RESULTS.txt"
OUT_CSV = AUDIT / "DAY6_MMLUPRO_PER_PROMPT_RESULTS.csv"
OUT_CONFIG = AUDIT / "DAY6_MMLUPRO_ROUTER_CONFIG.txt"
OUT_REPORT = AUDIT / "DAY6_MMLUPRO_FINAL_REPORT.md"

SEED = 2026
BOOTSTRAPS = 10000
ALPHAS = [0.1, 1.0, 10.0, 100.0]
FEATURES = [
    "char_count", "word_count", "line_count", "digit_count",
    "question_mark_count", "exclamation_count", "code_symbol_count",
    "contains_code_fence", "contains_url", "contains_equation_symbol",
    "contains_question_word",
]
CANDIDATES = [
    "claude-sonnet-4",
    "deepseek-r1-0528",
    "deepseek-v3.1-terminus",
    "deepseek-v3-0324",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "glm-4.6",
    "gpt-5",
    "gpt-5-chat",
    "intern-s1",
    "kimi-k2-0905",
    "qwen3-235b-a22b-2507",
    "qwen3-235b-a22b-thinking-2507",
]
DOMAINS = [
    "arenahard_coding",
    "arenahard_creative_writing",
    "arenahard_math",
]

def prompt_text(rec):
    origin = rec.get("origin_query")
    if isinstance(origin, str) and origin.strip():
        return origin
    return rec.get("prompt")

def normalize(text):
    return re.sub(r"\s+", " ", text).strip().casefold()

def load_feature_function(path):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    node = next(
        n for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name == "feature_row"
    )
    module = ast.Module(body=[node], type_ignores=[])
    namespace = {"re": re, "math": math}
    exec(compile(module, str(path), "exec"), namespace)
    return namespace["feature_row"]

def numeric_feature_row(text, feature_fn):
    result = feature_fn(text)
    return [float(result[name]) for name in FEATURES]

def macro_domain_utility(scores, choices, domains, model_names):
    chosen_scores = scores[np.arange(len(choices)), choices]
    per_domain = {}
    for domain in DOMAINS:
        mask = np.asarray(domains) == domain
        if not mask.any():
            raise ValueError(f"Missing source domain: {domain}")
        per_domain[domain] = float(chosen_scores[mask].mean())
    return float(np.mean(list(per_domain.values()))), per_domain

def main():
    for path in [ARCHIVE, SOURCE_CSV, META_CSV, EXTRACTOR]:
        if not path.exists():
            raise FileNotFoundError(path)

    feature_fn = load_feature_function(EXTRACTOR)

    with SOURCE_CSV.open(encoding="utf-8-sig", newline="") as f:
        source_rows = list(csv.DictReader(f))
    if not source_rows:
        raise ValueError("Source feature/score table is empty")

    feature_columns = {
        "dataset", "index", "prompt_text_source", *FEATURES
    }
    available_models = set(source_rows[0]) - feature_columns
    missing = sorted(set(CANDIDATES) - available_models)
    if missing:
        raise ValueError(f"Candidate models missing from source table: {missing}")

    source_rows = [
        row for row in source_rows
        if row["dataset"] in DOMAINS
    ]
    if not source_rows:
        raise ValueError("No rows found for the three expected source domains")

    X = np.asarray(
        [[float(row[f]) for f in FEATURES] for row in source_rows],
        dtype=float,
    )
    Y = np.asarray(
        [[float(row[m]) for m in CANDIDATES] for row in source_rows],
        dtype=float,
    )
    source_domains = np.asarray([r["dataset"] for r in source_rows])

    if not np.isfinite(X).all() or not np.isfinite(Y).all():
        raise ValueError("Non-finite source feature or score values detected")

    # Reproduce the established source-only, domain-stratified validation split.
    rng = np.random.default_rng(SEED)
    train_parts, val_parts = [], []
    for domain in DOMAINS:
        idx = np.flatnonzero(source_domains == domain)
        if len(idx) < 2:
            raise ValueError(f"Too few source rows in {domain}")
        permuted = rng.permutation(idx)
        n_val = max(1, round(0.20 * len(idx)))
        val_parts.extend(permuted[:n_val].tolist())
        train_parts.extend(permuted[n_val:].tolist())

    train_idx = np.asarray(sorted(train_parts), dtype=int)
    val_idx = np.asarray(sorted(val_parts), dtype=int)

    alpha_results = []
    for alpha in ALPHAS:
        models = []
        for j in range(len(CANDIDATES)):
            model = make_pipeline(
                StandardScaler(),
                Ridge(alpha=alpha),
            )
            model.fit(X[train_idx], Y[train_idx, j])
            models.append(model)

        val_predictions = np.column_stack(
            [model.predict(X[val_idx]) for model in models]
        )
        val_choices = val_predictions.argmax(axis=1)
        utility, per_domain = macro_domain_utility(
            Y[val_idx], val_choices, source_domains[val_idx], CANDIDATES
        )
        alpha_results.append((utility, alpha, per_domain))

    # Tie-break toward stronger regularization, as in Day 4.
    best_utility, best_alpha, best_domain_scores = max(
        alpha_results, key=lambda item: (item[0], item[1])
    )

    # Day 6 correction: select the single-model baseline on the same
    # source-only validation split used to select Ridge alpha.
    # Target scores are not used to select either choice.
    global_domain_means = {}
    for j, model_name in enumerate(CANDIDATES):
        global_domain_means[model_name] = float(np.mean([
            Y[val_idx[source_domains[val_idx] == d], j].mean()
            for d in DOMAINS
        ]))
    global_model = max(CANDIDATES, key=lambda m: global_domain_means[m])

    # Freeze source-side choices before reading target scores.
    final_models = []
    for j in range(len(CANDIDATES)):
        model = make_pipeline(
            StandardScaler(),
            Ridge(alpha=best_alpha),
        )
        model.fit(X, Y[:, j])
        final_models.append(model)

    with META_CSV.open(encoding="utf-8-sig", newline="") as f:
        metadata = list(csv.DictReader(f))
    target_meta = [
        r for r in metadata
        if r["dataset"].lower() == "mmlupro"
        and r["split"].lower() == "test_3000"
        and r["model"] in CANDIDATES
    ]
    if len(target_meta) != 13 or {r["model"] for r in target_meta} != set(CANDIDATES):
        raise ValueError("Target metadata does not contain exactly the 13 shared candidates")

    # Read only the target records after the source router is frozen.
    target_records = {}
    with tarfile.open(ARCHIVE, "r:gz") as tar:
        member_map = {
            m.name.lstrip("./"): m
            for m in tar.getmembers() if m.isfile()
        }
        for row in target_meta:
            model_name = row["model"]
            member = member_map.get(row["archive_path"].lstrip("./"))
            if member is None:
                raise ValueError(f"Archive member missing for {model_name}")
            handle = tar.extractfile(member)
            if handle is None:
                raise ValueError(f"Could not read archive member for {model_name}")
            payload = json.load(handle)
            records = payload.get("records")
            if not isinstance(records, list) or len(records) != 3000:
                raise ValueError(f"{model_name}: expected exactly 3000 records")

            indices, texts, scores = [], [], []
            for rec in records:
                idx = str(rec.get("index", ""))
                text = prompt_text(rec)
                score = rec.get("score")
                if not idx:
                    raise ValueError(f"{model_name}: missing index")
                if not isinstance(text, str) or not text.strip():
                    raise ValueError(f"{model_name}: missing prompt at {idx}")
                try:
                    score = float(score)
                except (TypeError, ValueError):
                    raise ValueError(f"{model_name}: invalid score at {idx}")
                if not math.isfinite(score) or score not in (0.0, 1.0):
                    raise ValueError(f"{model_name}: unexpected score {score} at {idx}")
                indices.append(idx)
                texts.append(text)
                scores.append(score)

            if len(set(indices)) != 3000:
                raise ValueError(f"{model_name}: duplicate indices")
            target_records[model_name] = {
                "indices": indices, "texts": texts,
                "scores": np.asarray(scores, dtype=float),
            }

    reference = target_records[CANDIDATES[0]]
    ref_norm = [normalize(t) for t in reference["texts"]]
    for model_name in CANDIDATES:
        item = target_records[model_name]
        if item["indices"] != reference["indices"]:
            raise ValueError(f"{model_name}: target index order mismatch")
        if [normalize(t) for t in item["texts"]] != ref_norm:
            raise ValueError(f"{model_name}: target prompt order mismatch")

    # Prompt features are derived from the aligned target prompts.
    Xt = np.asarray(
        [numeric_feature_row(t, feature_fn) for t in reference["texts"]],
        dtype=float,
    )
    if not np.isfinite(Xt).all():
        raise ValueError("Non-finite target features detected")

    target_predictions = np.column_stack(
        [model.predict(Xt) for model in final_models]
    )
    router_choices = target_predictions.argmax(axis=1)
    router_scores_matrix = np.column_stack(
        [target_records[m]["scores"] for m in CANDIDATES]
    )
    router_scores = router_scores_matrix[
        np.arange(len(router_choices)), router_choices
    ]
    global_scores = target_records[global_model]["scores"]
    differences = router_scores - global_scores

    n = len(differences)
    boot_rng = np.random.default_rng(SEED)
    boot_means = np.empty(BOOTSTRAPS, dtype=float)
    # Chunked bootstrap limits peak memory use.
    for start in range(0, BOOTSTRAPS, 200):
        end = min(start + 200, BOOTSTRAPS)
        sampled = boot_rng.integers(0, n, size=(end - start, n))
        boot_means[start:end] = differences[sampled].mean(axis=1)
    ci_low, ci_high = np.quantile(boot_means, [0.025, 0.975])

    router_mean = float(router_scores.mean())
    global_mean = float(global_scores.mean())
    delta = float(differences.mean())
    wins = int((differences > 0).sum())
    ties = int((differences == 0).sum())
    losses = int((differences < 0).sum())
    selection_counts = Counter(CANDIDATES[i] for i in router_choices)

    result_lines = [
        "DAY 6 — MMLU-PRO HELD-OUT TRANSFER EXPERIMENT",
        f"Target split: mmlupro/test_3000",
        f"Target prompts: {n}",
        f"Shared candidate models: {len(CANDIDATES)}",
        f"Source rows: {len(source_rows)}",
        f"Source domains: {', '.join(DOMAINS)}",
        f"Source validation fraction per domain: 20%",
        f"Validation seed: {SEED}",
        f"Selected alpha: {best_alpha}",
        f"Global baseline model: {global_model}",
        f"Router mean score: {router_mean:.6f}",
        f"Global baseline mean score: {global_mean:.6f}",
        f"Mean paired difference (router - global): {delta:+.6f}",
        f"95% prompt-bootstrap percentile CI: [{ci_low:+.6f}, {ci_high:+.6f}]",
        f"Wins/ties/losses: {wins}/{ties}/{losses}",
        "",
        "ROUTER SELECTION FREQUENCIES:",
    ]
    result_lines += [
        f"{model}: {selection_counts.get(model, 0)}"
        for model in CANDIDATES
    ]
    result_lines += ["", "SOURCE VALIDATION UTILITY BY ALPHA:"]
    for utility, alpha, per_domain in alpha_results:
        result_lines.append(
            f"alpha={alpha}: macro_utility={utility:.8f}; {per_domain}"
        )
    result_lines += [
        "",
        "GLOBAL BASELINE VALIDATION MACRO-MEAN:",
        *[f"{m}: {global_domain_means[m]:.8f}" for m in CANDIDATES],
        "",
        "Interpretation: target results are descriptive for this benchmark and",
        "this candidate pool. A bootstrap interval containing zero does not",
        "establish a reliable difference. One transfer benchmark cannot establish",
        "broad generalization or research novelty.",
        "The prompt bootstrap conditions on the observed benchmark prompts and",
        "does not quantify training, model-version, or benchmark-construction uncertainty.",
        "The global baseline and Ridge alpha are both selected on the same",
        "source-only validation split. Selection on one split can be unstable.",
        "Cost/latency claims are excluded because aggregate metric semantics remain unresolved.",
    ]
    OUT_TXT.write_text("\n".join(result_lines) + "\n", encoding="utf-8")

    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "index", "router_model", "router_score",
            "global_model", "global_score", "paired_difference",
        ])
        for i in range(n):
            writer.writerow([
                reference["indices"][i],
                CANDIDATES[int(router_choices[i])],
                float(router_scores[i]),
                global_model,
                float(global_scores[i]),
                float(differences[i]),
            ])

    config_lines = [
        "DAY 6 — SOURCE-ONLY ROUTER CONFIGURATION",
        f"Source rows: {len(source_rows)}",
        f"Source domains: {', '.join(DOMAINS)}",
        f"Candidate models: {len(CANDIDATES)}",
        f"Validation seed: {SEED}",
        f"Validation fraction per source domain: 20%",
        f"Alpha candidates: {ALPHAS}",
        f"Selected alpha: {best_alpha}",
        f"Selected source validation macro utility: {best_utility:.8f}",
        f"Validation-selected global baseline: {global_model}",
        f"Global baseline validation macro-mean: {global_domain_means[global_model]:.8f}",
        "Target scores were not used for source fitting or model/alpha selection.",
        "",
        "Validation utility by alpha:",
    ]
    config_lines += [
        f"alpha={alpha}: utility={utility:.8f}; {per_domain}"
        for utility, alpha, per_domain in alpha_results
    ]
    OUT_CONFIG.write_text("\n".join(config_lines) + "\n", encoding="utf-8")

    report = f"""# Day 6 — MMLU-Pro Held-Out Transfer Results

## Protocol

- Source: {len(source_rows)} ArenaHard rows across coding, creative writing, and math.
- Features: 11 lexical/structural prompt features.
- Candidate pool: 13 models shared between source data and MMLU-Pro `test_3000`.
- Alpha selected from {ALPHAS} using a domain-stratified 20% source validation split (seed {SEED}).
- Final router refit on all source rows after alpha selection.
- Target: 3,000 aligned MMLU-Pro prompts; target scores are evaluation-only.
- Global baseline selected by equal-weight mean performance across the source validation domains: `{global_model}`.

## Results

| Metric | Result |
|---|---:|
| Router mean score | {router_mean:.4%} |
| Global baseline mean score | {global_mean:.4%} |
| Paired difference (router − baseline) | {delta*100:+.3f} percentage points |
| 95% prompt-bootstrap percentile interval | [{ci_low*100:+.3f}, {ci_high*100:+.3f}] percentage points |
| Router wins / ties / losses | {wins} / {ties} / {losses} |
| Selected alpha | {best_alpha} |

## Interpretation

This is one held-out benchmark transfer result, not evidence by itself of broad generalization or novelty. If the interval contains zero, the observed difference is not statistically distinguishable from zero under this prompt-bootstrap analysis. If the interval excludes zero, that is still limited to the benchmark and evaluation protocol used here.

Both the baseline model and Ridge alpha are selected using the same source-only validation split. The router is refit on all source rows after alpha selection. Reusing the validation split for both choices can still cause model-selection optimism; this result is conditional on the fixed split. The bootstrap does not capture variability from training choices, model versions, or benchmark construction. Cost and latency comparisons are omitted pending metric-semantics verification.

## Router model selection frequencies

{chr(10).join(f"- `{m}`: {selection_counts.get(m, 0)} prompts" for m in CANDIDATES)}

## Artifacts

- `DAY6_MMLUPRO_TRANSFER_RESULTS.txt`
- `DAY6_MMLUPRO_PER_PROMPT_RESULTS.csv`
- `DAY6_MMLUPRO_ROUTER_CONFIG.txt`
- `DAY6_MMLUPRO_FINAL_REPORT.md`
"""
    OUT_REPORT.write_text(report, encoding="utf-8")

    print("\n".join(result_lines[:18]))
    print("\nARTIFACTS WRITTEN:")
    for p in [OUT_TXT, OUT_CSV, OUT_CONFIG, OUT_REPORT]:
        print(p)
    print("\nDAY 6 MMLU-PRO TRANSFER RUN COMPLETE")

if __name__ == "__main__":
    main()
