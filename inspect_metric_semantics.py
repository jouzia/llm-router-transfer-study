from pathlib import Path
import csv
from collections import defaultdict

path = (Path(__file__).resolve().parent / "day1_audit" / "all_result_metadata.csv")

with open(path, newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

print("Columns:", list(rows[0]) if rows else "NO ROWS")

groups = defaultdict(list)
for row in rows:
    groups[row["model"]].append(row)

print("Distinct models:", len(groups))
print("Models with multiple result files:",
      sum(len(items) > 1 for items in groups.values()))

for model, items in list(groups.items())[:6]:
    print(f"\nMODEL: {model}")
    for row in items[:6]:
        print(
            " dataset=", row["dataset"],
            "| split=", row["split"],
            "| performance=", row["performance"],
            "| time_taken=", row["time_taken"],
            "| aggregate_cost=", row["aggregate_cost"],
            "| sum_record_cost=", row["sum_record_cost"]
        )

print("\n=== Models with repeated aggregate cost/time across datasets ===")
for model, items in groups.items():
    if len(items) < 2:
        continue
    costs = {r["aggregate_cost"] for r in items}
    times = {r["time_taken"] for r in items}
    if len(costs) == 1 or len(times) == 1:
        print(
            model,
            "| files=", len(items),
            "| unique aggregate costs=", len(costs),
            "| unique time values=", len(times)
        )
