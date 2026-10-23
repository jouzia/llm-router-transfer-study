import csv
import json
import tarfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "bench-release.tar.gz"
METADATA = ROOT / "day1_audit" / "all_result_metadata.csv"
OUT = ROOT / "day1_audit"
TARGETS = {
    "arenahard_coding",
    "arenahard_math",
    "arenahard_creative_writing",
}

with METADATA.open(newline="", encoding="utf-8-sig") as f:
    metadata = list(csv.DictReader(f))

selected = [
    r for r in metadata
    if r["dataset"].lower() in TARGETS and r["split"] == "test"
]

if len(selected) != 99:
    raise RuntimeError(f"Expected 99 result files; found {len(selected)}")

scores = defaultdict(dict)
audit = []
all_models = set()
archive_errors = []

with tarfile.open(ARCHIVE, mode="r:gz") as tar:
    members = {m.name: m for m in tar.getmembers() if m.isfile()}

    for row in selected:
        dataset = row["dataset"].lower()
        model = row["model"]
        member_name = row["archive_path"]

        if member_name not in members:
            archive_errors.append(f"Archive member missing: {member_name}")
            continue

        stream = tar.extractfile(members[member_name])
        if stream is None:
            archive_errors.append(f"Could not read: {member_name}")
            continue

        try:
            result = json.load(stream)
        except Exception as exc:
            archive_errors.append(f"JSON error in {member_name}: {exc}")
            continue

        records = result.get("records", [])
        seen = set()
        duplicates = []
        invalid_scores = []
        missing_scores = 0

        for record in records:
            idx = record.get("index")
            if idx is None:
                archive_errors.append(
                    f"Missing record index: {dataset} / {model}"
                )
                continue

            idx = str(idx)
            if idx in seen:
                duplicates.append(idx)
                continue
            seen.add(idx)

            raw_score = record.get("score")
            if isinstance(raw_score, bool) or not isinstance(raw_score, (int, float)):
                missing_scores += 1
                continue

            score = float(raw_score)
            if not 0.0 <= score <= 1.0:
                invalid_scores.append((idx, score))
                continue

            key = (dataset, idx)
            if model in scores[key]:
                archive_errors.append(
                    f"Duplicate model score: {dataset} / {idx} / {model}"
                )
            scores[key][model] = score

        all_models.add(model)
        audit.append({
            "dataset": dataset,
            "model": model,
            "record_count": len(records),
            "unique_indices": len(seen),
            "duplicate_indices": len(duplicates),
            "missing_or_non_numeric_scores": missing_scores,
            "out_of_range_scores": len(invalid_scores),
            "metadata_declared_count": row["records"],
        })

        if duplicates or invalid_scores:
            print("FLAG:", dataset, model,
                  "| duplicate indices:", duplicates[:5],
                  "| invalid scores:", invalid_scores[:5])

# Determine which models have a score for every index in each domain.
matrix_rows = []
domain_summary = []

for dataset in sorted(TARGETS):
    keys = sorted(
        [key for key in scores if key[0] == dataset],
        key=lambda key: (0, int(key[1])) if key[1].isdigit() else (1, key[1])
    )
    expected_indices = {key[1] for key in keys}

    complete_models = [
        model for model in sorted(all_models)
        if all(model in scores[key] for key in keys)
    ]

    domain_summary.append(
        f"{dataset}: indices={len(expected_indices)}, "
        f"complete_models={len(complete_models)}"
    )

    for key in keys:
        row = {"dataset": dataset, "index": key[1]}
        for model in sorted(all_models):
            row[model] = scores[key].get(model, "")
        matrix_rows.append(row)

matrix_path = OUT / "pilot_score_matrix.csv"
fieldnames = ["dataset", "index"] + sorted(all_models)

with matrix_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(matrix_rows)

audit_path = OUT / "pilot_matrix_audit.txt"
with audit_path.open("w", encoding="utf-8") as f:
    f.write(f"Selected result files: {len(selected)}\n")
    f.write(f"Distinct models: {len(all_models)}\n")
    f.write(f"Matrix rows: {len(matrix_rows)}\n\n")
    f.write("DOMAIN SUMMARY\n")
    f.write("\n".join(domain_summary) + "\n\n")
    f.write("FILE-LEVEL CHECKS\n")
    for item in audit:
        f.write(json.dumps(item, sort_keys=True) + "\n")
    f.write("\nARCHIVE ERRORS\n")
    f.write("\n".join(archive_errors) if archive_errors else "None")
    f.write("\n")

print("\n=== SCORE MATRIX BUILD COMPLETE ===")
print("Matrix:", matrix_path)
print("Audit:", audit_path)
print("Models:", len(all_models))
print("Rows:", len(matrix_rows))
print("\nDomain summary:")
for line in domain_summary:
    print(line)
print("Archive errors:", len(archive_errors))
print("Inspect audit:", audit_path)
