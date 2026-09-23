"""Reconciliation tests for the seat feature table.

The point of these is to catch a parsing or join error that would otherwise
produce a plausible-looking wrong answer. Every number here traces back to
something the Election Commission published, or to the raw database computed
a different way than features.py computes it.
"""

import pandas as pd
import pytest

from src.features import build_seat_features, connect, SEATS_POLLED_2026

# Published statewide shares, percentage of valid votes, NOTA excluded.
PUBLISHED = {
    (2021, "TMC"): 48.55,
    (2021, "BJP"): 38.39,
    (2026, "TMC"): 41.12,
    (2026, "BJP"): 46.20,
}


@pytest.fixture(scope="module")
def seats():
    return build_seat_features()


def test_one_row_per_seat_polled_in_both_years(seats):
    assert len(seats) == SEATS_POLLED_2026
    assert seats["ac_no"].is_unique
    # Falta polled in 2021 only, so it must not be here.
    assert 144 not in set(seats["ac_no"])


def test_no_missing_values(seats):
    missing = seats.isna().sum()
    assert missing.sum() == 0, f"nulls in: {missing[missing > 0].to_dict()}"


def test_shares_sum_to_100_in_every_seat(seats):
    for year in (2021, 2026):
        cols = [f"{b}_pct_{year}" for b in ("tmc", "bjp", "left_inc", "other")]
        total = seats[cols].sum(axis=1)
        assert (total - 100).abs().max() < 1e-6


def test_statewide_shares_match_published(seats):
    """Vote-weighted over all polled seats, straight from the database.

    This is the one that would catch a wrong share denominator. It goes back
    to `results` rather than to the built table, so features.py can't mark its
    own homework.
    """
    with connect() as con:
        got = pd.read_sql_query(
            "select year, "
            "100.0*sum(case when party='TMC' then total_votes else 0 end)"
            "/sum(total_votes) as TMC, "
            "100.0*sum(case when party='BJP' then total_votes else 0 end)"
            "/sum(total_votes) as BJP "
            "from results group by year",
            con,
        ).set_index("year")

    for (year, party), published in PUBLISHED.items():
        assert got.loc[year, party] == pytest.approx(published, abs=0.005)


def test_built_table_reproduces_2026_statewide(seats):
    """2026 polled 293 seats, so the table covers the whole 2026 universe."""
    v = seats["valid_votes_2026"]
    for party, published in (("tmc", 41.12), ("bjp", 46.20)):
        weighted = (seats[f"{party}_pct_2026"] * v).sum() / v.sum()
        assert weighted == pytest.approx(published, abs=0.005)


def test_seat_counts_reconcile(seats):
    """215 and 77 in 2021, minus Falta which was TMC and isn't in this table."""
    c21 = seats["winner_party_2021"].value_counts()
    assert c21["TMC"] == 214
    assert c21["BJP"] == 77

    c26 = seats["winner_party_2026"].value_counts()
    assert c26["BJP"] == 207
    assert c26["TMC"] == 80
    assert c26.sum() == SEATS_POLLED_2026


def test_swing_is_share_difference(seats):
    assert (
        (seats["swing_tmc"] - (seats["tmc_pct_2026"] - seats["tmc_pct_2021"]))
        .abs()
        .max()
        < 1e-9
    )


def test_the_roll_shrank_in_most_seats(seats):
    """From the earlier write-up: the register shrank in 241 of 293 seats."""
    assert (seats["roll_change_pct"] < 0).sum() == 241


def test_roll_change_and_turnout_change_move_opposite_ways(seats):
    """A shrinking denominator inflates turnout. Reported as -0.84 earlier."""
    r = seats["roll_change_pct"].corr(seats["turnout_change"])
    assert r == pytest.approx(-0.84, abs=0.03)


def test_no_seat_moved_against_the_tide(seats):
    """129 seats went TMC to BJP and none came back."""
    tmc_to_bjp = (
        (seats["winner_party_2021"] == "TMC") & (seats["winner_party_2026"] == "BJP")
    ).sum()
    bjp_to_tmc = (
        (seats["winner_party_2021"] == "BJP") & (seats["winner_party_2026"] == "TMC")
    ).sum()
    assert tmc_to_bjp == 129
    assert bjp_to_tmc == 0
