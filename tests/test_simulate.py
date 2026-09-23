"""Tests for the Monte Carlo.

Mostly determinism and the degenerate cases, plus a check that the fitted
lead-scaled swing really does land closer to the actual result than plain
uniform swing does. If that stops being true the whole of phase 4 is noise.
"""

import numpy as np
import pytest

from src.features import load_seat_features
from src.models import target, uniform_swing_prediction
from src.simulate import LEAD_BETA, run, summarise


@pytest.fixture(scope="module")
def seats():
    return load_seat_features()


def test_same_seed_same_answer(seats):
    a = run(seats, n_draws=500, seed=7)
    b = run(seats, n_draws=500, seed=7)
    assert np.array_equal(a, b)


def test_different_seed_different_answer(seats):
    a = run(seats, n_draws=500, seed=7)
    b = run(seats, n_draws=500, seed=8)
    assert not np.array_equal(a, b)


def test_no_randomness_reproduces_the_baseline(seats):
    """Zero everything and it must collapse to the deterministic baseline."""
    counts = run(seats, n_draws=5, swing_sd=0.0, local_sd=0.0, lead_beta=0.0)
    assert len(set(counts.tolist())) == 1
    assert counts[0] == uniform_swing_prediction(seats).sum()


def test_counts_stay_inside_the_house(seats):
    counts = run(seats, n_draws=1000)
    assert counts.min() >= 0
    assert counts.max() <= len(seats)


def test_lead_scaling_beats_plain_uniform(seats):
    """The point of the drift term. BJP gained most in TMC's safest seats, so
    a swing that scales with the lead should land nearer 207 than one that
    doesn't."""
    actual = int(target(seats).sum())
    plain = run(seats, n_draws=5, swing_sd=0.0, local_sd=0.0, lead_beta=0.0)[0]
    scaled = run(seats, n_draws=5, swing_sd=0.0, local_sd=0.0)[0]
    assert abs(scaled - actual) < abs(plain - actual)
    assert LEAD_BETA > 0


def test_more_uncertainty_widens_the_interval(seats):
    narrow = summarise(run(seats, n_draws=2000, swing_sd=0.5))
    wide = summarise(run(seats, n_draws=2000, swing_sd=4.0))
    assert wide["sd"] > narrow["sd"]


def test_summarise_reports_what_it_says(seats):
    counts = run(seats, n_draws=1000)
    got = summarise(counts, actual=207)
    assert got["draws"] == 1000
    assert got["p05"] <= got["median"] <= got["p95"]
    assert 0 <= got["actual_percentile"] <= 100
    assert 0 <= got["majority_prob"] <= 1


def test_noise_pulls_the_average_down(seats):
    """Counterintuitive but real: mean-zero seat noise lowers the expected BJP
    total, because more seats sit just inside the tipping line than just
    outside, so noise knocks more out than it brings in."""
    still = run(seats, n_draws=5, swing_sd=0.0, local_sd=0.0)[0]
    noisy = run(seats, n_draws=4000, swing_sd=0.0).mean()
    assert noisy < still
