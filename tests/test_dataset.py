from qrewrite.dataset import SPLIT_FAMILIES, build_dataset, check_split_leakage


def test_dataset_contract(tmp_path):
    records = build_dataset(tmp_path / "circuits.jsonl", per_family=1)
    assert len(records) == sum(map(len, SPLIT_FAMILIES.values()))
    assert check_split_leakage(records) == []
    assert {r["split"] for r in records} == set(SPLIT_FAMILIES)
