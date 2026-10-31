"""Day 15: diagnose the Claude Sonnet 4 ArenaHard aggregate/partition mismatch.

Run from the repository root:
    python .\day1_audit\day15_claude_alignment_audit.py

Standard-library-only, read-only audit. It does not change the archive or experiment outputs.
"""
from __future__ import annotations

import json
import re
import tarfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "bench-release.tar.gz"
REPORT = ROOT / "day1_audit" / "DAY15_CLAUDE_ALIGNMENT_AUDIT.txt"
MODEL = "claude-sonnet-4"
DOMAINS = ("arenahard_coding", "arenahard_creative_writing", "arenahard_math")
EXPECTED_TOTAL = 750


def normalize(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", value).strip().casefold()


def prompt(record: dict, field: str) -> str:
    return normalize(record.get(field))


def locate(names: list[str], dataset: str) -> str:
    prefix = f"bench-release/{dataset}/"
    matches = [
        n for n in names
        if n.lower().startswith(prefix.lower())
        and n.lower().endswith(".json")
        and n[len(prefix):].split("/", 1)[0].lower() == MODEL
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {dataset}/{MODEL} file; found {len(matches)}: {matches[:5]}")
    return matches[0]


def load(tar: tarfile.TarFile, name: str) -> tuple[dict, list[dict]]:
    member = tar.getmember(name)
    stream = tar.extractfile(member)
    if stream is None:
        raise RuntimeError(f"Cannot read {name}")
    payload = json.load(stream)
    records = payload.get("records")
    if not isinstance(records, list) or not all(isinstance(x, dict) for x in records):
        raise RuntimeError(f"Invalid records in {name}")
    return payload, records


def score(record: dict) -> str:
    try:
        return format(float(record["score"]), ".12g")
    except (KeyError, TypeError, ValueError):
        return "<MISSING_OR_NONNUMERIC>"


def describe_counter_delta(label: str, left: Counter, right: Counter, lines: list[str]) -> None:
    only_left = left - right
    only_right = right - left
    lines.append(f"{label}: left_only={sum(only_left.values())}; right_only={sum(only_right.values())}")
    if only_left:
        lines.append("  LEFT-ONLY (partition side):")
        for value, count in only_left.most_common():
            lines.append(f"    count={count} value={value!r}")
    if only_right:
        lines.append("  RIGHT-ONLY (aggregate side):")
        for value, count in only_right.most_common():
            lines.append(f"    count={count} value={value!r}")


def main() -> None:
    if not ARCHIVE.is_file():
        raise SystemExit(f"Archive not found: {ARCHIVE}")

    lines = [
        "RESEARCH 3 — DAY 15 CLAUDE SONNET 4 ALIGNMENT AUDIT",
        "=" * 68,
        f"Archive: {ARCHIVE}",
        f"Candidate: {MODEL}",
        "Method: order-independent multiset comparisons; no records are modified.",
        "",
    ]

    with tarfile.open(ARCHIVE, "r:gz") as tar:
        names = sorted(
            m.name.lstrip("./") for m in tar.getmembers()
            if m.isfile() and m.name.lower().endswith(".json")
        )
        partition_records: list[tuple[str, int, dict]] = []
        partition_payloads = {}
        for domain in DOMAINS:
            member = locate(names, domain)
            payload, records = load(tar, member)
            partition_payloads[domain] = payload
            lines.append(
                f"{domain}: records={len(records)}; dataset_name={payload.get('dataset_name')!r}; "
                f"split={payload.get('split')!r}; model_name={payload.get('model_name')!r}"
            )
            partition_records.extend((domain, i, rec) for i, rec in enumerate(records))

        aggregate_name = locate(names, "arenahard")
        aggregate_payload, aggregate_records = load(tar, aggregate_name)
        lines.extend([
            f"arenahard aggregate: records={len(aggregate_records)}; "
            f"dataset_name={aggregate_payload.get('dataset_name')!r}; "
            f"split={aggregate_payload.get('split')!r}; "
            f"model_name={aggregate_payload.get('model_name')!r}",
            "",
        ])

        if len(partition_records) != EXPECTED_TOTAL:
            lines.append(f"WARNING: partition total expected {EXPECTED_TOTAL}, got {len(partition_records)}")
        if len(aggregate_records) != EXPECTED_TOTAL:
            lines.append(f"WARNING: aggregate total expected {EXPECTED_TOTAL}, got {len(aggregate_records)}")

        for field in ("origin_query", "prompt"):
            part = Counter(prompt(rec, field) for _, _, rec in partition_records)
            agg = Counter(prompt(rec, field) for rec in aggregate_records)
            lines.append(f"{field} comparison:")
            describe_counter_delta(field, part, agg, lines)
            lines.append(
                f"  partition_nonempty={sum(v for k, v in part.items() if k)}; "
                f"aggregate_nonempty={sum(v for k, v in agg.items() if k)}; "
                f"partition_unique={len(part) - (1 if '' in part else 0)}; "
                f"aggregate_unique={len(agg) - (1 if '' in agg else 0)}"
            )
            lines.append("")

        # Match the exact field-selection rule used by Day 14.
        def selected(rec: dict) -> str:
            origin = rec.get("origin_query")
            return normalize(origin if isinstance(origin, str) and origin.strip() else rec.get("prompt", ""))

        part_text = Counter(selected(rec) for _, _, rec in partition_records)
        agg_text = Counter(selected(rec) for rec in aggregate_records)
        part_scored = Counter((selected(rec), score(rec)) for _, _, rec in partition_records)
        agg_scored = Counter((selected(rec), score(rec)) for rec in aggregate_records)
        lines.append("DAY 14 SELECTION RULE (origin_query if nonblank, otherwise prompt):")
        describe_counter_delta("selected prompt multiset", part_text, agg_text, lines)
        describe_counter_delta("selected (prompt, score) multiset", part_scored, agg_scored, lines)
        lines.append("")

        # For prompts present on both sides, identify score multiplicity differences.
        part_by_prompt: dict[str, Counter] = {}
        agg_by_prompt: dict[str, Counter] = {}
        for _, _, rec in partition_records:
            part_by_prompt.setdefault(selected(rec), Counter())[score(rec)] += 1
        for rec in aggregate_records:
            agg_by_prompt.setdefault(selected(rec), Counter())[score(rec)] += 1
        score_diffs = []
        for text in sorted(set(part_by_prompt) & set(agg_by_prompt)):
            if part_by_prompt[text] != agg_by_prompt[text]:
                score_diffs.append((text, part_by_prompt[text], agg_by_prompt[text]))
        lines.append(f"Shared-prompt score-multiplicity differences: {len(score_diffs)}")
        for text, left, right in score_diffs:
            lines.append(f"  prompt={text!r}")
            lines.append(f"    partitions={dict(left)}")
            lines.append(f"    aggregate={dict(right)}")
        lines.append("")

        # Compact schema and distribution diagnostics.
        for label, payload, records in [
            ("partition", partition_payloads[DOMAINS[0]], [r for _, _, r in partition_records]),
            ("aggregate", aggregate_payload, aggregate_records),
        ]:
            key_counts = Counter(k for rec in records for k in rec.keys())
            score_counts = Counter(score(rec) for rec in records)
            origin_nonempty = sum(bool(normalize(rec.get("origin_query"))) for rec in records)
            prompt_nonempty = sum(bool(normalize(rec.get("prompt"))) for rec in records)
            lines.append(f"{label} record diagnostics:")
            lines.append(f"  origin_query_nonempty={origin_nonempty}/{len(records)}")
            lines.append(f"  prompt_nonempty={prompt_nonempty}/{len(records)}")
            lines.append(f"  score_distribution={dict(sorted(score_counts.items()))}")
            lines.append(f"  most_common_record_keys={key_counts.most_common(20)}")
            lines.append("")

        # Index-level check is diagnostic only: source partitions are concatenated in
        # the declared domain order, while aggregate order may be different.
        lines.append("FIRST 10 SELECTED PROMPTS BY FILE ORDER (diagnostic only):")
        for domain in DOMAINS:
            records = partition_payloads[domain]["records"]
            lines.append(f"  {domain}:")
            for i, rec in enumerate(records[:10]):
                lines.append(f"    [{i}] prompt={selected(rec)!r}; score={score(rec)}")
        lines.append("  arenahard:")
        for i, rec in enumerate(aggregate_records[:10]):
            lines.append(f"    [{i}] prompt={selected(rec)!r}; score={score(rec)}")

    lines.extend([
        "",
        "INTERPRETATION GUARDRAILS",
        "- A prompt mismatch can reflect coverage, prompt-field, or release-aggregation differences.",
        "- A score mismatch on a shared prompt can reflect a different recorded model response/run.",
        "- This audit does not decide which file is authoritative for a new experiment.",
        "- Do not exclude Claude or claim all 13 models are aligned until the differences are explained.",
        "",
    ])
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"Report: {REPORT}")


if __name__ == "__main__":
    main()
