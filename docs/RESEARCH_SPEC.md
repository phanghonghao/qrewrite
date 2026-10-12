# Research specification (frozen 2026-10-12)

The scope is 3-6 qubit Clifford+T circuits using H, S, Sdg, T, Tdg, X, Y, Z,
CX, CZ, and SWAP. No ancillas, measurement, classical control, reset,
feed-forward, or opaque gates are included. T-count is primary; gate count,
CX count, depth, and runtime are secondary. The rewrite budget is 64 steps.

Candidates are accepted only when SymPy exact matrices match up to one scalar
global phase. Dataset splits are family-disjoint: train random/mirror,
validation motif, and test ladder/qft_like. Evaluator, split labels, dataset,
and scoring rules are frozen during policy experiments.
