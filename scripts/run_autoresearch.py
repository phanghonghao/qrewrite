import argparse
import json
import time
from pathlib import Path

from qrewrite.evaluator import aggregate, evaluator_hash, evaluate_policy
from qrewrite.policy import TabularPolicy

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "experiment_results.jsonl"
CHECKPOINT = ROOT / "results" / "checkpoint.json"


def run_trial(seed=0, split="validation", budget=64, reward_mode="terminal"):
    started = time.perf_counter()
    policy = TabularPolicy(seed=seed, reward_mode=reward_mode)
    rows = evaluate_policy(policy, split, budget, seed)
    summary = aggregate(rows)
    accepted = summary["equivalence_pass_rate"] == 1.0
    trial = {"revision": "working-tree", "seed": seed, "runtime_s": time.perf_counter() - started,
             "evaluator_hash": evaluator_hash(), "split": split, "budget": budget,
             "reward_mode": reward_mode, "metrics": summary, "accepted": accepted,
             "failure_reason": None if accepted else "equivalence_pass_rate_below_100_percent", "results": rows}
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(trial, sort_keys=True) + "\n")
    if accepted:
        CHECKPOINT.write_text(json.dumps({"evaluator_hash": trial["evaluator_hash"], "seed": seed,
                                          "score": summary["mean_t_reduction_if_verified"]}, indent=2), encoding="utf-8")
    return trial


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--split", default="validation")
    parser.add_argument("--budget", type=int, default=64)
    parser.add_argument("--reward-mode", choices=["immediate", "terminal", "reusability"], default="terminal")
    args = parser.parse_args()
    trial = run_trial(args.seed, args.split, args.budget, args.reward_mode)
    print(json.dumps({key: trial[key] for key in ("accepted", "evaluator_hash", "metrics", "failure_reason")}, sort_keys=True))


if __name__ == "__main__":
    main()
