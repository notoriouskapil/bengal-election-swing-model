"""Models.

The baseline is uniform swing: take each seat's 2021 shares, move TMC and BJP
by one statewide number, recount. It knows nothing about any individual seat,
so anything with features in it has to beat this to be worth keeping.

On leakage. Two feature sets, deliberately kept apart:

  PRE_FEATURES   2021 results and things fixed before polling day
                 (reservation, region). Everything here was knowable in
                 advance, so a score off this set means something.

  POST_FEATURES  the above plus the 2026 roll change and turnout change.
                 Both are measured at the same time as the outcome, so a
                 model using them is explaining, not predicting. The gap
                 between the two is the interesting part, not the second
                 number on its own.

Scoring uses 5-fold cross-validation over seats. That is not a held-out
election, and with two elections in one state there isn't one. See
docs/model_card.md.
"""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.features import load_seat_features

SEED = 2026

NUMERIC_PRE = [
    "tmc_pct_2021",
    "bjp_pct_2021",
    "left_inc_pct_2021",
    "other_pct_2021",
    "tmc_lead_2021",
    "margin_pct_polled_2021",
    "turnout_pct_2021",
    "is_reserved",
]
NUMERIC_POST = NUMERIC_PRE + ["roll_change_pct", "turnout_change"]
CATEGORICAL = ["region"]

PRE_FEATURES = NUMERIC_PRE + CATEGORICAL
POST_FEATURES = NUMERIC_POST + CATEGORICAL


def target(seats):
    """1 where BJP won the seat in 2026. 207 of 293."""
    return (seats["winner_party_2026"] == "BJP").astype(int)


# --------------------------------------------------------------------------
# baseline
# --------------------------------------------------------------------------

def apply_uniform_swing(seats, swing_pct):
    """2021 shares with `swing_pct` moved from TMC to BJP, then recounted.

    This is a two-party model, and deliberately so. An earlier version picked
    the winner by argmax across TMC, BJP and two aggregate blocs, which was
    wrong: a bloc sum is not a candidate. In Darjeeling the `OTHER` bloc
    reaches 57% because several hill parties split that vote, while BJP won
    the seat on 41.5%. Calling the seat for `OTHER` invents a winner.

    So the contest is TMC against BJP, and the only third element is
    `third_party_hold_2021` — the actual share of the winning candidate in the
    two seats a third party held, which a swung TMC or BJP has to clear to
    take it. It is zero everywhere else.
    """
    shares = pd.DataFrame(
        {
            "TMC": seats["tmc_pct_2021"] - swing_pct,
            "BJP": seats["bjp_pct_2021"] + swing_pct,
            "THIRD": seats["third_party_hold_2021"],
        }
    )
    return shares.idxmax(axis=1)


def statewide_swing(seats):
    """The actual two-party swing, vote-weighted: half of what changed hands."""
    v21, v26 = seats["valid_votes_2021"], seats["valid_votes_2026"]
    tmc21 = (seats["tmc_pct_2021"] * v21).sum() / v21.sum()
    tmc26 = (seats["tmc_pct_2026"] * v26).sum() / v26.sum()
    bjp21 = (seats["bjp_pct_2021"] * v21).sum() / v21.sum()
    bjp26 = (seats["bjp_pct_2026"] * v26).sum() / v26.sum()
    return ((tmc21 - tmc26) + (bjp26 - bjp21)) / 2.0


def uniform_swing_prediction(seats, swing_pct=None):
    """Baseline prediction of `BJP won` per seat."""
    if swing_pct is None:
        swing_pct = statewide_swing(seats)
    return (apply_uniform_swing(seats, swing_pct) == "BJP").astype(int)


# --------------------------------------------------------------------------
# fitted models
# --------------------------------------------------------------------------

def _pipeline(estimator, numeric):
    return Pipeline(
        [
            (
                "prep",
                ColumnTransformer(
                    [
                        ("num", StandardScaler(), numeric),
                        (
                            "cat",
                            OneHotEncoder(handle_unknown="ignore"),
                            CATEGORICAL,
                        ),
                    ]
                ),
            ),
            ("clf", estimator),
        ]
    )


def build_models():
    """The models compared in phase 2, each with the feature set it may use."""
    return {
        "logistic (pre)": (
            _pipeline(LogisticRegression(max_iter=2000, random_state=SEED), NUMERIC_PRE),
            PRE_FEATURES,
        ),
        "logistic (post)": (
            _pipeline(LogisticRegression(max_iter=2000, random_state=SEED), NUMERIC_POST),
            POST_FEATURES,
        ),
        "gradient boosting (pre)": (
            _pipeline(
                GradientBoostingClassifier(random_state=SEED), NUMERIC_PRE
            ),
            PRE_FEATURES,
        ),
        "gradient boosting (post)": (
            _pipeline(
                GradientBoostingClassifier(random_state=SEED), NUMERIC_POST
            ),
            POST_FEATURES,
        ),
    }


def cross_val_prediction(model, seats, features, y, folds=5):
    """Out-of-fold predictions, so no seat is scored by a model that saw it."""
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=SEED)
    return cross_val_predict(model, seats[features], y, cv=cv)


def evaluate(pred, y, actual_bjp_seats=None):
    """Seat-count error and per-seat accuracy. Both, because they differ."""
    pred = np.asarray(pred)
    y = np.asarray(y)
    if actual_bjp_seats is None:
        actual_bjp_seats = int(y.sum())
    predicted_seats = int(pred.sum())
    return {
        "bjp_seats_predicted": predicted_seats,
        "bjp_seats_actual": actual_bjp_seats,
        "seat_error": predicted_seats - actual_bjp_seats,
        "seats_correct": int((pred == y).sum()),
        "accuracy": float((pred == y).mean()),
    }


def run_comparison(seats=None):
    """Baseline against every model. Returns a tidy frame, worst first."""
    if seats is None:
        seats = load_seat_features()
    y = target(seats)

    rows = []
    # Everything has to clear this first. 207 of 293 seats went BJP, so a model
    # that just says "BJP" every time is already right 70.6% of the time.
    rows.append(
        {"model": "always BJP", "features": "none", **evaluate(np.ones(len(seats), dtype=int), y)}
    )

    swing = statewide_swing(seats)
    rows.append(
        {"model": f"uniform swing ({swing:.2f} pts)", "features": "none", **evaluate(uniform_swing_prediction(seats, swing), y)}
    )

    for name, (model, features) in build_models().items():
        pred = cross_val_prediction(model, seats, features, y)
        rows.append({"model": name, "features": "post" if "post" in name else "pre", **evaluate(pred, y)})

    return pd.DataFrame(rows).sort_values("accuracy").reset_index(drop=True)


if __name__ == "__main__":
    seats = load_seat_features()
    print(f"actual statewide two-party swing: {statewide_swing(seats):.2f} points\n")
    table = run_comparison(seats)
    print(table.to_string(index=False))
