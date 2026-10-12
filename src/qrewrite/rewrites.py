"""Finite, exact-preserving rewrite actions used by baselines and learning."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .model import Circuit, Gate, equivalent, metrics

INVERSE = {"h": "h", "x": "x", "y": "y", "z": "z", "s": "sdg", "sdg": "s", "t": "tdg", "tdg": "t", "cx": "cx", "cz": "cz", "swap": "swap"}

@dataclass(frozen=True)
class Action:
    rule: str
    location: int
    qubits: tuple[int, ...] = ()

    def as_dict(self):
        return {"rule": self.rule, "location": self.location, "qubits": list(self.qubits)}

def _replace(c: Circuit, start: int, width: int, gates: list[Gate]) -> Circuit:
    return Circuit(c.n_qubits, c.gates[:start] + gates + c.gates[start + width:], c.global_phase, True)

def valid_actions(circuit: Circuit) -> list[Action]:
    """Enumerate a finite action space; actions are syntactic candidates only."""
    out: list[Action] = []
    g = circuit.gates
    for i in range(len(g) - 1):
        a, b = g[i], g[i + 1]
        if a.qubits == b.qubits and a.name == b.name and a.name in {"h", "x", "y", "z", "cx", "cz", "swap"}:
            out.append(Action("cancel_pair", i, a.qubits))
        if a.qubits == b.qubits and {a.name, b.name} in ({"s", "sdg"}, {"t", "tdg"}):
            out.append(Action("cancel_pair", i, a.qubits))
        if a.qubits == b.qubits and a.name == b.name == "t":
            out.append(Action("merge_t", i, a.qubits))
        if a.qubits == b.qubits and a.name == b.name == "tdg":
            out.append(Action("merge_tdg", i, a.qubits))
    return out

def apply_action(circuit: Circuit, action: Action) -> Circuit | None:
    i = action.location
    if i < 0 or i >= len(circuit.gates):
        return None
    g = circuit.gates
    if action.rule == "cancel_pair" and i + 1 < len(g):
        a, b = g[i], g[i + 1]
        if a.qubits == b.qubits and (INVERSE.get(a.name) == b.name):
            return _replace(circuit, i, 2, [])
        if a.qubits == b.qubits and a.name == b.name and a.name in {"h", "x", "y", "z", "cx", "cz", "swap"}:
            return _replace(circuit, i, 2, [])
    if action.rule == "cancel_inverse" and i + 1 < len(g):
        a, b = g[i], g[i + 1]
        if a.qubits == b.qubits and INVERSE.get(a.name) == b.name:
            return _replace(circuit, i, 2, [])
    if action.rule == "merge_t" and i + 1 < len(g) and g[i].name == g[i + 1].name == "t" and g[i].qubits == g[i + 1].qubits:
        return _replace(circuit, i, 2, [Gate("s", g[i].qubits)])
    if action.rule == "merge_tdg" and i + 1 < len(g) and g[i].name == g[i + 1].name == "tdg" and g[i].qubits == g[i + 1].qubits:
        return _replace(circuit, i, 2, [Gate("sdg", g[i].qubits)])
    return None

def verified_apply(circuit: Circuit, action: Action, *, verify: bool = True) -> Circuit | None:
    candidate = apply_action(circuit, action)
    return candidate if candidate is not None and (not verify or equivalent(circuit, candidate)) else None

def greedy(circuit: Circuit, budget: int = 64) -> tuple[Circuit, list[dict]]:
    current, trajectory = circuit.copy(), []
    for step in range(budget):
        before = metrics(current)
        choices = []
        for action in valid_actions(current):
            candidate = verified_apply(current, action)
            if candidate is not None and metrics(candidate)["t_count"] <= before["t_count"]:
                choices.append((metrics(candidate), action, candidate))
        if not choices:
            break
        _, action, current = min(choices, key=lambda item: (item[0]["t_count"], item[0]["gate_count"], item[1].location, item[1].rule))
        trajectory.append({"step": step, "action": action.as_dict(), "metrics": metrics(current), "verified": True})
    return current, trajectory
