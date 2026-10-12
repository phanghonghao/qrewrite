"""Frozen benchmark evaluator; keep this file stable during autoresearch."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from .baselines import from_record
from .model import equivalent, metrics
ROOT=Path(__file__).resolve().parents[2]; DATASET=ROOT/"data"/"circuits.jsonl"; BUDGET=64
def evaluator_hash(): return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
def load_records(split=None, dataset_path=None):
    path = Path(dataset_path) if dataset_path is not None else DATASET
    rows=[json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    return [x for x in rows if split is None or x["split"]==split]
def score_candidate(source,candidate):
    passed=equivalent(source,candidate); before,after=metrics(source),metrics(candidate)
    return {"equivalence_pass":passed,"t_count_before":before["t_count"],"t_count_after":after["t_count"],"t_reduction":before["t_count"]-after["t_count"],"metrics":after}
def evaluate_policy(policy,split="validation",budget=BUDGET,seed=0,dataset_path=None):
    out=[]
    for record in load_records(split, dataset_path):
        source=from_record(record); candidate,trajectory,info=policy.run(source,budget,seed)
        out.append({"id":record["id"],"family":record["family"],"split":split,"seed":seed,"budget":budget,"trajectory":trajectory,"verification":score_candidate(source,candidate),"policy_info":info})
    return out
def aggregate(results):
    if not results: return {"count":0,"equivalence_pass_rate":1.0,"mean_t_reduction":0.0,"mean_t_reduction_if_verified":0.0}
    good=[r for r in results if r["verification"]["equivalence_pass"]]; reductions=[r["verification"]["t_reduction"] for r in results]
    return {"count":len(results),"equivalence_pass_rate":len(good)/len(results),"mean_t_reduction":sum(reductions)/len(reductions),"mean_t_reduction_if_verified":sum(r["verification"]["t_reduction"] for r in good)/len(good) if good else 0.0}
