"""What the models are doing, and where they fail.

Not in the original file plan. It grew out of models.py once the residual
work needed more than a couple of functions.

Two questions:

  1. Which features move a prediction? Standardised logistic coefficients,
     plus permutation importance as a check that the coefficients aren't an
     artefact of collinear inputs.
  2. Which seats does the baseline get wrong, and do the misses share
     anything?

The second matters more. Uniform swing already gets 246 of 293, so the
remaining 47 are where the state stopped behaving uniformly.
"""

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from src.features import load_seat_features
from src.models import (
    NUMERIC_PRE,
    PRE_FEATURES,
    SEED,
    build_models,
    statewide_swing,
    target,
    uniform_swing_prediction,
)


def logistic_coefficients(seats=None):
    """Standardised coefficients from the best model, largest effect first.

    Inputs are scaled in the pipeline, so these are comparable across
    features. Positive means the feature pushes the seat towards BJP.
    """
    if seats is None:
        seats = load_seat_features()
    model, features = build_models()["logistic (pre)"]
    model.fit(seats[features], target(seats))

    names = list(NUMERIC_PRE) + list(
        model.named_steps["prep"].named_transformers_["cat"].get_feature_names_out()
    )
    coefs = model.named_steps["clf"].coef_[0]
    out = pd.DataFrame({"feature": names, "coefficient": coefs})
    out["absolute"] = out["coefficient"].abs()
    return out.sort_values("absolute", ascending=False).reset_index(drop=True)


def permutation_table(seats=None, repeats=30):
    """How much accuracy drops when each feature is shuffled."""
    if seats is None:
        seats = load_seat_features()
    model, features = build_models()["logistic (pre)"]
    y = target(seats)
    model.fit(seats[features], y)
    result = permutation_importance(
        model, seats[features], y, n_repeats=repeats, random_state=SEED
    )
    return (
        pd.DataFrame(
            {
                "feature": features,
                "importance": result.importances_mean,
                "std": result.importances_std,
            }
        )
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )


def baseline_misses(seats=None, swing_pct=None):
    """Seats the uniform swing baseline calls wrong, with why."""
    if seats is None:
        seats = load_seat_features()
    if swing_pct is None:
        swing_pct = statewide_swing(seats)

    pred = uniform_swing_prediction(seats, swing_pct)
    actual = target(seats)
    wrong = pred != actual

    out = seats.loc[
        wrong,
        [
            "ac_no",
            "ac_name",
            "region",
            "reservation",
            "winner_party_2021",
            "winner_party_2026",
            "tmc_lead_2021",
            "margin_pct_polled_2021",
            "swing_tmc",
            "swing_bjp",
            "roll_change_pct",
        ],
    ].copy()
    # The seat's own two-party swing, against the statewide number applied to it.
    out["local_swing"] = (out["swing_bjp"] - out["swing_tmc"]) / 2.0
    out["swing_vs_statewide"] = out["local_swing"] - swing_pct
    out["baseline_said"] = np.where(pred[wrong], "BJP", "not BJP")
    out["actually"] = np.where(actual[wrong], "BJP", "not BJP")
    return out.sort_values("swing_vs_statewide").reset_index(drop=True)


def miss_summary(seats=None):
    """Are the misses concentrated anywhere? Region and margin band."""
    if seats is None:
        seats = load_seat_features()
    pred = uniform_swing_prediction(seats)
    wrong = pred != target(seats)

    frame = seats[["region", "margin_pct_polled_2021"]].copy()
    frame["missed"] = wrong.values
    frame["margin_band"] = pd.cut(
        frame["margin_pct_polled_2021"],
        [0, 5, 10, 15, 25, 100],
        labels=["0-5", "5-10", "10-15", "15-25", "25+"],
    )

    by_region = (
        frame.groupby("region")["missed"].agg(["sum", "count", "mean"]).reset_index()
    )
    by_band = (
        frame.groupby("margin_band", observed=True)["missed"]
        .agg(["sum", "count", "mean"])
        .reset_index()
    )
    for f in (by_region, by_band):
        f.columns = [f.columns[0], "missed", "seats", "miss_rate"]
    return by_region.sort_values("miss_rate", ascending=False), by_band


def local_swing_spread(seats=None):
    """How far each seat's own swing sits from the statewide one.

    Uniform swing assumes this is zero everywhere. It isn't, and the spread
    is what the baseline's errors are made of.
    """
    if seats is None:
        seats = load_seat_features()
    statewide = statewide_swing(seats)
    local = (seats["swing_bjp"] - seats["swing_tmc"]) / 2.0
    return pd.DataFrame(
        {
            "ac_no": seats["ac_no"],
            "ac_name": seats["ac_name"],
            "region": seats["region"],
            "local_swing": local,
            "deviation": local - statewide,
        }
    )


if __name__ == "__main__":
    seats = load_seat_features()
    print("=== standardised logistic coefficients ===")
    print(logistic_coefficients(seats).head(8).to_string(index=False))

    spread = local_swing_spread(seats)
    print(f"\n=== local swing, statewide = {statewide_swing(seats):.2f} ===")
    print(f"  mean {spread['local_swing'].mean():.2f}  sd {spread['local_swing'].std():.2f}")
    print(f"  range {spread['local_swing'].min():.1f} to {spread['local_swing'].max():.1f}")

    misses = baseline_misses(seats)
    print(f"\n=== baseline misses: {len(misses)} seats ===")
    by_region, by_band = miss_summary(seats)
    print(by_region.to_string(index=False))
    print()
    print(by_band.to_string(index=False))
