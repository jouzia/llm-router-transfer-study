from pathlib import Path
import tarfile, json, csv, os, math
from collections import Counter

archive = (Path(__file__).resolve().parent / "bench-release.tar.gz")
report = (Path(__file__).resolve().parent / "day1_audit" / "record_quality_checks.csv")

with open(report, newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

targets = [
    r for r in rows
    if (r["score_diff"] and float(r["score_diff"]) > 1e-6)
    or (r["cost_diff"] and float(r["cost_diff"]) > 1e-6)
]

print("Files requiring metric investigation:", len(targets))

with tarfile.open(archive, "r:gz") as tar:
    for row in targets:
        member = tar.extractfile(row["archive_path"])
        if member is None:
            continue
        obj = json.load(member)
        records = obj.get("records") or []

        costs = [
            float(r["cost"]) for r in records
            if isinstance(r, dict)
            and isinstance(r.get("cost"), (int, float))
            and math.isfinite(float(r["cost"]))
        ]
        scores = [
            float(r["score"]) for r in records
            if isinstance(r, dict)
            and isinstance(r.get("score"), (int, float))
            and math.isfinite(float(r["score"]))
        ]

        missing_cost = sum(
            not isinstance(r, dict)
            or not isinstance(r.get("cost"), (int, float))
            for r in records
        )
        zero_cost = sum(c == 0 for c in costs)
        negative_cost = sum(c < 0 for c in costs)

        agg_cost = obj.get("cost")
        sum_cost = sum(costs) if costs else None
        cost_diff = abs(float(agg_cost) - sum_cost) if agg_cost is not None and sum_cost is not None else None

        agg_perf = obj.get("performance")
        mean_score = sum(scores) / len(scores) if scores else None
        score_diff = abs(float(agg_perf) - mean_score) if agg_perf is not None and mean_score is not None else None

        if (cost_diff is not None and cost_diff > 1e-6) or (score_diff is not None and score_diff > 1e-6):
            print("\n---", obj.get("dataset_name"), "|", obj.get("model_name"), "|", obj.get("split"), "---")
            print("Records:", len(records))
            print("Aggregate cost:", agg_cost)
            print("Sum of numeric record costs:", sum_cost)
            print("Absolute cost difference:", cost_diff)
            print("Records missing/non-numeric cost:", missing_cost)
            print("Zero-cost records:", zero_cost)
            print("Negative-cost records:", negative_cost)
            print("Aggregate performance:", agg_perf)
            print("Mean numeric record score:", mean_score)
            print("Absolute score difference:", score_diff)
            print("Time taken:", obj.get("time_taken"))

print("\nDiagnostics complete.")
