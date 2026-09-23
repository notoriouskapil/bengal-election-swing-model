"""Tests for the baseline and the model comparison.

Mostly these pin down the uniform swing machinery, because it's the thing
every other number gets compared against. If it drifts, every claim in the
project moves with it.
"""

import numpy as np
import pytest

from src.features import load_seat_features
from src.models import (
    apply_uniform_swing,
    evaluate,
    run_comparison,
    statewide_swing,
    target,
    uniform_swing_prediction,
)


@pytest.fixture(scope="module")
def seats():
    return load_seat_features()


def test_zero_swing_reproduces_2021(seats):
    """No swing means no change, so the baseline must return the 2021 winners.

    Only checked on seats TMC or BJP actually won, since the bloc labels
    collapse the small parties and can't reproduce `AJUP` or `RSSCMJP`.
    """
    called = apply_uniform_swing(seats, 0.0)
    two_party = seats["winner_party_2021"].isin(["TMC", "BJP"])
    assert (called[two_party] == seats.loc[two_party, "winner_party_2021"]).all()


def test_statewide_swing_is_about_seven_and_a_half(seats):
    """TMC lost 7.4 points and BJP gained 7.8, so the two-party swing is ~7.6."""
    assert statewide_swing(seats) == pytest.approx(7.60, abs=0.05)


def test_more_swing_never_costs_bjp_a_seat(seats):
    """Monotone by construction. A seat BJP wins at 5 points it wins at 10."""
    counts = [uniform_swing_prediction(seats, s).sum() for s in (0, 5, 10, 15, 20)]
    assert counts == sorted(counts)


def test_a_big_enough_swing_takes_everything(seats):
    assert uniform_swing_prediction(seats, 100.0).sum() == len(seats)
    assert uniform_swing_prediction(seats, -100.0).sum() == 0


def test_evaluate_arithmetic():
    y = np.array([1, 1, 0, 0])
    pred = np.array([1, 0, 0, 0])
    got = evaluate(pred, y)
    assert got["bjp_seats_predicted"] == 1
    assert got["bjp_seats_actual"] == 2
    assert got["seat_error"] == -1
    assert got["seats_correct"] == 3
    assert got["accuracy"] == pytest.approx(0.75)


def test_target_matches_the_published_seat_count(seats):
    assert target(seats).sum() == 207


def test_uniform_swing_beats_guessing_bjp_everywhere(seats):
    """The baseline has to be worth something before any model is interesting."""
    y = target(seats)
    naive = evaluate(np.ones(len(seats), dtype=int), y)["accuracy"]
    swing = evaluate(uniform_swing_prediction(seats), y)["accuracy"]
    assert swing > naive


def test_every_model_clears_the_naive_baseline(seats):
    table = run_comparison(seats)
    naive = table.loc[table["model"] == "always BJP", "accuracy"].iloc[0]
    assert (table[table["model"] != "always BJP"]["accuracy"] > naive).all()
