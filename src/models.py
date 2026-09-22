"""Models.

Baseline first: apply one statewide swing to every seat and recount. Then
whatever beats it, if anything does.

Everything gets scored against the same held-out arrangement so the numbers
are comparable. Phase 2.
"""


def uniform_swing(seats, swing_pct):
    """2021 shares shifted by a single statewide swing, then recounted."""
    raise NotImplementedError("phase 2")


def fit(seats):
    raise NotImplementedError("phase 2")


def evaluate(model, seats):
    """Seat count error and per-seat accuracy against the actual 2026 result."""
    raise NotImplementedError("phase 2")
