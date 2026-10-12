from qrewrite.evaluator import aggregate, evaluator_hash


def test_evaluator_hash_and_empty_aggregate():
    assert len(evaluator_hash()) == 64
    assert aggregate([])["equivalence_pass_rate"] == 1.0
