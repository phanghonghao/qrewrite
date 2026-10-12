"""Small interpretable learned policy; a tabular scorer precedes any GNN/PPO work."""
from __future__ import annotations
import random
from collections import defaultdict
from .environment import RewriteEnv
from .model import metrics, equivalent

class TabularPolicy:
    def __init__(self, seed=0, epsilon=0.1, reward_mode="terminal"):
        self.rng=random.Random(seed); self.epsilon=epsilon; self.reward_mode=reward_mode; self.values=defaultdict(float)
    def _key(self, state, action): return (action.rule, state["metrics"]["t_count"], state["metrics"]["gate_count"], tuple(action.qubits))
    def select(self, state, actions):
        if not actions: return None
        if self.rng.random()<self.epsilon: return self.rng.choice(actions)
        return max(actions, key=lambda a:(self.values[self._key(state,a)], -a.location, a.rule))
    def run(self, circuit, budget=64, seed=0, train=False):
        env=RewriteEnv(circuit,budget,self.reward_mode); state=env.reset(seed); total=0.0
        while env.actions() and env.steps<budget:
            action=self.select(state,env.actions()); nxt,reward,done,row=env.step(action); total+=reward
            if train: self.values[self._key(state,action)] += 0.1*(reward-self.values[self._key(state,action)])
            state=nxt
            if done: break
        return env.current, env.trajectory, {"return":total,"equivalence_pass":equivalent(circuit,env.current)}

def train_policy(circuits, episodes=10, budget=64, seed=0, reward_mode="terminal"):
    policy=TabularPolicy(seed,reward_mode=reward_mode)
    for episode in range(episodes):
        for circuit in circuits: policy.run(circuit,budget,seed+episode,train=True)
    return policy
