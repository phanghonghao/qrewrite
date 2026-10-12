"""Deterministic, family-disjoint dataset construction for phase 3."""
from __future__ import annotations

import json
from pathlib import Path

from .model import circuit_signature, generate_circuit, metrics

SPLIT_FAMILIES = {
    "train": ("random", "mirror"),
    "validation": ("motif",),
    "test": ("ladder", "qft_like"),
}


def build_dataset(output: Path, *, per_family: int = 8, base_seed: int = 1000) -> list[dict]:
    records = []
    for split, families in SPLIT_FAMILIES.items():
        for family_index, family in enumerate(families):
            for index in range(per_family):
                seed = base_seed + family_index * 10000 + index + (0 if split == "train" else 100000 if split == "validation" else 200000)
                n_qubits = 3 + (seed % 4)
                circuit = generate_circuit(n_qubits, seed, family, length=8 + seed % 5)
                source = [{"name": g.name, "qubits": list(g.qubits)} for g in circuit.gates]
                records.append({
                    "id": f"{split}-{family}-{index:04d}",
                    "split": split,
                    "family": family,
                    "seed": seed,
                    "n_qubits": n_qubits,
                    "source": source,
                    # The forward-generated source is the target unitary for a
                    # future rewrite episode; this field makes that contract explicit.
                    "target_operations": source,
                    "signature": circuit_signature(circuit),
                    "metrics": metrics(circuit),
                })
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n", encoding="utf-8")
    return records


def check_split_leakage(records: list[dict]) -> list[str]:
    errors = []
    seen: dict[str, str] = {}
    for record in records:
        prior = seen.get(record["signature"])
        if prior is not None and prior != record["split"]:
            errors.append(f"circuit signature appears in {prior} and {record['split']}: {record['id']}")
        seen[record["signature"]] = record["split"]
    family_by_split = {split: set(families) for split, families in SPLIT_FAMILIES.items()}
    for record in records:
        if record["family"] not in family_by_split[record["split"]]:
            errors.append(f"family assigned to wrong split: {record['id']}")
    return errors


def load_dataset(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
