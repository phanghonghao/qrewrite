import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from qrewrite.model import Circuit, Gate, equivalent, generate_circuit, metrics


def test_identical_and_known_equivalent():
    a = Circuit(3, [Gate("t", (0,)), Gate("tdg", (0,))])
    assert equivalent(a, a)
    assert equivalent(a, Circuit(3, []))


def test_global_phase_policy():
    a = Circuit(3, [Gate("x", (0,))])
    b = Circuit(3, [Gate("x", (0,))], global_phase=3.141592653589793)
    # symbolic pi is the exact representation used for this test
    import sympy as sp
    b.global_phase = sp.pi
    assert equivalent(a, b)
    assert not equivalent(a, b, up_to_global_phase=False)


def test_non_equivalent_and_metrics():
    assert not equivalent(Circuit(3, [Gate("t", (0,))]), Circuit(3, [Gate("t", (1,))]))
    assert metrics(Circuit(3, [Gate("t", (0,)), Gate("cx", (0, 1))])) == {
        "t_count": 1, "gate_count": 2, "cx_count": 1, "depth": 2
    }


def test_generators_are_deterministic_and_bounded():
    a = generate_circuit(4, 9, "random")
    b = generate_circuit(4, 9, "random")
    assert a.gates == b.gates
    assert 3 <= a.n_qubits <= 6
