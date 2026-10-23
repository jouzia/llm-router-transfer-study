import csv
import random
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path((Path(__file__).resolve().parent / "day1_audit"))
INPUT = ROOT / "pilot_score_matrix.csv"
RESULTS = ROOT / "baseline_results.csv"
SELECTIONS = ROOT / "baseline_selected_models.csv"
SUMMARY = ROOT / "baseline_summary.txt"

SEEDS = [42, 43, 44, 45, 46]
TRAIN_FRAC = 0.60
VALID_FRAC = 0.20

with INPUT.open(newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    model_names = [
        name for name in reader.fieldnames
        if name not in {"dataset", "index"}
    ]
    rows = list(reader)

domains = sorted({row["dataset"] for row in rows})
data = defaultdict(list)

for row in rows:
    scores = {}
    for model in model_names:
        value = row.get(model, "")
        if value != "":
            scores[model] = float(value)
    data[row["dataset"]].append({
        "index": row["index"],
        "scores": scores,
    })

for domain in domains:
    records = data[domain]
    if len(records) < 30:
        raise RuntimeError(f"Too few records in {domain}")
    if any(len(r["scores"]) != len(model_names) for r in records):
        raise RuntimeError(f"Incomplete score row in {domain}")

results = []
selections = []

for seed in SEEDS:
    splits = {}
    for domain in domains:
        records = list(data[domain])
        rng = random.Random(seed * 1009 + sum(map(ord, domain)))
        rng.shuffle(records)

        n = len(records)
        n_train = int(n * TRAIN_FRAC)
        n_valid = int(n * VALID_FRAC)

        splits[domain] = {
            "train": records[:n_train],
            "validation": records[n_train:n_train + n_valid],
            "test": records[n_train + n_valid:],
        }

    # Choose the global model using training data only.
    # Macro-average domains so larger domains do not dominate.
    global_train_means = {}
    for model in model_names:
        domain_means = [
            statistics.mean(
                record["scores"][model]
                for record in splits[domain]["train"]
            )
            for domain in domains
        ]
        global_train_means[model] = statistics.mean(domain_means)

    global_model = max(
        model_names, key=lambda model: (global_train_means[model], model)
    )

    # Choose a separate model for each domain using training data only.
    domain_models = {}
    for domain in domains:
        train = splits[domain]["train"]
        means = {
            model: statistics.mean(r["scores"][model] for r in train)
            for model in model_names
        }
        domain_models[domain] = max(
            model_names, key=lambda model: (means[model], model)
        )

    for domain in domains:
        for method, model in [
            ("global", global_model),
            ("domain_aware", domain_models[domain]),
        ]:
            selections.append({
                "seed": seed,
                "domain": domain,
                "method": method,
                "selected_model": model,
            })

        test = splits[domain]["test"]
        for method, model in [
            ("global", global_model),
            ("domain_aware", domain_models[domain]),
        ]:
            achieved = [r["scores"][model] for r in test]
            oracle = [
                max(r["scores"].values()) for r in test
            ]
            regret = [
                best - actual
                for best, actual in zip(oracle, achieved)
            ]

            results.append({
                "seed": seed,
                "domain": domain,
                "method": method,
                "model": model,
                "test_prompts": len(test),
                "mean_score": statistics.mean(achieved),
                "oracle_mean": statistics.mean(oracle),
                "mean_regret": statistics.mean(regret),
            })

        # Oracle is computed on each test prompt, only as an upper bound.
        oracle_scores = [
            max(r["scores"].values()) for r in test
        ]
        results.append({
            "seed": seed,
            "domain": domain,
            "method": "oracle_upper_bound",
            "model": "PER_PROMPT_ORACLE",
            "test_prompts": len(test),
            "mean_score": statistics.mean(oracle_scores),
            "oracle_mean": statistics.mean(oracle_scores),
            "mean_regret": 0.0,
        })

with RESULTS.open("w", newline="", encoding="utf-8") as f:
    fields = [
        "seed", "domain", "method", "model", "test_prompts",
        "mean_score", "oracle_mean", "mean_regret"
    ]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(results)

with SELECTIONS.open("w", newline="", encoding="utf-8") as f:
    fields = ["seed", "domain", "method", "selected_model"]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(selections)

# Macro-average domain scores within each seed and method.
macro = defaultdict(list)
for seed in SEEDS:
    for method in ("global", "domain_aware", "oracle_upper_bound"):
        per_domain = [
            r for r in results
            if r["seed"] == seed
            and r["method"] == method
        ]
        macro[(method, "score")].append(
            statistics.mean(r["mean_score"] for r in per_domain)
        )
        macro[(method, "regret")].append(
            statistics.mean(r["mean_regret"] for r in per_domain)
        )

lines = [
    "RESEARCH 3: INITIAL OFFLINE BASELINE",
    f"Input: {INPUT}",
    f"Models: {len(model_names)}",
    f"Domains: {len(domains)}",
    f"Seeds: {SEEDS}",
    "Split: 60% train / 20% validation / 20% test per domain",
    "Validation is reserved and not used in this baseline.",
    "Global model selected on macro-average training performance.",
    "Domain-aware model selected separately per domain on training data.",
    "Oracle uses test labels and is only an upper bound.",
    "Primary score: mean per-record score; higher is better.",
    "Regret: oracle score minus selected model score; lower is better.",
    "",
    "MACRO-AVERAGED TEST RESULTS ACROSS DOMAINS",
]

for method in ("global", "domain_aware", "oracle_upper_bound"):
    scores = macro[(method, "score")]
    regrets = macro[(method, "regret")]
    lines.append(
        f"{method}: score mean={statistics.mean(scores):.6f}, "
        f"split SD={statistics.stdev(scores):.6f}, "
        f"regret mean={statistics.mean(regrets):.6f}, "
        f"regret split SD={statistics.stdev(regrets):.6f}"
    )

lines += [
    "",
    "Per-seed values reflect repeated random splits, not independent studies.",
    "Do not interpret split SD as a confidence interval.",
    "These results evaluate domain-level model selection, not yet a learned "
    "per-prompt router.",
    f"Detailed results: {RESULTS}",
    f"Selected models: {SELECTIONS}",
]

SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")

print("\n".join(lines))
print("\nSaved detailed results:", RESULTS)
print("Saved selected models:", SELECTIONS)
print("Saved summary:", SUMMARY)
