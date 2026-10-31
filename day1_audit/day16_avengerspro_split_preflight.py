#!/usr/bin/env python3
"""Offline integrity preflight for prepared Avengers-Pro train/test JSONL files.

This checks split membership, prompt isolation, and complete candidate-score
coverage. It does not fit a router, load target labels into a model, or call
any embedding/API service.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

SOURCE_DATASETS = {
    "arenahard_coding",
    "arenahard_creative_writing",
    "arenahard_math",
}
OOD_DATASETS = {"gpqa", "mmlupro"}
EXPECTED_MODELS = {
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
}


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: row must be an object")
            rows.append(row)
    return rows


def validate_rows(rows: list[dict], split_name: str) -> Counter:
    counts = Counter()
    seen = set()
    for index, row in enumerate(rows, 1):
        dataset = row.get("dataset")
        query = row.get("query")
        records = row.get("records")
        if not isinstance(dataset, str) or not dataset:
            raise ValueError(f"{split_name} row {index}: missing dataset")
        if not isinstance(query, str) or not query.strip():
            raise ValueError(f"{split_name} row {index}: missing query")
        if not isinstance(records, dict):
            raise ValueError(f"{split_name} row {index}: records must be an object")
        key = (dataset, query)
        if key in seen:
            raise ValueError(f"{split_name}: duplicate prompt row for {dataset!r}")
        seen.add(key)
        actual_models = set(records)
        if actual_models != EXPECTED_MODELS:
            missing = sorted(EXPECTED_MODELS - actual_models)
            extra = sorted(actual_models - EXPECTED_MODELS)
            raise ValueError(
                f"{split_name} row {index} ({dataset}): candidate pool mismatch; "
                f"missing={missing}, extra={extra}"
            )
        for model, score in records.items():
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                raise ValueError(
                    f"{split_name} row {index}: non-numeric score for {model}"
                )
        counts[dataset] += 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", required=True, type=Path)
    parser.add_argument("--test", required=True, type=Path)
    args = parser.parse_args()

    train = load_jsonl(args.train)
    test = load_jsonl(args.test)
    train_counts = validate_rows(train, "train")
    test_counts = validate_rows(test, "test")

    train_datasets = set(train_counts)
    test_datasets = set(test_counts)
    if not train_datasets or not train_datasets <= SOURCE_DATASETS:
        raise ValueError(f"train contains non-source or unknown datasets: {sorted(train_datasets - SOURCE_DATASETS)}")
    if not OOD_DATASETS <= test_datasets:
        raise ValueError(f"test is missing required OOD datasets: {sorted(OOD_DATASETS - test_datasets)}")
    if train_datasets & OOD_DATASETS:
        raise ValueError("OOD target dataset found in train")
    if not test_datasets <= SOURCE_DATASETS | OOD_DATASETS:
        raise ValueError(f"test contains unknown datasets: {sorted(test_datasets - SOURCE_DATASETS - OOD_DATASETS)}")

    train_keys = {(row["dataset"], row["query"]) for row in train}
    test_keys = {(row["dataset"], row["query"]) for row in test}
    overlap = train_keys & test_keys
    if overlap:
        sample = sorted(overlap)[:3]
        raise ValueError(f"prompt leakage across train/test: {sample}")

    source_test_counts = {k: v for k, v in test_counts.items() if k in SOURCE_DATASETS}
    ood_test_counts = {k: v for k, v in test_counts.items() if k in OOD_DATASETS}
    print("AVENGERS-PRO SPLIT PREFLIGHT PASSED")
    print(f"Train prompts: {len(train)}; source datasets: {dict(train_counts)}")
    print(f"Test prompts: {len(test)}; source holdout: {source_test_counts}; OOD: {ood_test_counts}")
    print(f"Candidate models per prompt: exactly {len(EXPECTED_MODELS)}")
    print("OOD targets appear only in test; no (dataset, query) crosses the split.")
    print("Note: this validates prepared-file structure, not the runtime's internal data flow.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"PREFLIGHT FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
