import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
METADATA_PATH = ROOT / "day1_audit" / "all_result_metadata.csv"

TARGETS = {
    "arenahard_coding",
    "arenahard_creative_writing",
    "arenahard_math",
}


def main():
    if not METADATA_PATH.is_file():
        raise FileNotFoundError(
            f"Required local metadata file not found: {METADATA_PATH.name}"
        )

    with METADATA_PATH.open(
        newline="", encoding="utf-8-sig"
    ) as handle:
        rows = list(csv.DictReader(handle))

    print("Total metadata rows:", len(rows))
    print("Columns:", list(rows[0]) if rows else "EMPTY")

    for dataset in sorted(TARGETS):
        matches = [
            row for row in rows
            if row.get("dataset", "").lower() == dataset
        ]
        missing = sum(
            not Path(row.get("archive_path", "")).is_file()
            for row in matches
        )
        print(f"\n{dataset}: {len(matches)} metadata rows")
        print("Archive paths not found locally:", missing)


if __name__ == "__main__":
    main()
