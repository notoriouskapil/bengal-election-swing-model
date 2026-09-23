"""Tests for the residual analysis.

The headline claim of phase 3 is that the baseline's errors sit at the
tipping point rather than in the close seats. That's counterintuitive enough
that it needs pinning down.
"""

import pytest

from src.features import load_seat_features
from src.models import statewide_swing, target, uniform_swing_prediction
from src.explain import (
    baseline_misses,
    local_swing_spread,
    logistic_coefficients,
    miss_summary,
)


@pytest.fixture(scope="module")
def seats():
    return load_seat_features()


def test_baseline_misses_47_seats(seats):
    misses = baseline_misses(seats)
    assert len(misses) == 47
    correct = (uniform_swing_prediction(seats) == target(seats)).sum()
    assert correct + len(misses) == len(seats)


def test_local_swing_is_not_uniform(seats):
    """The whole premise. If this spread were near zero the baseline would be
    close to exact, and there would be nothing to model."""
    spread = local_swing_spread(seats)
    assert spread["local_swing"].std() == pytest.approx(4.99, abs=0.1)
    assert spread["local_swing"].min() < 0      # some seats swung to TMC
    assert spread["local_swing"].max() > 20     # and some swung very hard


def test_misses_concentrate_at_the_tipping_point(seats):
    """Miss rate should fall as seats get further from the decisive margin."""
    statewide = statewide_swing(seats)
    tipping = 2 * statewide
    dist = (seats["tmc_lead_2021"] - tipping).abs()
    missed = (uniform_swing_prediction(seats) != target(seats)).values

    near = missed[dist <= 3].mean()
    far = missed[dist > 20].mean()
    assert near > 0.3
    assert far < 0.06
    assert near > far * 5


def test_close_seats_are_predicted_well(seats):
    """The counterintuitive bit: seats decided by under 5 points in 2021 are
    the baseline's *easiest*, because any positive swing flips them."""
    _, by_band = miss_summary(seats)
    closest = by_band[by_band["margin_band"] == "0-5"]["miss_rate"].iloc[0]
    midband = by_band[by_band["margin_band"] == "15-25"]["miss_rate"].iloc[0]
    assert closest < 0.05
    assert midband > 0.35


def test_kolkata_is_the_worst_region(seats):
    by_region, _ = miss_summary(seats)
    assert by_region.iloc[0]["region"] == "Kolkata & Howrah"


def test_coefficients_come_back_ranked(seats):
    coefs = logistic_coefficients(seats)
    assert len(coefs) > len(seats.columns) // 4
    assert coefs["absolute"].is_monotonic_decreasing
