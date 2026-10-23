from pathlib import Path
import tarfile, json, hashlib, csv, os, statistics
from collections import defaultdict

archive = (Path(__file__).resolve().parent / "bench-release.tar.gz")
outdir = (Path(__file__).resolve().parent / "day1_audit")
os.makedirs(outdir, exist_ok=True)

rows = []
errors = []
pair_groups = defaultdict(list)

def record_signature(records):
    normalized = []
    for r in records:
        normalized.append((
            str(r.get("index", "")),
            str(r.get("origin_query", r.get("prompt", ""))),
            json.dumps(r.get("ground_truth"), sort_keys=True, ensure_ascii=False)
        ))
    normalized.sort(key=lambda x: x[0])
    payload = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

print("Scanning archive once; this may take a little while...")

with tarfile.open(archive, "r:gz") as tar:
    for member in tar:
        if not member.isfile() or not member.name.endswith(".json"):
            continue
        try:
            f = tar.extractfile(member)
            if f is None:
                raise ValueError("Unable to read archive member")
            obj = json.load(f)

            records = obj.get("records") or []
            dataset = str(obj.get("dataset_name") or member.name.split("/")[1])
            model = str(obj.get("model_name") or "")
            split = str(obj.get("split") or "")
            fingerprint = str(obj.get("data_fingerprint") or "")
            demo = str(obj.get("demo", ""))
            signature = record_signature(records) if records else ""

            scores = [
                float(r["score"]) for r in records
                if isinstance(r, dict) and isinstance(r.get("score"), (int, float))
            ]
            record_costs = [
                float(r["cost"]) for r in records
                if isinstance(r, dict) and isinstance(r.get("cost"), (int, float))
            ]

            row = {
                "dataset": dataset,
                "model": model,
                "split": split,
                "demo": demo,
                "fingerprint": fingerprint,
                "records": len(records),
                "declared_count": obj.get("counts"),
                "performance": obj.get("performance"),
                "mean_record_score": statistics.mean(scores) if scores else None,
                "time_taken": obj.get("time_taken"),
                "prompt_tokens": obj.get("prompt_tokens"),
                "completion_tokens": obj.get("completion_tokens"),
                "aggregate_cost": obj.get("cost"),
                "sum_record_cost": sum(record_costs) if record_costs else None,
                "record_signature": signature,
                "archive_path": member.name
            }
            rows.append(row)

            if fingerprint and signature and model:
                key = (dataset, fingerprint, split, demo)
                pair_groups[key].append(row)

        except Exception as e:
            errors.append({"archive_path": member.name, "error": str(e)})

def write_csv(path, data):
    if not data:
        return
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        w.writeheader()
        w.writerows(data)

write_csv(os.path.join(outdir, "all_result_metadata.csv"), rows)
write_csv(os.path.join(outdir, "parse_errors.csv"), errors)

coverage = defaultdict(list)
for r in rows:
    coverage[r["dataset"]].append(r)

coverage_rows = []
for dataset, items in sorted(coverage.items()):
    models = sorted(set(r["model"] for r in items if r["model"]))
    valid_fps = len(set(r["fingerprint"] for r in items if r["fingerprint"]))
    groups = [
        (key, group) for key, group in pair_groups.items()
        if key[0] == dataset
    ]
    multi_groups = [(key, g) for key, g in groups if len(g) >= 2]
    largest = max((len(set(x["model"] for x in g)) for _, g in multi_groups), default=0)
    coverage_rows.append({
        "dataset": dataset,
        "result_files": len(items),
        "unique_models": len(models),
        "fingerprint_variants": valid_fps,
        "groups_with_2plus_results": len(multi_groups),
        "largest_models_per_matching_group": largest,
        "files_missing_fingerprint": sum(not r["fingerprint"] for r in items),
        "files_missing_records": sum(r["records"] == 0 for r in items)
    })

write_csv(os.path.join(outdir, "dataset_coverage.csv"), coverage_rows)

compat_rows = []
for (dataset, fingerprint, split, demo), group in sorted(pair_groups.items()):
    by_signature = defaultdict(list)
    for r in group:
        by_signature[r["record_signature"]].append(r)

    for signature, compatible in by_signature.items():
        if len(compatible) < 2:
            continue
        compatible_models = sorted(set(r["model"] for r in compatible))
        compat_rows.append({
            "dataset": dataset,
            "split": split,
            "demo": demo,
            "fingerprint": fingerprint,
            "record_signature": signature,
            "matching_files": len(compatible),
            "matching_models": len(compatible_models),
            "models": "; ".join(compatible_models),
            "records_per_file": min(r["records"] for r in compatible),
            "performance_range": (
                max(float(r["performance"]) for r in compatible if r["performance"] is not None)
                - min(float(r["performance"]) for r in compatible if r["performance"] is not None)
                if all(r["performance"] is not None for r in compatible) else None
            )
        })

write_csv(os.path.join(outdir, "compatible_model_groups.csv"), compat_rows)

print("\n=== AUDIT SUMMARY ===")
print("JSON files parsed:", len(rows))
print("JSON files with errors:", len(errors))
print("Datasets found:", len(coverage_rows))
print("Compatible model groups:", len(compat_rows))
print("Output folder:", outdir)

print("\n=== DATASET COVERAGE ===")
for r in sorted(coverage_rows, key=lambda x: (-x["largest_models_per_matching_group"], x["dataset"])):
    print(
        f'{r["dataset"]}: files={r["result_files"]}, '
        f'models={r["unique_models"]}, '
        f'largest_verified_group={r["largest_models_per_matching_group"]}, '
        f'multi-model_groups={r["groups_with_2plus_results"]}'
    )

print("\n=== TOP VERIFIED COMPARISON GROUPS ===")
for r in sorted(compat_rows, key=lambda x: (-x["matching_models"], -x["records_per_file"]))[:15]:
    print(
        f'{r["dataset"]} | split={r["split"]} | '
        f'models={r["matching_models"]} | records={r["records_per_file"]}'
    )

print("\nAudit finished.")
