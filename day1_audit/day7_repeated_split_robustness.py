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

OUT_SUMMARY = AUDIT / "DAY7_REPEATED_SPLIT_SUMMARY.txt"
OUT_CSV = AUDIT / "DAY7_REPEATED_SPLIT_RESULTS.csv"

SEEDS = list(range(2026, 2036))
ALPHAS = [0.1, 1.0, 10.0, 100.0]
BOOTSTRAPS = 2000
DOMAINS = [
    "arenahard_coding",
    "arenahard_creative_writing",
    "arenahard_math",
]
FEATURES = [
    "char_count", "word_count", "line_count", "digit_count",
    "question_mark_count", "exclamation_count", "code_symbol_count",
    "contains_code_fence", "contains_url", "contains_equation_symbol",
    "contains_question_word",
]
CANDIDATES = [
    "claude-sonnet-4", "deepseek-r1-0528",
    "deepseek-v3.1-terminus", "deepseek-v3-0324",
    "gemini-2.5-flash", "gemini-2.5-pro", "glm-4.6",
    "gpt-5", "gpt-5-chat", "intern-s1", "kimi-k2-0905",
    "qwen3-235b-a22b-2507", "qwen3-235b-a22b-thinking-2507",
]
FIXED_REFERENCE = "gemini-2.5-pro"


def load_feature_function(path):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    node = next(
        n for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name == "feature_row"
    )
    namespace = {"re": re, "math": math}
    exec(compile(ast.Module(body=[node], type_ignores=[]),
                 str(path), "exec"), namespace)
    return namespace["feature_row"]


def get_text(rec):
    q = rec.get("origin_query")
    if isinstance(q, str) and q.strip():
        return q
    return rec.get("prompt")


def macro_utility(scores, choices, domains):
    chosen = scores[np.arange(len(choices)), choices]
    return float(np.mean([
        chosen[np.asarray(domains) == d].mean() for d in DOMAINS
    ]))


def fit_models(X, Y, alpha, indices):
    fitted = []
    for j in range(Y.shape[1]):
        model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
        model.fit(X[indices], Y[indices, j])
        fitted.append(model)
    return fitted


def bootstrap_ci(differences, seed):
    rng = np.random.default_rng(seed)
    n = len(differences)
    values = np.empty(BOOTSTRAPS)
    for start in range(0, BOOTSTRAPS, 100):
        end = min(start + 100, BOOTSTRAPS)
        sample = rng.integers(0, n, size=(end-start, n))
        values[start:end] = differences[sample].mean(axis=1)
    return np.quantile(values, [0.025, 0.975])


def main():
    for p in [ARCHIVE, SOURCE_CSV, META_CSV, EXTRACTOR]:
        if not p.exists():
            raise FileNotFoundError(p)

    feature_fn = load_feature_function(EXTRACTOR)

    with SOURCE_CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["dataset"] in DOMAINS]

    if len(rows) != 750:
        raise ValueError(f"Expected 750 source rows, found {len(rows)}")

    X = np.asarray([[float(r[c]) for c in FEATURES] for r in rows])
    Y = np.asarray([[float(r[m]) for m in CANDIDATES] for r in rows])
    domains = np.asarray([r["dataset"] for r in rows])

    with META_CSV.open(encoding="utf-8-sig", newline="") as f:
        metadata = list(csv.DictReader(f))

    target_meta = [
        r for r in metadata
        if r["dataset"].lower() == "mmlupro"
        and r["split"].lower() == "test_3000"
        and r["model"] in CANDIDATES
    ]
    if len(target_meta) != len(CANDIDATES):
        raise ValueError("Expected metadata for all 13 target models")

    target_records = {}
    with tarfile.open(ARCHIVE, "r:gz") as tar:
        members = {
            m.name.lstrip("./"): m for m in tar.getmembers() if m.isfile()
        }
        for meta in target_meta:
            name = meta["model"]
            member = members.get(meta["archive_path"].lstrip("./"))
            if member is None:
                raise ValueError(f"Archive member missing: {name}")
            payload = json.load(tar.extractfile(member))
            records = payload.get("records")
            if not isinstance(records, list) or len(records) != 3000:
                raise ValueError(f"{name}: expected 3000 records")

            indices, texts, scores = [], [], []
            for rec in records:
                idx, txt = str(rec.get("index", "")), get_text(rec)
                score = float(rec["score"])
                if not idx or not isinstance(txt, str) or not txt.strip():
                    raise ValueError(f"Invalid target record in {name}")
                if score not in (0.0, 1.0):
                    raise ValueError(f"Unexpected score in {name}: {score}")
                indices.append(idx)
                texts.append(re.sub(r"\s+", " ", txt).strip().casefold())
                scores.append(score)
            if len(set(indices)) != 3000:
                raise ValueError(f"Duplicate target indices: {name}")
            target_records[name] = (indices, texts, np.asarray(scores))

    first = target_records[CANDIDATES[0]]
    for name in CANDIDATES:
        item = target_records[name]
        if item[0] != first[0] or item[1] != first[1]:
            raise ValueError(f"Target prompt alignment mismatch: {name}")

    Xt = np.asarray([
        [float(feature_fn(txt)[c]) for c in FEATURES]
        for txt in [get_text(rec) for rec in []]
    ]) if False else None

    # Use original target text; features are computed once and reused.
    target_texts = []
    first_meta = next(r for r in target_meta if r["model"] == CANDIDATES[0])
    with tarfile.open(ARCHIVE, "r:gz") as tar:
        member = next(
            m for m in tar.getmembers()
            if m.isfile() and m.name.lstrip("./") ==
            first_meta["archive_path"].lstrip("./")
        )
        payload = json.load(tar.extractfile(member))
        target_texts = [get_text(rec) for rec in payload["records"]]

    Xt = np.asarray([
        [float(feature_fn(txt)[c]) for c in FEATURES]
        for txt in target_texts
    ])
    target_Y = np.column_stack([target_records[m][2] for m in CANDIDATES])
    target_domains = None
    model_counts = Counter()
    results = []

    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        train_parts, val_parts = [], []
        for domain in DOMAINS:
            idx = np.flatnonzero(domains == domain)
            perm = rng.permutation(idx)
            n_val = max(1, round(0.20 * len(idx)))
            val_parts.extend(perm[:n_val].tolist())
            train_parts.extend(perm[n_val:].tolist())

        train_idx = np.asarray(sorted(train_parts), dtype=int)
        val_idx = np.asarray(sorted(val_parts), dtype=int)

        alpha_rows = []
        for alpha in ALPHAS:
            models = fit_models(X, Y, alpha, train_idx)
            pred = np.column_stack([m.predict(X[val_idx]) for m in models])
            choices = pred.argmax(axis=1)
            utility = macro_utility(Y[val_idx], choices, domains[val_idx])
            alpha_rows.append((utility, alpha))

        # Fixed tie-break: choose the larger alpha on a utility tie.
        _, best_alpha = max(alpha_rows, key=lambda x: (x[0], x[1]))

        baseline_validation = {
            m: float(np.mean([
                Y[val_idx[domains[val_idx] == d], j].mean()
                for d in DOMAINS
            ]))
            for j, m in enumerate(CANDIDATES)
        }
        baseline = max(CANDIDATES, key=lambda m: baseline_validation[m])
        model_counts[baseline] += 1

        final_models = fit_models(X, Y, best_alpha, np.arange(len(rows)))
        target_pred = np.column_stack([m.predict(Xt) for m in final_models])
        choices = target_pred.argmax(axis=1)
        router_score = target_Y[np.arange(len(Xt)), choices]
        baseline_score = target_records[baseline][2]
        gemini_score = target_records[FIXED_REFERENCE][2]

        d_selected = router_score - baseline_score
        d_gemini = router_score - gemini_score
        ci_selected = bootstrap_ci(d_selected, seed + 50000)
        ci_gemini = bootstrap_ci(d_gemini, seed + 50000)

        results.append({
            "seed": seed,
            "alpha": best_alpha,
            "baseline": baseline,
            "validation_baseline_utility": baseline_validation[baseline],
            "router_accuracy": router_score.mean(),
            "selected_baseline_accuracy": baseline_score.mean(),
            "router_minus_selected_baseline": d_selected.mean(),
            "selected_ci_low": ci_selected[0],
            "selected_ci_high": ci_selected[1],
            "gemini_accuracy": gemini_score.mean(),
            "router_minus_gemini": d_gemini.mean(),
            "gemini_ci_low": ci_gemini[0],
            "gemini_ci_high": ci_gemini[1],
        })

    fields = list(results[0].keys())
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    lines = [
        "DAY 7 — REPEATED SOURCE-VALIDATION SPLITS",
        "Target: MMLU-Pro test_3000 (3000 prompts)",
        f"Prespecified seeds: {SEEDS}",
        "Each seed selects alpha and baseline using source validation only.",
        "Target results are evaluation-only and do not select a seed.",
        "",
        "BASELINE SELECTION COUNTS:",
    ]
    lines += [f"{m}: {model_counts[m]}" for m in CANDIDATES]
    lines += ["", "PER-SEED RESULTS:"]
    for r in results:
        lines.append(
            f"seed={r['seed']} alpha={r['alpha']} baseline={r['baseline']} "
            f"router={r['router_accuracy']:.4f} "
            f"selected_baseline={r['selected_baseline_accuracy']:.4f} "
            f"delta_selected={r['router_minus_selected_baseline']:+.4f} "
            f"CI=[{r['selected_ci_low']:+.4f},{r['selected_ci_high']:+.4f}] "
            f"Gemini={r['gemini_accuracy']:.4f} "
            f"delta_Gemini={r['router_minus_gemini']:+.4f}"
        )

    lines += [
        "",
        "SUMMARY ACROSS PRESPECIFIED SPLITS (descriptive, not independent trials):",
        f"Baseline-selection frequencies: {dict(model_counts)}",
        f"Selected-baseline delta mean: {np.mean([r['router_minus_selected_baseline'] for r in results]):+.4f}",
        f"Selected-baseline delta min/max: {min(r['router_minus_selected_baseline'] for r in results):+.4f} / {max(r['router_minus_selected_baseline'] for r in results):+.4f}",
        f"Gemini delta mean: {np.mean([r['router_minus_gemini'] for r in results]):+.4f}",
        f"Gemini delta min/max: {min(r['router_minus_gemini'] for r in results):+.4f} / {max(r['router_minus_gemini'] for r in results):+.4f}",
        "",
        "Caution: the same target prompts are reused across seeds. Do not treat",
        "these ten runs as independent target samples or select a best seed.",
        "The prompt bootstrap intervals condition on the observed target prompts.",
        "This experiment covers MMLU-Pro only; it does not establish broad generalization.",
    ]
    OUT_SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print("\nArtifacts written:")
    print(OUT_SUMMARY)
    print(OUT_CSV)
    print("\nDAY 7 COMPLETE")


if __name__ == "__main__":
    main()
