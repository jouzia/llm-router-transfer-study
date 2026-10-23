from pathlib import Path
import csv
from collections import defaultdict

path = (Path(__file__).resolve().parent / "day1_audit" / "all_result_metadata.csv")
targets = {
    "arenahard_coding",
    "arenahard_math",
    "arenahard_creative_writing",
}

with open(path, newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

selected = [
    r for r in rows
    if r["dataset"].lower() in targets
    and r["split"] == "test"
]

by_dataset = defaultdict(list)
for r in selected:
    by_dataset[r["dataset"].lower()].append(r)

for dataset in sorted(targets):
    items = by_dataset[dataset]
    models = {r["model"] for r in items}
    counts = {r["records"] for r in items}
    fingerprints = {r["fingerprint"] for r in items}
    signatures = {r["record_signature"] for r in items}

    print(f"\nDATASET: {dataset}")
    print("Result files:", len(items))
    print("Distinct models:", len(models))
    print("Record-count values:", counts)
    print("Fingerprint count:", len(fingerprints))
    print("Record-signature count:", len(signatures))

    mismatches = [
        r for r in items
        if r["performance"] != ""
        and r["mean_record_score"] != ""
        and abs(float(r["performance"]) -
                float(r["mean_record_score"])) > 1e-6
    ]
    print("Aggregate/mean score mismatches:", len(mismatches))
    for r in mismatches:
        print("  FLAG:", r["model"],
              "| aggregate:", r["performance"],
              "| record mean:", r["mean_record_score"])

if all(t in by_dataset for t in targets):
    common = set.intersection(*[
        {r["model"] for r in by_dataset[t]} for t in targets
    ])
    print("\nCOMMON MODELS ACROSS ALL THREE:", len(common))
    for model in sorted(common):
        print(" ", model)
