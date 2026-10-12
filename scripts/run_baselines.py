from pathlib import Path

from qrewrite.baselines import evaluate
from qrewrite.dataset import load_dataset

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    rows = evaluate(load_dataset(ROOT / "data" / "circuits.jsonl"), output=ROOT / "results" / "baseline_results.jsonl")
    print(f"wrote {len(rows)} baseline records")


if __name__ == "__main__":
    main()
