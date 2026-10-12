"""Exact, auditable Clifford+T circuit rewriting research harness."""

from .model import Circuit, Gate, equivalent, exact_unitary, metrics

__all__ = ["Circuit", "Gate", "equivalent", "exact_unitary", "metrics"]
