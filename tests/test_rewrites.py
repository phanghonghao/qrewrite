from qrewrite.model import Circuit, Gate, equivalent, metrics
from qrewrite.rewrites import Action, greedy, verified_apply


def test_exact_cancel_and_greedy():
    source = Circuit(3, [Gate("t", (0,)), Gate("tdg", (0,)), Gate("h", (1,))])
    candidate = verified_apply(source, Action("cancel_pair", 0, (0,)))
    assert candidate is not None and equivalent(source, candidate)
    result, trajectory = greedy(source)
    assert equivalent(source, result)
    assert metrics(result)["t_count"] == 0
    assert trajectory
