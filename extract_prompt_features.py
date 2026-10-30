import csv
import json
import math
import re
import tarfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "bench-release.tar.gz"
AUDIT_DIR = ROOT / "day1_audit"
META = AUDIT_DIR / "all_result_metadata.csv"
MATRIX = AUDIT_DIR / "pilot_score_matrix.csv"
OUT = AUDIT_DIR / "prompt_feature_score_table.csv"
REPORT = AUDIT_DIR / "prompt_feature_extraction_audit.txt"

DOMAINS = {
    "arenahard_coding": 253,
    "arenahard_creative_writing": 250,
    "arenahard_math": 247,
}
EXPECTED_MODELS = 33
SCORE_TOLERANCE = 1e-9
FEATURE_NAMES = [
    "char_count", "word_count", "line_count", "digit_count",
    "question_mark_count", "exclamation_count", "code_symbol_count",
    "contains_code_fence", "contains_url", "contains_equation_symbol",
    "contains_question_word",
]


def feature_row(text):
    text = text or ""
    words = re.findall(r"\b[\w']+\b", text)
    lines = text.splitlines()
    return {
        "char_count": len(text),
        "word_count": len(words),
        "line_count": len(lines),
        "digit_count": sum(c.isdigit() for c in text),
        "question_mark_count": text.count("?"),
        "exclamation_count": text.count("!"),
        "code_symbol_count": sum(text.count(c) for c in "{}[]();<>"),
        "contains_code_fence": int("\u0060\u0060\u0060" in text),
        "contains_url": int(bool(re.search(r"https?://|www\.", text))),
        "contains_equation_symbol": int(bool(re.search(r"[=+\-*/^]", text))),
        "contains_question_word": int(bool(re.search(
            r"\b(what|why|how|when|where|which|who|explain|compare)\b",
            text, re.I
        ))),
    }


def stop(message):
    raise SystemExit("INTEGRITY FAILURE: " + message)


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            stop(f"{path.name}: missing CSV header")
        return reader.fieldnames, list(reader)


def duplicate_keys(rows, key_fn):
    counts = Counter(key_fn(row) for row in rows)
    return {key: count for key, count in counts.items() if count > 1}


def numeric_score(value, context):
    try:
        score = float(value)
    except (TypeError, ValueError):
        stop(f"Missing or non-numeric score ({context}): {value!r}")
    if not math.isfinite(score):
        stop(f"Non-finite score ({context}): {value!r}")
    return score


def main():
    for required in (ARCHIVE, META, MATRIX):
        if not required.is_file():
            stop(f"Required input file missing: {required}")

    meta_header, metadata = read_csv(META)
    matrix_header, matrix = read_csv(MATRIX)

    required_meta = {"dataset", "model", "split", "demo", "archive_path"}
    if not required_meta.issubset(meta_header):
        stop(f"Metadata missing columns: {sorted(required_meta - set(meta_header))}")
    if not {"dataset", "index"}.issubset(matrix_header):
        stop("Score matrix must contain dataset and index columns")

    meta_dupes = duplicate_keys(
        metadata,
        lambda r: (r["dataset"], r["model"], r["split"], r["demo"])
    )
    if meta_dupes:
        key, count = next(iter(meta_dupes.items()))
        stop(f"Duplicate metadata key {key!r} occurs {count} times")

    matrix_dupes = duplicate_keys(
        matrix, lambda r: (r["dataset"], str(r["index"]))
    )
    if matrix_dupes:
        key, count = next(iter(matrix_dupes.items()))
        stop(f"Duplicate score-matrix key {key!r} occurs {count} times")

    matrix_models = [c for c in matrix_header if c not in {"dataset", "index"}]
    if len(matrix_models) != EXPECTED_MODELS or len(set(matrix_models)) != EXPECTED_MODELS:
        stop(f"Expected exactly {EXPECTED_MODELS} unique model columns; found {len(matrix_models)}")

    matrix_by_key = {}
    matrix_score_distribution = Counter()
    for row in matrix:
        dataset, idx = row["dataset"], str(row["index"]).strip()
        if dataset not in DOMAINS:
            stop(f"Unexpected dataset in score matrix: {dataset!r}")
        if not idx:
            stop(f"Blank prompt index in score matrix for {dataset}")
        key = (dataset, idx)
        matrix_by_key[key] = row
        for model in matrix_models:
            matrix_score_distribution[numeric_score(
                row.get(model), f"matrix {dataset}/{model}/{idx}"
            )] += 1

    selected = [
        r for r in metadata
        if r["dataset"].strip().lower() in DOMAINS
        and r["split"].strip().lower() == "test"
        and str(r["demo"]).strip().lower() == "false"
    ]
    if len(selected) != len(DOMAINS) * EXPECTED_MODELS:
        stop(f"Expected {len(DOMAINS) * EXPECTED_MODELS} selected source files; found {len(selected)}")

    models_by_domain = {}
    archive_paths = set()
    for domain in DOMAINS:
        domain_rows = [r for r in selected if r["dataset"] == domain]
        models = [r["model"] for r in domain_rows]
        if len(models) != EXPECTED_MODELS or len(set(models)) != EXPECTED_MODELS:
            stop(f"{domain}: expected {EXPECTED_MODELS} distinct model files; found {len(set(models))}")
        models_by_domain[domain] = set(models)
        if set(models) != set(matrix_models):
            missing = sorted(set(matrix_models) - set(models))
            extra = sorted(set(models) - set(matrix_models))
            stop(f"{domain}: metadata/model-matrix pool mismatch; missing={missing}, extra={extra}")
        for row in domain_rows:
            path = row["archive_path"].strip().lstrip("./")
            if not path:
                stop(f"Blank archive_path for {domain}/{row['model']}")
            if path in archive_paths:
                stop(f"Archive member referenced more than once: {path}")
            archive_paths.add(path)

    expected_keys_by_domain = {}
    for domain, expected_count in DOMAINS.items():
        indices = {idx for ds, idx in matrix_by_key if ds == domain}
        if len(indices) != expected_count:
            stop(f"{domain}: expected {expected_count} distinct matrix prompts; found {len(indices)}")
        expected_keys_by_domain[domain] = indices

    if len(matrix_by_key) != sum(DOMAINS.values()):
        stop("Score matrix contains missing or unexpected source-domain keys")
    if len(matrix) != sum(DOMAINS.values()):
        stop(f"Expected {sum(DOMAINS.values())} score-matrix rows; found {len(matrix)}")

    records_by_domain = {domain: {} for domain in DOMAINS}
    archive_score_distribution = Counter()
    ground_truth_present = 0
    ground_truth_missing = 0
    prompt_text_mismatches = []
    ground_truth_mismatches = []
    score_mismatches = []
    archive_record_counts = Counter()

    with tarfile.open(ARCHIVE, "r:gz") as tar:
        members = {
            member.name.lstrip("./"): member
            for member in tar.getmembers() if member.isfile()
        }
        for meta_row in selected:
            dataset = meta_row["dataset"]
            model = meta_row["model"]
            member_name = meta_row["archive_path"].strip().lstrip("./")
            member = members.get(member_name)
            if member is None:
                stop(f"Archive member not found: {member_name} ({dataset}/{model})")
            handle = tar.extractfile(member)
            if handle is None:
                stop(f"Unable to read archive member: {member_name}")
            try:
                payload = json.load(handle)
            except Exception as exc:
                stop(f"Invalid JSON in {member_name}: {type(exc).__name__}: {exc}")
            records = payload.get("records") if isinstance(payload, dict) else None
            if not isinstance(records, list):
                stop(f"{member_name}: payload.records must be a list")

            seen_indices = set()
            for rec in records:
                if not isinstance(rec, dict):
                    stop(f"Malformed record in {dataset}/{model}: expected object")
                idx = str(rec.get("index", "")).strip()
                if not idx:
                    stop(f"Missing index in {dataset}/{model}")
                if idx in seen_indices:
                    stop(f"Duplicate prompt index within archive file: {dataset}/{model}/{idx}")
                seen_indices.add(idx)

                item = records_by_domain[dataset].setdefault(
                    idx, {"texts": {}, "scores": {}, "ground_truths": {}, "seen": set()}
                )
                archive_key = (dataset, model, idx)
                if archive_key in item["seen"] or model in item["scores"]:
                    stop(f"Duplicate archive record across inputs: {dataset}/{model}/{idx}")
                item["seen"].add(archive_key)

                origin = rec.get("origin_query")
                prompt = rec.get("prompt")
                prompt_text = origin if isinstance(origin, str) and origin.strip() else prompt
                if not isinstance(prompt_text, str) or not prompt_text.strip():
                    stop(f"Missing usable prompt text: {dataset}/{model}/{idx}")

                score = numeric_score(rec.get("score"), f"archive {dataset}/{model}/{idx}")
                archive_score_distribution[score] += 1
                archive_record_counts[(dataset, model)] += 1

                matrix_row = matrix_by_key.get((dataset, idx))
                if matrix_row is None:
                    stop(f"Missing matrix row for archive record: {dataset}/{model}/{idx}")
                matrix_score = numeric_score(
                    matrix_row.get(model), f"matrix {dataset}/{model}/{idx}"
                )
                if not math.isclose(score, matrix_score, rel_tol=0.0, abs_tol=SCORE_TOLERANCE):
                    score_mismatches.append(
                        f"{dataset}/{model}/{idx}: archive={score}, matrix={matrix_score}"
                    )

                item["texts"][model] = prompt_text
                item["scores"][model] = score
                if "ground_truth" in rec and rec.get("ground_truth") is not None:
                    item["ground_truths"][model] = rec.get("ground_truth")
                    ground_truth_present += 1
                else:
                    ground_truth_missing += 1

            if seen_indices != expected_keys_by_domain[dataset]:
                missing = sorted(expected_keys_by_domain[dataset] - seen_indices)
                extra = sorted(seen_indices - expected_keys_by_domain[dataset])
                stop(
                    f"{dataset}/{model}: archive prompt coverage mismatch; "
                    f"missing={missing[:10]}, extra={extra[:10]}"
                )

    if score_mismatches:
        stop("Archive/matrix score mismatches:\n" + "\n".join(score_mismatches[:20]))

    rows_out = []
    for dataset, expected_count in DOMAINS.items():
        domain_items = records_by_domain[dataset]
        if len(domain_items) != expected_count:
            stop(f"{dataset}: expected {expected_count} archive prompt keys; found {len(domain_items)}")
        expected_models = models_by_domain[dataset]
        for idx in sorted(domain_items, key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else x)):
            item = domain_items[idx]
            observed_models = set(item["scores"])
            if observed_models != expected_models:
                missing = sorted(expected_models - observed_models)
                extra = sorted(observed_models - expected_models)
                stop(f"Missing/unexpected model records at {dataset}/{idx}; missing={missing}, extra={extra}")

            distinct_texts = set(item["texts"].values())
            if len(distinct_texts) != 1:
                prompt_text_mismatches.append(f"{dataset}/{idx}: {len(distinct_texts)} text variants")
                continue

            truths = {
                json.dumps(value, sort_keys=True, ensure_ascii=False)
                for value in item["ground_truths"].values()
            }
            if len(truths) > 1:
                ground_truth_mismatches.append(f"{dataset}/{idx}: ground truth differs across models")

            prompt_text = next(iter(distinct_texts))
            row = {
                "dataset": dataset,
                "index": idx,
                "prompt_text_source": "origin_query when available, otherwise prompt",
                **feature_row(prompt_text),
            }
            matrix_row = matrix_by_key[(dataset, idx)]
            for model in matrix_models:
                row[model] = matrix_row[model]
            rows_out.append(row)

    if prompt_text_mismatches:
        stop("Prompt text disagreement across models:\n" + "\n".join(prompt_text_mismatches[:20]))
    if ground_truth_mismatches:
        stop("Ground-truth disagreement across models:\n" + "\n".join(ground_truth_mismatches[:20]))

    expected_header = ["dataset", "index", "prompt_text_source", *FEATURE_NAMES, *matrix_models]
    if len(rows_out) != sum(DOMAINS.values()):
        stop(f"Expected 750 output rows; found {len(rows_out)}")
    if len({(r["dataset"], r["index"]) for r in rows_out}) != len(rows_out):
        stop("Generated feature table contains duplicate (dataset, index) keys")

    experiment_scripts = [
        AUDIT_DIR / name for name in (
            "day4_gpqa_transfer.py", "day5_mmlupro_transfer.py",
            "day6_fair_baseline_transfer.py", "day7_repeated_split_robustness.py",
            "day8_gpqa_repeated_splits.py",
        )
    ]
    for script in experiment_scripts:
        if script.is_file():
            source = script.read_text(encoding="utf-8-sig")
            match = re.search(r"FEATURES\s*=\s*\[(.*?)\]", source, re.S)
            if not match:
                stop(f"Cannot locate FEATURES list in {script.name}")
            parsed = re.findall(r"""["']([^"']+)["']""", match.group(1))
            if parsed != FEATURE_NAMES:
                stop(f"{script.name} FEATURES order differs from extractor: {parsed}")

    old_rows, old_header, backup = [], None, None
    if OUT.is_file():
        old_header, old_rows = read_csv(OUT)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = OUT.with_name(f"{OUT.stem}.pre_integrity_{stamp}{OUT.suffix}")
        backup.write_bytes(OUT.read_bytes())

    old_by_key = {(r.get("dataset", ""), str(r.get("index", ""))): r for r in old_rows}
    new_by_key = {(r["dataset"], r["index"]): r for r in rows_out}
    old_keys, new_keys = set(old_by_key), set(new_by_key)
    common_keys = old_keys & new_keys
    old_duplicate_count = len(old_rows) - len(old_keys)
    compare_columns = [c for c in expected_header if old_header and c in old_header]
    changed_cells = [
        (key, column)
        for key in common_keys
        for column in compare_columns
        if str(old_by_key[key].get(column, "")) != str(new_by_key[key].get(column, ""))
    ]

    temp_out = OUT.with_suffix(OUT.suffix + ".tmp")
    with temp_out.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=expected_header)
        writer.writeheader()
        writer.writerows(rows_out)
    temp_out.replace(OUT)

    total_records = sum(archive_record_counts.values())
    report = [
        "RESEARCH 3 — PROMPT FEATURE EXTRACTION INTEGRITY AUDIT",
        "=" * 64,
        "STATUS: PASS",
        f"Selected source metadata files: {len(selected)} (expected 99)",
        "Duplicate metadata keys (dataset, model, split, demo): 0",
        "Duplicate score-matrix keys (dataset, index): 0",
        f"Archive members referenced uniquely: {len(archive_paths)}",
        f"Archive records checked: {total_records}",
        "Duplicate prompt indices within an archive file: 0",
        "Duplicate (dataset, model, index) archive records: 0",
        "Missing/unexpected model records: 0",
        "Missing/non-finite scores: 0",
        f"Archive/matrix score mismatches: {len(score_mismatches)}",
        f"Prompt-text mismatches across models: {len(prompt_text_mismatches)}",
        f"Ground-truth mismatches across models: {len(ground_truth_mismatches)}",
        f"Ground-truth present records: {ground_truth_present}",
        f"Ground-truth missing records: {ground_truth_missing}",
        f"Ground-truth coverage: {ground_truth_present / total_records:.6%}",
        f"Score matrix rows: {len(matrix)}",
        f"Feature table rows: {len(rows_out)}",
        f"Feature definitions: {len(FEATURE_NAMES)} (original ordered definitions retained)",
        f"Feature table columns: {len(expected_header)}",
        "",
        "DOMAIN COVERAGE:",
    ]
    for domain, expected_count in DOMAINS.items():
        report.append(
            f"{domain}: {len(records_by_domain[domain])} unique prompts; "
            f"{len(models_by_domain[domain])} models; expected prompts={expected_count}"
        )
    report.extend(["", "ARCHIVE SCORE DISTRIBUTION (all model-record scores):"])
    for score, count in sorted(archive_score_distribution.items()):
        report.append(f"{score:g}: {count}")
    report.extend(["", "MATRIX SCORE DISTRIBUTION (all model-record scores):"])
    for score, count in sorted(matrix_score_distribution.items()):
        report.append(f"{score:g}: {count}")
    identical = (
        old_header == expected_header
        and old_duplicate_count == 0
        and old_keys == new_keys
        and not changed_cells
        and len(old_rows) == len(rows_out)
    )
    report.extend([
        "",
        "OLD-TO-NEW FEATURE TABLE COMPARISON:",
        f"Previous rows: {len(old_rows)}",
        f"Previous unique keys: {len(old_keys)}",
        f"Previous duplicate keys: {old_duplicate_count}",
        f"New rows: {len(rows_out)}",
        f"New unique keys: {len(new_keys)}",
        f"Keys only in previous table: {len(old_keys - new_keys)}",
        f"Keys only in regenerated table: {len(new_keys - old_keys)}",
        f"Changed cell values among common keys/columns: {len(changed_cells)}",
        f"Previous header exactly matches regenerated header: {old_header == expected_header if old_header is not None else 'no previous table'}",
        f"Previous table identical to regenerated table: {identical if old_header is not None else 'no previous table'}",
        f"Previous table backup: {backup if backup else 'not applicable'}",
        "",
        "EXPERIMENT FEATURE-ORDER CHECK:",
        "All available Day 4–8 FEATURES lists match the extractor's 11 ordered feature names.",
        "",
        "No score values were binarized, rounded, or silently discarded.",
    ])
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    print(f"\nFeature table: {OUT}")
    print(f"Audit report: {REPORT}")


if __name__ == "__main__":
    main()
