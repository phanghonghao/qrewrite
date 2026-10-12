# qrewrite

`qrewrite` is a standalone research harness for exactly verified Clifford+T
circuit rewriting. Qiskit is an external wheel dependency; this repository does
not import or copy the Qiskit source checkout.

Install from any working directory:

```powershell
python -m pip install -e .
python scripts/prepare.py
python -m pip install -e ".[test]"
python -m pytest -q
python scripts/run_baselines.py
python scripts/run_autoresearch.py --seed 0 --split validation --budget 64
```

The exact symbolic verifier, frozen evaluator, deterministic dataset, and
research scope are documented in `docs/RESEARCH_SPEC.md` and
`configs/frozen_scope.json`. Generated benchmark output is kept under
`results/`; the source dataset is versioned under `data/`.
