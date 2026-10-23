import csv
import statistics
from collections import defaultdict, Counter
from pathlib import Path

root = Path((Path(__file__).resolve().parent / "day1_audit"))

with (root / "baseline_results.csv").open(
    newline="", encoding="utf-8-sig"
) as f:
    results = list(csv.DictReader(f))

with (root / "baseline_selected_models.csv").open(
    newline="", encoding="utf-8-sig"
) as f:
    selections = list(csv.DictReader(f))

by_domain = defaultdict(dict)
by_seed = defaultdict(dict)

for r in results:
    seed = int(r["seed"])
    domain = r["domain"]
    method = r["method"]
    score = float(r["mean_score"])
    by_domain[domain].setdefault(method, []).append(score)
    by_seed[(seed, domain)][method] = score

print("=== PER-DOMAIN MEAN TEST SCORES ACROSS FIVE SPLITS ===")
for domain in sorted(by_domain):
    methods = by_domain[domain]
    print(f"\n{domain}")
    for method in ("global", "domain_aware", "oracle_upper_bound"):
        vals = methods.get(method, [])
        if vals:
            print(
                f"  {method}: mean={statistics.mean(vals):.6f}, "
                f"split_sd={statistics.stdev(vals):.6f}"
            )
    paired = [
        by_seed[(seed, domain)]["domain_aware"]
        - by_seed[(seed, domain)]["global"]
        for seed in sorted({s for s, d in by_seed if d == domain})
    ]
    if paired:
        print(
            f"  paired domain-aware minus global: "
            f"mean={statistics.mean(paired):+.6f}; "
            f"wins={sum(x > 0 for x in paired)}/"
            f"{len(paired)} splits"
        )

print("\n=== PAIRED MACRO DIFFERENCE PER SEED ===")
for seed in sorted({int(r["seed"]) for r in results}):
    diffs = []
    for domain in sorted(by_domain):
        scores = by_seed[(seed, domain)]
        diffs.append(scores["domain_aware"] - scores["global"])
    print(
        f"seed={seed}: difference={statistics.mean(diffs):+.6f}"
    )

print("\n=== MOST FREQUENTLY SELECTED MODELS ===")
for method in ("global", "domain_aware"):
    counter = Counter(
        r["selected_model"] for r in selections
        if r["method"] == method
    )
    print(f"\n{method}:")
    for model, count in counter.most_common(10):
        print(f"  {model}: {count}")

print("\n=== REPORT COMPLETE ===")
