from pathlib import Path

from qrewrite.dataset import SPLIT_FAMILIES, build_dataset, check_split_leakage

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "circuits.jsonl"


def main() -> None:
    records = build_dataset(DATASET)
    errors = check_split_leakage(records)
    if errors:
        raise RuntimeError("dataset leakage detected: " + "; ".join(errors))
    print(f"wrote {len(records)} records to {DATASET}")
    print("split counts:", {split: sum(r["split"] == split for r in records) for split in SPLIT_FAMILIES})


if __name__ == "__main__":
    main()
