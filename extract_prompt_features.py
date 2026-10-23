import csv
import json
import re
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "bench-release.tar.gz"
META = ROOT / "day1_audit" / "all_result_metadata.csv"
MATRIX = ROOT / "day1_audit" / "pilot_score_matrix.csv"
OUT = ROOT / "day1_audit" / "prompt_feature_score_table.csv"
REPORT = ROOT / "day1_audit" / "prompt_feature_extraction_audit.txt"

DOMAINS = {
    "arenahard_coding",
    "arenahard_creative_writing",
    "arenahard_math",
}

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
        "contains_code_fence": int("```" in text),
        "contains_url": int(bool(re.search(r"https?://|www\.", text))),
        "contains_equation_symbol": int(bool(re.search(r"[=+\-*/^]", text))),
        "contains_question_word": int(bool(re.search(
            r"\b(what|why|how|when|where|which|who|explain|compare)\b",
            text, re.I
        ))),
    }

for p in (ARCHIVE, META, MATRIX):
    if not p.is_file():
        raise SystemExit(f"ERROR: required file missing: {p}")

with META.open(newline="", encoding="utf-8-sig") as f:
    metadata = list(csv.DictReader(f))

with MATRIX.open(newline="", encoding="utf-8-sig") as f:
    matrix = list(csv.DictReader(f))

matrix_by_key = {
    (r["dataset"], str(r["index"])): r
    for r in matrix
}
selected = [
    r for r in metadata
    if r.get("dataset", "").lower() in DOMAINS
    and r.get("split") == "test"
    and r.get("demo", "").lower() == "false"
]

if len(selected) != 99:
    raise SystemExit(
        f"STOP: expected 99 selected result files, found {len(selected)}."
    )

audit = []
records_by_domain = defaultdict(dict)
score_checks = []
archive_errors = []
model_names_by_domain = defaultdict(set)

with tarfile.open(ARCHIVE, "r:gz") as tar:
    members = {m.name.lstrip("./"): m for m in tar.getmembers() if m.isfile()}

    for meta in selected:
        dataset = meta["dataset"]
        model = meta["model"]
        member_name = meta["archive_path"].lstrip("./")

        member = members.get(member_name)
        if member is None:
            archive_errors.append(
                f"Archive member not found: {member_name}"
            )
            continue

        try:
            handle = tar.extractfile(member)
            if handle is None:
                raise ValueError("Unable to read archive member")
            payload = json.load(handle)
            records = payload.get("records", [])
        except Exception as exc:
            archive_errors.append(f"{member_name}: {type(exc).__name__}: {exc}")
            continue

        model_names_by_domain[dataset].add(model)

        for rec in records:
            idx = str(rec.get("index", ""))
            if not idx:
                archive_errors.append(
                    f"Missing record index: {member_name}"
                )
                continue

            key = (dataset, idx)
            origin = rec.get("origin_query")
            prompt = rec.get("prompt")
            text = origin if isinstance(origin, str) and origin.strip() else prompt

            if not isinstance(text, str) or not text.strip():
                archive_errors.append(
                    f"No usable prompt text: {dataset}, {model}, index={idx}"
                )
                continue

            item = records_by_domain[dataset].setdefault(
                idx, {"texts": {}, "scores": {}, "ground_truths": {}}
            )
            item["texts"][model] = text
            item["scores"][model] = rec.get("score")
            if "ground_truth" in rec:
                item["ground_truths"][model] = rec.get("ground_truth")

            matrix_row = matrix_by_key.get(key)
            if matrix_row is None:
                score_checks.append(
                    f"No matrix row for {dataset}, index={idx}"
                )
            elif model not in matrix_row:
                score_checks.append(
                    f"Model column missing: {dataset}, {model}"
                )
            else:
                try:
                    archived_score = float(rec["score"])
                    matrix_score = float(matrix_row[model])
                    if abs(archived_score - matrix_score) > 1e-9:
                        score_checks.append(
                            f"Score mismatch: {dataset}, {model}, index={idx}"
                        )
                except (KeyError, TypeError, ValueError):
                    score_checks.append(
                        f"Invalid score: {dataset}, {model}, index={idx}"
                    )

rows_out = []
prompt_mismatches = []
ground_truth_mismatches = []
missing_model_records = []

for dataset in sorted(DOMAINS):
    expected_models = model_names_by_domain[dataset]

    for idx, item in sorted(
        records_by_domain[dataset].items(),
        key=lambda kv: int(kv[0]) if kv[0].isdigit() else kv[0]
    ):
        texts = item["texts"]
        if len(texts) != len(expected_models):
            missing_model_records.append(
                f"{dataset}, index={idx}: "
                f"{len(texts)}/{len(expected_models)} model prompts"
            )

        distinct_texts = set(texts.values())
        if len(distinct_texts) != 1:
            prompt_mismatches.append(
                f"{dataset}, index={idx}: {len(distinct_texts)} "
                "distinct text versions"
            )

        truths = [
            json.dumps(v, sort_keys=True, ensure_ascii=False)
            for v in item["ground_truths"].values()
        ]
        if truths and len(set(truths)) != 1:
            ground_truth_mismatches.append(
                f"{dataset}, index={idx}: ground truth differs across models"
            )

        # Do not silently select one version when model prompts disagree.
        # Use only verified-consistent prompt text for feature generation.
        if len(distinct_texts) != 1:
            continue

        text = next(iter(distinct_texts))
        features = feature_row(text)
        row = {
            "dataset": dataset,
            "index": idx,
            "prompt_text_source": "origin_query when available, otherwise prompt",
            **features,
        }

        matrix_row = matrix_by_key.get((dataset, idx))
        if matrix_row is None:
            continue

        for model in sorted(expected_models):
            if model not in matrix_row or model not in item["scores"]:
                row[model] = ""
            else:
                row[model] = matrix_row[model]

        rows_out.append(row)

feature_names = [
    "char_count", "word_count", "line_count", "digit_count",
    "question_mark_count", "exclamation_count", "code_symbol_count",
    "contains_code_fence", "contains_url", "contains_equation_symbol",
    "contains_question_word",
]
model_columns = sorted({
    model
    for models in model_names_by_domain.values()
    for model in models
})
fieldnames = [
    "dataset", "index", "prompt_text_source",
    *feature_names, *model_columns
]

with OUT.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows_out)

audit.extend([
    "RESEARCH 3 — PROMPT FEATURE EXTRACTION AUDIT",
    "=" * 55,
    f"Selected metadata files: {len(selected)}",
    f"Output rows with consistent prompt text: {len(rows_out)}",
    f"Feature columns: {len(feature_names)}",
    f"Archive errors: {len(archive_errors)}",
    f"Prompt-text mismatches: {len(prompt_mismatches)}",
    f"Ground-truth mismatches: {len(ground_truth_mismatches)}",
    f"Missing model records: {len(missing_model_records)}",
    f"Score alignment issues: {len(score_checks)}",
    "",
    "DOMAIN COVERAGE:"
])

for dataset in sorted(DOMAINS):
    audit.append(
        f"{dataset}: {len(records_by_domain[dataset])} distinct indices; "
        f"{len(model_names_by_domain[dataset])} models"
    )

for title, issues in [
    ("ARCHIVE ERRORS", archive_errors),
    ("PROMPT-TEXT MISMATCHES", prompt_mismatches),
    ("GROUND-TRUTH MISMATCHES", ground_truth_mismatches),
    ("MISSING MODEL RECORDS", missing_model_records),
    ("SCORE ALIGNMENT ISSUES", score_checks),
]:
    audit.extend(["", title])
    audit.extend(issues[:20] if issues else ["None"])

if prompt_mismatches or archive_errors or score_checks:
    audit.extend([
        "",
        "CAUTION: Resolve the reported issues before using this table "
        "for routing experiments."
    ])

REPORT.write_text("\n".join(audit) + "\n", encoding="utf-8")
print("\n".join(audit))
print(f"\nFeature table: {OUT}")
print(f"Audit report: {REPORT}")
