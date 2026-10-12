# Research program

Only `src/qrewrite/policy.py` is intended to change during autoresearch.
`evaluator.py`, the dataset, split labels, budget, verifier, and scoring rules
are frozen. Every trial records its evaluator hash, trajectory, verification
outcomes, runtime, and failure reason.
