"""Day 14: verify official LLMRouterBench archive identity and OOD baseline inputs.

Uses only the Python standard library. Run from the repository root:
    python .\day1_audit\day14_release_ood_preflight.py

The script does not modify the archive or experiment outputs.
"""
from __future__ import annotations

import hashlib
import json
import re
import tarfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "bench-release.tar.gz"
REPORT = ROOT / "day1_audit" / "DAY14_RELEASE_OOD_PREFLIGHT.txt"
EXPECTED_SHA256 = "b79f8cde1a6f029c2efa663a3a3b6f7748defb22341fe59f328cebef6648c8f1"

CANDIDATES = [
    "claude-sonnet-4",
    "deepseek-r1-0528",
    "deepseek-v3.1-terminus",
    "deepseek-v3-0324",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "glm-4.6",
    "gpt-5",
    "gpt-5-chat",
    "intern-s1",
    "kimi-k2-0905",
    "qwen3-235b-a22b-2507",
    "qwen3-235b-a22b-thinking-2507",
]
SOURCE_DOMAINS = {
    "arenahard_coding": 253,
    "arenahard_creative_writing": 250,
    "arenahard_math": 247,
}
TARGETS = {
    ("gpqa", "test"): 198,
    ("mmlupro", "test_3000"): 3000,
}


def fail(message: str) -> None:
    raise SystemExit(f"INTEGRITY FAILURE: {message}")


def normalize(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", value).strip().casefold()


def prompt_text(record: dict) -> str:
    origin = record.get("origin_query")
    if isinstance(origin, str) and origin.strip():
        return origin
    return record.get("prompt", "")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_json_member(names: list[str], dataset: str, model: str, split: str | None = None) -> str:
    prefix = f"bench-release/{dataset}/"
    if split is not None:
        prefix += f"{split}/"
    matches = [
        name for name in names
        if name.lower().startswith(prefix.lower())
        and name.lower().endswith(".json")
        and name[len(prefix):].split("/", 1)[0].lower() == model.lower()
    ]
    if len(matches) != 1:
        fail(
            f"Expected one archive JSON for {dataset}/{split or '(no split)'}/{model}; "
            f"found {len(matches)}: {matches[:5]}"
        )
    return matches[0]


def read_payload(tar: tarfile.TarFile, member_name: str) -> dict:
    member = tar.getmember(member_name)
    stream = tar.extractfile(member)
    if stream is None:
        fail(f"Cannot read archive member: {member_name}")
    payload = json.load(stream)
    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
        fail(f"Invalid result payload/records list: {member_name}")
    return payload


def record_summary(payload: dict, expected_count: int, context: str) -> tuple[Counter, Counter, dict]:
    records = payload["records"]
    if len(records) != expected_count:
        fail(f"{context}: expected {expected_count} records; found {len(records)}")
    texts = []
    scored = []
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            fail(f"{context}: record {i} is not an object")
        text = normalize(prompt_text(record))
        if not text:
            fail(f"{context}: record {i} has no usable origin_query/prompt")
        texts.append(text)
        try:
            score = float(record["score"])
        except (KeyError, TypeError, ValueError):
            fail(f"{context}: record {i} has no numeric score")
        scored.append((text, score))
    metadata = {
        "dataset_name": payload.get("dataset_name"),
        "split": payload.get("split"),
        "model_name": payload.get("model_name"),
        "record_count": len(records),
        "unique_prompt_texts": len(set(texts)),
    }
    return Counter(texts), Counter(scored), metadata


def main() -> None:
    if not ARCHIVE.is_file():
        fail(f"Archive not found: {ARCHIVE}")

    actual_hash = sha256(ARCHIVE)
    if actual_hash.lower() != EXPECTED_SHA256:
        fail(
            "Archive SHA-256 does not match the official LLMRouterBench Hugging Face "
            f"release. expected={EXPECTED_SHA256}; actual={actual_hash}"
        )

    report = [
        "RESEARCH 3 — OFFICIAL RELEASE / OOD BASELINE PREFLIGHT",
        "=" * 68,
        "STATUS: PASS (archive identity and requested records)",
        f"Archive: {ARCHIVE}",
        f"Archive SHA-256: {actual_hash}",
        "Official LLMRouterBench archive identity: EXACT BYTE-FOR-BYTE MATCH",
        "",
    ]

    with tarfile.open(ARCHIVE, "r:gz") as tar:
        names = [
            member.name.lstrip("./")
            for member in tar.getmembers()
            if member.isfile() and member.name.lower().endswith(".json")
        ]
        names = sorted(names)

        source_dataset_ids = set()
        target_dataset_ids = set()
        source_split_values = set()
        target_split_values = set()
        source_texts_by_model = {model: Counter() for model in CANDIDATES}
        source_scores_by_model = {model: Counter() for model in CANDIDATES}
        aggregate_comparison = {}

        report.append("SOURCE PARTITIONS")
        for domain, count in SOURCE_DOMAINS.items():
            for model in CANDIDATES:
                member_name = find_json_member(names, domain, model)
                payload = read_payload(tar, member_name)
                texts, scores, metadata = record_summary(
                    payload, count, f"{domain}/{model}"
                )
                if metadata["model_name"] and metadata["model_name"].lower() != model.lower():
                    fail(f"{domain}/{model}: internal model_name mismatch: {metadata['model_name']}")
                source_dataset_ids.add(metadata["dataset_name"])
                source_split_values.add(metadata["split"])
                source_texts_by_model[model].update(texts)
                source_scores_by_model[model].update(scores)
            report.append(
                f"{domain}: {count} prompts; {len(CANDIDATES)} candidate-model files"
            )

        report.extend(["", "AGGREGATE ARENAHARD PROMPT ALIGNMENT"])
        for model in CANDIDATES:
            member_name = find_json_member(names, "arenahard", model)
            payload = read_payload(tar, member_name)
            texts, scores, metadata = record_summary(
                payload, sum(SOURCE_DOMAINS.values()), f"arenahard/{model}"
            )
            text_match = texts == source_texts_by_model[model]
            score_match = scores == source_scores_by_model[model]
            aggregate_comparison[model] = (text_match, score_match)
        text_matches = sum(v[0] for v in aggregate_comparison.values())
        score_matches = sum(v[1] for v in aggregate_comparison.values())
        report.append(
            f"Exact normalized prompt-multiset match: {text_matches}/{len(CANDIDATES)} models"
        )
        report.append(
            f"Exact (normalized prompt, score) multiset match: {score_matches}/{len(CANDIDATES)} models"
        )
        for model, (text_match, score_match) in aggregate_comparison.items():
            if not text_match or not score_match:
                report.append(
                    f"DIFFERENCE {model}: prompt_match={text_match}; score_match={score_match}"
                )

        report.extend(["", "HELD-OUT TARGET DATASETS"])
        for (dataset, split), count in TARGETS.items():
            observed_ids = set()
            observed_splits = set()
            for model in CANDIDATES:
                member_name = find_json_member(names, dataset, model, split)
                payload = read_payload(tar, member_name)
                _, _, metadata = record_summary(
                    payload, count, f"{dataset}/{split}/{model}"
                )
                if metadata["model_name"] and metadata["model_name"].lower() != model.lower():
                    fail(f"{dataset}/{model}: internal model_name mismatch: {metadata['model_name']}")
                observed_ids.add(metadata["dataset_name"])
                observed_splits.add(metadata["split"])
            if len(observed_ids) != 1 or None in observed_ids:
                fail(f"{dataset}: inconsistent internal dataset_name values: {observed_ids}")
            if len(observed_splits) != 1 or None in observed_splits:
                fail(f"{dataset}: inconsistent internal split values: {observed_splits}")
            target_dataset_ids.update(observed_ids)
            target_split_values.update(observed_splits)
            report.append(
                f"{dataset}/{split}: {count} prompts; {len(CANDIDATES)} candidate-model files; "
                f"internal dataset_name={next(iter(observed_ids))!r}; "
                f"internal split={next(iter(observed_splits))!r}"
            )

    source_dataset_ids.discard(None)
    if source_dataset_ids & target_dataset_ids:
        fail(
            "Internal source and target dataset_name values overlap; cannot safely use "
            f"dataset-level OOD split: overlap={sorted(source_dataset_ids & target_dataset_ids)}"
        )

    report.extend([
        "",
        "OOD SPLIT CONFIGURATION INPUTS",
        f"Source dataset_name values: {sorted(source_dataset_ids)}",
        f"Target dataset_name values: {sorted(target_dataset_ids)}",
        f"Source split values: {sorted(str(x) for x in source_split_values)}",
        f"Target split values: {sorted(str(x) for x in target_split_values)}",
        f"Proposed OOD dataset IDs: {sorted(str(x) for x in target_dataset_ids)}",
        "Dataset-level source/target separation: PASS",
        "Candidate pool: exact 13-model performance-cost pool membership",
        "",
        "INTERPRETATION",
        "- This script verifies the official archive hash and per-model record coverage.",
        "- The aggregate ArenaHard comparison reports whether the three source partitions",
        "  reproduce the aggregate prompt and score multisets for each candidate model.",
        "- The OOD split can be configured only if source and target internal dataset IDs",
        "  are disjoint, as checked above.",
        "- This is a data preflight, not an Avengers-Pro reproduction or performance result.",
        "",
    ])

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    print(f"Report: {REPORT}")


if __name__ == "__main__":
    main()
