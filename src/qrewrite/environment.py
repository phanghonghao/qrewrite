"""Deterministic rewrite environment and state/action encoding."""
from __future__ import annotations
import random
from .model import Circuit, metrics, equivalent
from .rewrites import Action, apply_action, valid_actions

RULES=("cancel_inverse","cancel_pair","merge_t","merge_tdg")

def state_representation(circuit: Circuit) -> dict:
    return {"n_qubits":circuit.n_qubits,"gates":[{"name":g.name,"qubits":list(g.qubits),"phase":0} for g in circuit.gates],"connectivity":[list(g.qubits) for g in circuit.gates if len(g.qubits)==2],"metrics":metrics(circuit)}

class RewriteEnv:
    def __init__(self, source: Circuit, budget=64, reward_mode="terminal"):
        self.source=source.copy(); self.budget=budget; self.reward_mode=reward_mode; self._verified_pairs={}; self.reset()
    def reset(self, seed=0):
        self.rng=random.Random(seed); self.current=self.source.copy(); self.steps=0; self.trajectory=[]; return state_representation(self.current)
    def actions(self): return valid_actions(self.current)
    def step(self, action: Action):
        before=metrics(self.current); candidate=apply_action(self.current,action)
        key=(tuple((g.name,g.qubits) for g in self.current.gates), action.rule, action.location)
        verified = key in self._verified_pairs
        if candidate is not None and not verified:
            verified = equivalent(self.current,candidate); self._verified_pairs[key]=verified
        if verified: self.current=candidate
        self.steps += 1; after=metrics(self.current)
        reward=before["t_count"]-after["t_count"] if self.reward_mode=="immediate" else 0.0
        if self.steps >= self.budget or not self.actions(): reward += metrics(self.source)["t_count"]-after["t_count"]
        row={"step":self.steps-1,"action":action.as_dict(),"before":before,"after":after,"verified":verified,"reward":reward}
        self.trajectory.append(row)
        return state_representation(self.current), reward, self.steps>=self.budget or not self.actions(), row
