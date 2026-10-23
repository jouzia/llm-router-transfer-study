from pathlib import Path
import tarfile, json, os, csv, math
from collections import Counter

archive = (Path(__file__).resolve().parent / "bench-release.tar.gz")
outdir = (Path(__file__).resolve().parent / "day1_audit")
os.makedirs(outdir, exist_ok=True)

checks = []
errors = []

with tarfile.open(archive, "r:gz") as tar:
    for member in tar:
        if not member.isfile() or not member.name.endswith(".json"):
            continue
        try:
            f = tar.extractfile(member)
            obj = json.load(f)
            records = obj.get("records") or []

            scores = [
                float(r["score"]) for r in records
                if isinstance(r, dict)
                and isinstance(r.get("score"), (int, float))
                and math.isfinite(float(r["score"]))
            ]
            costs = [
                float(r["cost"]) for r in records
                if isinstance(r, dict)
                and isinstance(r.get("cost"), (int, float))
                and math.isfinite(float(r["cost"]))
            ]

            indices = [str(r.get("index")) for r in records if isinstance(r, dict)]
            duplicate_indices = len(indices) - len(set(indices))

            aggregate = obj.get("performance")
            mean_score = sum(scores) / len(scores) if scores else None
            score_diff = (
                abs(float(aggregate) - mean_score)
                if aggregate is not None and mean_score is not None
                else None
            )

            agg_cost = obj.get("cost")
            sum_cost = sum(costs) if costs else None
            cost_diff = (
                abs(float(agg_cost) - sum_cost)
                if agg_cost is not None and sum_cost is not None
                else None
            )

            row = {
                "dataset": obj.get("dataset_name"),
                "model": obj.get("model_name"),
                "split": obj.get("split"),
                "records": len(records),
                "declared_count": obj.get("counts"),
                "count_diff": len(records) - int(obj["counts"]) if obj.get("counts") is not None else None,
                "duplicate_indices": duplicate_indices,
                "scored_records": len(scores),
                "score_min": min(scores) if scores else None,
                "score_max": max(scores) if scores else None,
                "aggregate_performance": aggregate,
                "mean_record_score": mean_score,
                "score_diff": score_diff,
                "aggregate_cost": agg_cost,
                "sum_record_cost": sum_cost,
                "cost_diff": cost_diff,
                "time_taken": obj.get("time_taken"),
                "archive_path": member.name
            }
            checks.append(row)

        except Exception as e:
            errors.append({"archive_path": member.name, "error": str(e)})

def write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

write_csv(os.path.join(outdir, "record_quality_checks.csv"), checks)
write_csv(os.path.join(outdir, "quality_check_errors.csv"), errors)

print("=== QUALITY AUDIT SUMMARY ===")
print("Files checked:", len(checks))
print("Errors:", len(errors))
print("Record-count mismatches:", sum(r["count_diff"] not in (None, 0) for r in checks))
print("Files with duplicate indices:", sum(r["duplicate_indices"] > 0 for r in checks))
print("Files where score range is outside [0,1]:",
      sum(r["score_min"] is not None and (r["score_min"] < 0 or r["score_max"] > 1) for r in checks))
print("Files with score difference > 1e-6:",
      sum(r["score_diff"] is not None and r["score_diff"] > 1e-6 for r in checks))
print("Files with cost difference > 1e-6:",
      sum(r["cost_diff"] is not None and r["cost_diff"] > 1e-6 for r in checks))

print("\n=== COUNT / DUPLICATE EXCEPTIONS ===")
for r in checks:
    if r["count_diff"] not in (None, 0) or r["duplicate_indices"] > 0:
        print(
            f'{r["dataset"]} | {r["model"]} | split={r["split"]} | '
            f'records={r["records"]} declared={r["declared_count"]} '
            f'count_diff={r["count_diff"]} duplicate_indices={r["duplicate_indices"]}'
        )

print("\n=== LARGEST SCORE AGGREGATION DIFFERENCES ===")
valid = [r for r in checks if r["score_diff"] is not None]
for r in sorted(valid, key=lambda x: x["score_diff"], reverse=True)[:12]:
    print(
        f'{r["dataset"]} | {r["model"]} | split={r["split"]} | '
        f'aggregate={r["aggregate_performance"]} mean={r["mean_record_score"]} '
        f'diff={r["score_diff"]}'
    )

print("\nReports saved to:", outdir)
