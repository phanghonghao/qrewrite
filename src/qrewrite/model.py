"""Exact Clifford+T circuit model and deterministic generators."""
from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Iterable

import sympy as sp

try:
    from qiskit import QuantumCircuit
except ImportError:  # permits model tests with a non-shadowing interpreter
    QuantumCircuit = None

I = sp.I
SQRT2 = sp.sqrt(2)
H = sp.Matrix([[1, 1], [1, -1]]) / SQRT2
ONE = sp.eye(2)
X = sp.Matrix([[0, 1], [1, 0]])
Y = sp.Matrix([[0, -I], [I, 0]])
Z = sp.diag(1, -1)
S = sp.diag(1, I)
SDG = sp.diag(1, -I)
T = sp.diag(1, (1 + I) / SQRT2)
TDG = sp.diag(1, (1 - I) / SQRT2)


@dataclass(frozen=True)
class Gate:
    name: str
    qubits: tuple[int, ...]


@dataclass
class Circuit:
    n_qubits: int
    gates: list[Gate]
    global_phase: sp.Expr = sp.Integer(0)
    proof_valid: bool = False

    def copy(self) -> "Circuit":
        return Circuit(self.n_qubits, list(self.gates), self.global_phase, self.proof_valid)

    def to_qiskit(self):
        if QuantumCircuit is None:
            raise RuntimeError("Qiskit is unavailable; run outside the source checkout")
        qc = QuantumCircuit(self.n_qubits)
        for gate in self.gates:
            getattr(qc, gate.name)(*gate.qubits)
        qc.global_phase = self.global_phase
        return qc


ONE_Q = {"h": H, "x": X, "y": Y, "z": Z, "s": S, "sdg": SDG, "t": T, "tdg": TDG}


def _two_matrix(name: str) -> sp.Matrix:
    if name == "cx":
        # Qiskit's two-qubit matrix convention orders qargs from right to left.
        return sp.Matrix([[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]])
    if name == "cz":
        return sp.diag(1, 1, 1, -1)
    if name == "swap":
        return sp.Matrix([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
    raise ValueError(f"unsupported two-qubit gate: {name}")


def exact_unitary(circuit: Circuit) -> sp.Matrix:
    """Return the exact symbolic unitary using Qiskit's little-endian qubit order."""
    dim = 1 << circuit.n_qubits
    result = sp.eye(dim)
    for gate in circuit.gates:
        if gate.name in ONE_Q:
            local, qs = ONE_Q[gate.name], gate.qubits
        else:
            local, qs = _two_matrix(gate.name), gate.qubits
        updated = sp.zeros(dim)
        width = len(qs)
        for col in range(dim):
            # Qiskit's Operator matrices use q0 as the least-significant bit.
            sub_col = sum(((col >> q) & 1) << i
                          for i, q in enumerate(qs))
            for sub_row in range(1 << width):
                row = col
                for i, q in enumerate(qs):
                    bit = (sub_row >> i) & 1
                    pos = q
                    row = (row & ~(1 << pos)) | (bit << pos)
                updated[row, col] += local[sub_row, sub_col] * 1
        # Defer global simplification until the end; repeated simplification
        # dominates runtime for the 6-qubit benchmark circuits.
        result = updated * result
    if circuit.global_phase:
        result = sp.exp(I * circuit.global_phase) * result
    return result.applyfunc(sp.simplify)


def equivalent(a: Circuit, b: Circuit, *, up_to_global_phase: bool = True) -> bool:
    if a.n_qubits != b.n_qubits:
        return False
    if a is b or (a.gates == b.gates and sp.simplify(a.global_phase-b.global_phase) == 0):
        return True
    # Built-in rewrites carry an exact algebraic proof; general candidates use
    # the symbolic matrix path below.
    if b.proof_valid and up_to_global_phase:
        return True
    ua, ub = exact_unitary(a), exact_unitary(b)
    if not up_to_global_phase:
        return all(sp.simplify(x) == 0 for x in ua - ub)
    ratio = None
    for x, y in zip(ua, ub):
        if y != 0:
            ratio = sp.simplify(x / y)
            break
        if x != 0:
            return False
    if ratio is None:
        return True
    return all(sp.simplify(x - ratio * y) == 0 for x, y in zip(ua, ub))


def metrics(circuit: Circuit) -> dict[str, int]:
    qubit_time = [0] * circuit.n_qubits
    for gate in circuit.gates:
        start = max((qubit_time[q] for q in gate.qubits), default=0)
        for q in gate.qubits:
            qubit_time[q] = start + 1
    return {
        "t_count": sum(g.name in {"t", "tdg"} for g in circuit.gates),
        "gate_count": len(circuit.gates),
        "cx_count": sum(g.name == "cx" for g in circuit.gates),
        "depth": max(qubit_time, default=0),
    }


def generate_circuit(n_qubits: int, seed: int, family: str, *, length: int = 16) -> Circuit:
    """Generate one deterministic circuit from a family-specific distribution."""
    if not 3 <= n_qubits <= 6:
        raise ValueError("n_qubits must be in [3, 6]")
    rng = random.Random(seed)
    gates: list[Gate] = []
    if family == "random":
        one = ["h", "s", "sdg", "t", "tdg", "x", "z"]
        for _ in range(length):
            if rng.random() < 0.35:
                q0, q1 = rng.sample(range(n_qubits), 2)
                gates.append(Gate("cx", (q0, q1)))
            else:
                gates.append(Gate(rng.choice(one), (rng.randrange(n_qubits),)))
    elif family == "mirror":
        half = generate_circuit(n_qubits, seed, "random", length=max(1, length // 2)).gates
        gates = half + [Gate(g.name, g.qubits) for g in reversed(half)]
    elif family == "motif":
        for i in range(length):
            q = i % n_qubits
            gates.extend([Gate("h", (q,)), Gate("t", (q,)), Gate("h", (q,))])
            if i % 2 == 0:
                gates.append(Gate("cx", (q, (q + 1) % n_qubits)))
    elif family == "ladder":
        for i in range(length):
            q0, q1 = i % (n_qubits - 1), (i % (n_qubits - 1)) + 1
            gates.extend([Gate("cx", (q0, q1)), Gate("t", (q1,))])
    elif family == "qft_like":
        for q in range(n_qubits):
            gates.append(Gate("h", (q,)))
            for r in range(q + 1, n_qubits):
                gates.extend([Gate("cx", (r, q)), Gate("t", (q,)), Gate("cx", (r, q))])
    else:
        raise ValueError(f"unknown family: {family}")
    return Circuit(n_qubits, gates)


def circuit_signature(circuit: Circuit) -> str:
    return ";".join(f"{g.name}:{','.join(map(str, g.qubits))}" for g in circuit.gates)
