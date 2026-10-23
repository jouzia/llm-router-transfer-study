import csv
import random
import statistics
from collections import defaultdict
from pathlib import Path

source = (Path(__file__).resolve().parent / "day1_audit" / "prompt_router_test_predictions.csv")
output = (Path(__file__).resolve().parent / "day1_audit" / "day2_paired_analysis.txt")

with source.open(newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

if not rows:
    raise SystemExit("ERROR: prediction file is empty.")

comparisons = {
    "feature_minus_domain": (
        "feature_router_test_score", "domain_aware_test_score"
    ),
    "feature_minus_global": (
        "feature_router_test_score", "global_test_score"
    ),
}

groups = defaultdict(list)

for row in rows:
    seed = int(row["seed"])
    domain = row["domain"]

    for comparison, (a, b) in comparisons.items():
        difference = float(row[a]) - float(row[b])
        groups[(seed, domain, comparison)].append(difference)
        groups[(seed, "ALL_DOMAINS", comparison)].append(difference)

def bootstrap_ci(values, seed, iterations=5000):
    # Prompt-level paired bootstrap. Descriptive split-specific interval;
    # repeated prompts across seeds mean seeds are not independent studies.
    rng = random.Random(seed)
    n = len(values)
    estimates = []

    for _ in range(iterations):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        estimates.append(statistics.mean(sample))

    estimates.sort()
    lo = estimates[int(0.025 * iterations)]
    hi = estimates[min(int(0.975 * iterations), iterations - 1)]
    return lo, hi

lines = [
    "DAY 2 — PAIRED ROUTING ANALYSIS",
    "=" * 65,
    f"Prediction rows: {len(rows)}",
    "Positive difference means the feature selector scored higher.",
    "Bootstrap intervals resample prompts within each seed/domain.",
    "They do not account for benchmark provenance, prompt dependence,",
    "or uncertainty from choosing the method using validation results.",
    "",
]

for comparison in comparisons:
    lines.append(f"COMPARISON: {comparison}")
    seed_means = []

    for seed in sorted({int(r["seed"]) for r in rows}):
        values = groups[(seed, "ALL_DOMAINS", comparison)]
        avg = statistics.mean(values)
        lo, hi = bootstrap_ci(values, seed * 100 + 1)
        seed_means.append(avg)

        wins = sum(x > 0 for x in values)
        ties = sum(x == 0 for x in values)
        losses = sum(x < 0 for x in values)

        lines.append(
            f"  Seed {seed}: n={len(values)}, mean_diff={avg:+.6f}, "
            f"prompt_wins={wins}, ties={ties}, losses={losses}, "
            f"paired_bootstrap_95%_CI=[{lo:+.6f}, {hi:+.6f}]"
        )

    lines.append(
        f"  Across-seed mean of split differences: "
        f"{statistics.mean(seed_means):+.6f}"
    )
    lines.append(
        f"  Across-seed range: "
        f"[{min(seed_means):+.6f}, {max(seed_means):+.6f}]"
    )

    lines.append("  Per-domain differences:")
    for domain in sorted({r["domain"] for r in rows}):
        means = []
        for seed in sorted({int(r["seed"]) for r in rows}):
            values = groups.get((seed, domain, comparison), [])
            if values:
                means.append((seed, statistics.mean(values)))

        text = ", ".join(
            f"seed {s}: {v:+.4f}" for s, v in means
        )
        lines.append(f"    {domain}: {text}")

    lines.append("")

output.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
print(f"\nSaved report: {output}")
