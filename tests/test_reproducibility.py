from qrewrite.dataset import build_dataset


def test_dataset_bytes_are_deterministic(tmp_path):
    a, b = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    build_dataset(a)
    build_dataset(b)
    assert a.read_bytes() == b.read_bytes()
