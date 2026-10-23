import csv
import statistics
from collections import Counter, defaultdict
from pathlib import Path

path = (Path(__file__).resolve().parent / "day1_audit" / "pilot_score_matrix.csv")

with path.open(newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

models = [
    k for k in rows[0]
    if k not in {"dataset", "index"}
]

by_domain = defaultdict(list)
winner_counts = defaultdict(Counter)
margins = defaultdict(list)
score_spreads = defaultdict(list)
ties = Counter()

for row in rows:
    domain = row["dataset"]
    scores = {m: float(row[m]) for m in models if row[m] != ""}
    if not scores:
        continue

    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_score = ordered[0][1]
    second_score = ordered[1][1] if len(ordered) > 1 else best_score
    best_models = [m for m, s in ordered if s == best_score]

    # Count tied winners fractionally so ties do not favor one model.
    for model in best_models:
        winner_counts[domain][model] += 1 / len(best_models)

    if len(best_models) > 1:
        ties[domain] += 1

    margins[domain].append(best_score - second_score)
    score_spreads[domain].append(
        max(scores.values()) - min(scores.values())
    )
    by_domain[domain].append(scores)

print("=== PROMPT-LEVEL MODEL DIFFERENCES ===")

for domain in sorted(by_domain):
    print(f"\nDOMAIN: {domain}")
    print("Prompts:", len(by_domain[domain]))
    print("Prompts with tied best score:", ties[domain])
    print(
        "Mean best-vs-second-best margin:",
        f"{statistics.mean(margins[domain]):.6f}"
    )
    print(
        "Mean best-vs-worst score spread:",
        f"{statistics.mean(score_spreads[domain]):.6f}"
    )
    print("Most frequent best-scoring models:")
    for model, count in winner_counts[domain].most_common(8):
        print(f"  {model}: fractional wins={count:.2f}")

print("\n=== OVERALL WINNER COUNTS ===")
overall = Counter()
for domain, counts in winner_counts.items():
    overall.update(counts)

for model, count in overall.most_common(12):
    print(f"{model}: fractional wins={count:.2f}")

print("\nThis is descriptive analysis only; it does not train or test a router.")
