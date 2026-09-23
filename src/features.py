"""Seat-level feature table.

One row per constituency that polled in both 2021 and 2026, carrying each
year's vote shares, the winner, the margin, turnout and the electoral roll,
plus the swing between the two.

Vote share is a percentage of valid votes in that seat. NOTA sits in its own
table and is not a row in `results`, so it is excluded, which is the basis the
Commission's published shares use. That reproduces 48.55 / 38.39 for 2021 and
41.12 / 46.20 for 2026 statewide, which is what tests/test_features.py checks.

Reads data/raw/bengal_elections.db, writes data/model/seat_features.csv.
Nothing here writes to the raw database.
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DB = ROOT / "data" / "raw" / "bengal_elections.db"
MODEL_DIR = ROOT / "data" / "model"
OUT_CSV = MODEL_DIR / "seat_features.csv"

# Falta (ac_no 144) held no poll in 2026. Always filter on seat_status rather
# than hardcoding this, it's here so the number is written down somewhere.
SEATS_TOTAL = 294
SEATS_POLLED_2026 = 293

# The two parties the swing is measured between. Everything else is folded
# into LEFT_INC or OTHER, because no third force won more than 2 seats in
# either year and the model only needs the TMC/BJP contest.
LEFT_INC = ("CPI(M)", "CPIM", "CPI", "INC", "AIFB", "RSP", "AIFB(M)")


def connect(db_path=RAW_DB):
    """Open the raw database read-only so nothing can scribble on it."""
    if not Path(db_path).exists():
        raise FileNotFoundError(f"no database at {db_path}")
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def _shares(con):
    """Per seat per year: vote share for TMC, BJP, the Left/Congress bloc, rest."""
    votes = pd.read_sql_query(
        "select year, ac_no, party, sum(total_votes) as votes "
        "from results group by year, ac_no, party",
        con,
    )
    votes["bloc"] = "OTHER"
    votes.loc[votes["party"] == "TMC", "bloc"] = "TMC"
    votes.loc[votes["party"] == "BJP", "bloc"] = "BJP"
    votes.loc[votes["party"].isin(LEFT_INC), "bloc"] = "LEFT_INC"

    by_bloc = votes.groupby(["year", "ac_no", "bloc"], as_index=False)["votes"].sum()
    valid = by_bloc.groupby(["year", "ac_no"], as_index=False)["votes"].sum()
    valid = valid.rename(columns={"votes": "valid_votes"})

    wide = by_bloc.pivot_table(
        index=["year", "ac_no"], columns="bloc", values="votes", fill_value=0
    ).reset_index()
    wide = wide.merge(valid, on=["year", "ac_no"])

    for bloc in ("TMC", "BJP", "LEFT_INC", "OTHER"):
        if bloc not in wide:
            wide[bloc] = 0
        wide[f"{bloc.lower()}_pct"] = 100.0 * wide[bloc] / wide["valid_votes"]

    return wide[
        [
            "year",
            "ac_no",
            "valid_votes",
            "tmc_pct",
            "bjp_pct",
            "left_inc_pct",
            "other_pct",
        ]
    ]


def build_seat_features():
    """One row per seat that polled in both years. Returns the frame and writes it."""
    with connect() as con:
        seats = pd.read_sql_query(
            "select ac_no, ac_name, district, region, reservation, is_reserved "
            "from constituencies",
            con,
        )
        status = pd.read_sql_query("select year, ac_no, result_status from seat_status", con)
        wins = pd.read_sql_query(
            "select year, ac_no, winner_party, margin_pct_polled, turnout_pct, "
            "total_electors, votes_polled from winners",
            con,
        )
        shares = _shares(con)
        # The actual winning candidate's share. Needed because the bloc columns
        # sum several parties, and a bloc sum is not a candidate: in Darjeeling
        # the `OTHER` bloc reaches 57% while BJP won the seat on 41.5%.
        top = pd.read_sql_query(
            "select year, ac_no, vote_pct as winner_pct from results where position = 1",
            con,
        )

    # Seats that polled in both years. Falta drops out here, not by ac_no.
    polled = status[status["result_status"] == "polled"]
    both = set(polled.loc[polled["year"] == 2021, "ac_no"]) & set(
        polled.loc[polled["year"] == 2026, "ac_no"]
    )
    seats = seats[seats["ac_no"].isin(both)].copy()

    year_cols = wins.merge(shares, on=["year", "ac_no"]).merge(top, on=["year", "ac_no"])
    out = seats
    for year in (2021, 2026):
        block = year_cols[year_cols["year"] == year].drop(columns="year")
        block = block.rename(columns={c: f"{c}_{year}" for c in block.columns if c != "ac_no"})
        out = out.merge(block, on="ac_no", how="left")

    # Swing is positive when the party gained between 2021 and 2026.
    out["swing_tmc"] = out["tmc_pct_2026"] - out["tmc_pct_2021"]
    out["swing_bjp"] = out["bjp_pct_2026"] - out["bjp_pct_2021"]
    # The two-party margin, TMC minus BJP. Sign flips when the seat flips.
    out["tmc_lead_2021"] = out["tmc_pct_2021"] - out["bjp_pct_2021"]
    out["tmc_lead_2026"] = out["tmc_pct_2026"] - out["bjp_pct_2026"]
    out["roll_change_pct"] = 100.0 * (
        out["total_electors_2026"] / out["total_electors_2021"] - 1.0
    )
    out["turnout_change"] = out["turnout_pct_2026"] - out["turnout_pct_2021"]
    # Where a third party held the seat in 2021, this is the share a swung TMC
    # or BJP has to beat to take it. Zero everywhere else.
    third = ~out["winner_party_2021"].isin(["TMC", "BJP"])
    out["third_party_hold_2021"] = 0.0
    out.loc[third, "third_party_hold_2021"] = out.loc[third, "winner_pct_2021"]

    out = out.sort_values("ac_no").reset_index(drop=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    return out


def load_seat_features():
    """Read the built table. Builds it first if it isn't there."""
    if not OUT_CSV.exists():
        return build_seat_features()
    return pd.read_csv(OUT_CSV)


if __name__ == "__main__":
    df = build_seat_features()
    print(f"{len(df)} seats -> {OUT_CSV.relative_to(ROOT)}")
    print(f"  TMC {df['tmc_pct_2021'].mean():.2f} -> {df['tmc_pct_2026'].mean():.2f} (seat mean)")
    print(f"  BJP {df['bjp_pct_2021'].mean():.2f} -> {df['bjp_pct_2026'].mean():.2f} (seat mean)")
