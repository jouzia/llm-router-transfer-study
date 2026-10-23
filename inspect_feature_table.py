import csv
from pathlib import Path
from collections import Counter

p = (Path(__file__).resolve().parent / "day1_audit" / "prompt_feature_score_table.csv")

with p.open(newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    columns = reader.fieldnames or []

print("Rows:", len(rows))
print("\nColumns:")
for col in columns:
    print(" ", col)

print("\nMissing values by column:")
for col in columns:
    missing = sum(
        row.get(col) is None or row.get(col, "").strip() == ""
        for row in rows
    )
    if missing:
        print(f"  {col}: {missing}")

print("\nDomain counts:")
for domain, count in sorted(
    Counter(row.get("dataset", "") for row in rows).items()
):
    print(f"  {domain}: {count}")

print("\nFirst row (truncated values):")
if rows:
    for key, value in rows[0].items():
        print(f"  {key}: {str(value)[:100]}")
