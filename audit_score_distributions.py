import csv
import statistics
from collections import Counter, defaultdict
from pathlib import Path

source = (Path(__file__).resolve().parent / "day1_audit" / "pilot_score_matrix.csv")
output = (Path(__file__).resolve().parent / "day1_audit" / "score_distribution_audit.txt")

with source.open(newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

if not rows:
    raise SystemExit("ERROR: score matrix is empty.")

excluded = {"dataset", "index"}
models = [c for c in rows[0] if c not in excluded]

lines = []
lines.append("RESEARCH 3 — SCORE DISTRIBUTION AUDIT")
lines.append("=" * 55)
lines.append(f"Input rows: {len(rows)}")
lines.append(f"Model columns: {len(models)}")

by_domain = defaultdict(list)
all_scores = []
model_scores = defaultdict(list)
top_score_counts = Counter()
top_tie_counts = Counter()

for row in rows:
    domain = row["dataset"]
    scores = {
        m: float(row[m])
        for m in models
        if row.get(m, "").strip() != ""
    }
    if not scores:
        continue

    values = list(scores.values())
    all_scores.extend(values)
    by_domain[domain].append(scores)

    for model, score in scores.items():
        model_scores[model].append(score)

    top = max(values)
    winners = [m for m, s in scores.items() if s == top]
    top_score_counts[domain, top] += 1
    top_tie_counts[domain, len(winners)] += 1

lines.append(f"Total individual scores: {len(all_scores)}")
lines.append(f"Distinct pooled score values: {len(set(all_scores))}")
lines.append(f"Distinct pooled values (first 30): {sorted(set(all_scores))[:30]}")
lines.append("")

for domain in sorted(by_domain):
    domain_scores = [
        score
        for prompt in by_domain[domain]
        for score in prompt.values()
    ]
    score_hist = Counter(domain_scores)
    prompt_count = len(by_domain[domain])

    lines.append(f"DOMAIN: {domain}")
    lines.append(f"Prompts: {prompt_count}")
    lines.append(f"Individual scores: {len(domain_scores)}")
    lines.append(f"Mean score: {statistics.mean(domain_scores):.6f}")
    lines.append(f"Median score: {statistics.median(domain_scores):.6f}")
    lines.append(f"Distinct score values: {len(score_hist)}")
    lines.append("Most common individual scores:")
    for score, count in score_hist.most_common(10):
        lines.append(
            f"  score={score:.6f}: {count} "
            f"({count / len(domain_scores):.1%})"
        )

    lines.append("Number of prompts by number of tied top-scoring models:")
    for tie_count, prompts in sorted(top_tie_counts.items()):
        if tie_count[0] == domain:
            lines.append(f"  {tie_count[1]} model(s): {prompts} prompts")

    top_hist = Counter()
    for (d, score), count in top_score_counts.items():
        if d == domain:
            top_hist[score] = count
    lines.append("Most common per-prompt maximum scores:")
    for score, count in top_hist.most_common(8):
        lines.append(f"  max={score:.6f}: {count} prompts")
    lines.append("")

lines.append("MODEL MEANS — descriptive, not test-set routing results")
for model, values in sorted(
    model_scores.items(),
    key=lambda item: statistics.mean(item[1]),
    reverse=True
)[:15]:
    lines.append(
        f"{model}: mean={statistics.mean(values):.6f}; "
        f"n={len(values)}"
    )

report = "\n".join(lines) + "\n"
output.write_text(report, encoding="utf-8")
print(report)
print(f"\nSaved report: {output}")
