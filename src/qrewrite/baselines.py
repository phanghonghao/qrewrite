"""Comparable non-learning baselines with equal budgets and exact verification."""
from __future__ import annotations
import json, random, time
from pathlib import Path
from .model import Circuit, Gate, equivalent, metrics
from .rewrites import Action, greedy, valid_actions, verified_apply

def from_record(record: dict) -> Circuit:
    return Circuit(record["n_qubits"], [Gate(x["name"], tuple(x["qubits"])) for x in record["source"]])

def noop(circuit: Circuit, budget=64):
    return circuit.copy(), []

def random_search(circuit: Circuit, budget=64, seed=0):
    rng, current, best, trajectory = random.Random(seed), circuit.copy(), circuit.copy(), []
    for step in range(budget):
        actions = valid_actions(current)
        if not actions: break
        action = rng.choice(actions); candidate = verified_apply(current, action)
        if candidate is None: continue
        current = candidate
        if metrics(current)["t_count"] < metrics(best)["t_count"] or metrics(current)["gate_count"] < metrics(best)["gate_count"]:
            best = current
        trajectory.append({"step": step, "action": action.as_dict(), "metrics": metrics(current), "verified": equivalent(circuit, current)})
    return best, trajectory

def established(circuit: Circuit, budget=64):
    """Use Qiskit's optimizer when available; exact verification remains authoritative."""
    try:
        from qiskit import transpile
        candidate = transpile(circuit.to_qiskit(), optimization_level=3, basis_gates=["h", "s", "sdg", "t", "tdg", "x", "z", "cx"])
        gates = [Gate(op.name, tuple(q.index for q in qargs)) for op, qargs, _ in candidate.data if op.name in {"h","s","sdg","t","tdg","x","z","cx"}]
        result = Circuit(circuit.n_qubits, gates)
        if equivalent(circuit, result): return result, [{"method": "qiskit_transpile", "verified": True}]
    except Exception as exc:
        return greedy(circuit, budget)[0], [{"method": "greedy_fallback", "verified": True, "error": str(exc)}]
    return circuit.copy(), [{"method": "qiskit_transpile", "verified": False}]

def evaluate(records, budget=64, seeds=(0, 1, 2), output=None):
    methods = {"noop": noop, "random": random_search, "greedy": greedy, "established": established}
    rows=[]
    for record in records:
        source=from_record(record)
        for name, fn in methods.items():
            for seed in (seeds if name == "random" else (0,)):
                start=time.perf_counter()
                result, trajectory = fn(source, budget, seed) if name == "random" else fn(source, budget)
                elapsed=time.perf_counter()-start; verified=equivalent(source,result)
                rows.append({"id":record["id"],"family":record["family"],"split":record["split"],"method":name,"seed":seed,"budget":budget,"runtime_s":elapsed,"before":metrics(source),"after":metrics(result),"equivalence_pass":verified,"trajectory":trajectory,"failure_reason":None if verified else "exact_equivalence_failed"})
    if output:
        Path(output).write_text("\n".join(json.dumps(x, sort_keys=True) for x in rows)+"\n", encoding="utf-8")
    return rows
