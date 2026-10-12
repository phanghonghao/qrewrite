from qrewrite.environment import RewriteEnv
from qrewrite.model import Circuit, Gate


def test_environment_is_reproducible():
    circuit = Circuit(3, [Gate("t", (0,)), Gate("tdg", (0,))])
    first = RewriteEnv(circuit, budget=4)
    second = RewriteEnv(circuit, budget=4)
    assert first.reset(seed=7) == second.reset(seed=7)
