"""Monte Carlo over the swing.

A single seat total hides how much rests on the swing assumption. Phase 3
measured the two things that move it:

  * the statewide swing itself, which in a forecast you would not know
  * per-seat deviation from it, standard deviation 4.99 points in this data

So: draw a statewide swing, add per-seat noise, recount all 293 seats, repeat.
The output is a distribution of BJP seat counts rather than one number.

Local deviation is split in two, because phase 3 found the misses cluster by
region. Part of it is a shock shared by every seat in a region, the rest is
seat-specific. With `region_share=0` it collapses to independent seat noise.

Draws are written to results/sims/ and gitignored, they get large.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from src.features import ROOT, load_seat_features
from src.models import statewide_swing, target

SIMS_DIR = ROOT / "results" / "sims"

N_DRAWS = 10_000
SEED = 2026

# Measured in phase 3: sd of each seat's own two-party swing around the state.
LOCAL_SD = 4.99

# The swing was not independent of the seat. Regressing each seat's own swing
# on its 2021 TMC lead gives a slope of about 0.0985: BJP gained roughly one
# extra point for every ten points of lead TMC had to defend. R^2 is only
# 0.11, but it pushes hard on the seat total because it acts exactly on the
# safe seats the baseline never flips. Residual sd after taking it out is 4.71.
# Set lead_beta=0 for a pure uniform swing with symmetric noise.
LEAD_BETA = 0.0985
RESIDUAL_SD = 4.71
# Statewide swing uncertainty. A forecaster's polling error, not something
# this data can tell us, so it's an assumption and labelled as one.
SWING_SD = 2.0
# How much of the local deviation is a regional shock rather than seat noise.
REGION_SHARE = 0.35


def _recount(tmc21, bjp21, third, seat_swings):
    """Vectorised recount. seat_swings is (draws, seats)."""
    tmc = tmc21[None, :] - seat_swings
    bjp = bjp21[None, :] + seat_swings
    bjp_wins = (bjp > tmc) & (bjp > third[None, :])
    return bjp_wins.sum(axis=1)


def run(
    seats=None,
    n_draws=N_DRAWS,
    swing_mean=None,
    swing_sd=SWING_SD,
    local_sd=RESIDUAL_SD,
    region_share=REGION_SHARE,
    lead_beta=LEAD_BETA,
    seed=SEED,
    save=False,
):
    """Return an array of BJP seat counts, one per draw."""
    if seats is None:
        seats = load_seat_features()
    if swing_mean is None:
        swing_mean = statewide_swing(seats)

    rng = np.random.default_rng(seed)
    n_seats = len(seats)

    tmc21 = seats["tmc_pct_2021"].to_numpy()
    bjp21 = seats["bjp_pct_2021"].to_numpy()
    third = seats["third_party_hold_2021"].to_numpy()

    statewide = rng.normal(swing_mean, swing_sd, size=(n_draws, 1))

    region_sd = local_sd * np.sqrt(region_share)
    seat_sd = local_sd * np.sqrt(1.0 - region_share)

    codes, _ = pd.factorize(seats["region"])
    region_shock = rng.normal(0.0, region_sd, size=(n_draws, codes.max() + 1))
    regional = region_shock[:, codes]

    seat_noise = rng.normal(0.0, seat_sd, size=(n_draws, n_seats))

    # Swing that scales with what the incumbent had to defend. Centred on the
    # mean lead so the statewide draw stays the statewide swing.
    lead = seats["tmc_lead_2021"].to_numpy()
    drift = lead_beta * (lead - lead.mean())

    counts = _recount(
        tmc21, bjp21, third, statewide + drift[None, :] + regional + seat_noise
    )

    if save:
        SIMS_DIR.mkdir(parents=True, exist_ok=True)
        np.save(SIMS_DIR / f"bjp_seats_{n_draws}.npy", counts)
    return counts


def summarise(counts, actual=None):
    """Central estimate and interval. Percentiles, not a standard error, the
    distribution isn't symmetric near the top of the range."""
    counts = np.asarray(counts)
    out = {
        "draws": int(counts.size),
        "mean": float(counts.mean()),
        "median": float(np.median(counts)),
        "sd": float(counts.std(ddof=1)),
        "p05": float(np.percentile(counts, 5)),
        "p50": float(np.percentile(counts, 50)),
        "p95": float(np.percentile(counts, 95)),
        "min": int(counts.min()),
        "max": int(counts.max()),
    }
    if actual is not None:
        out["actual"] = int(actual)
        out["actual_percentile"] = float((counts <= actual).mean() * 100)
        out["majority_prob"] = float((counts >= 147).mean())
    return out


def sensitivity(seats=None, n_draws=4_000):
    """How much of the spread comes from which assumption."""
    if seats is None:
        seats = load_seat_features()
    rows = []
    for label, kwargs in [
        ("uniform, nothing random", dict(swing_sd=0.0, local_sd=0.0, lead_beta=0.0)),
        ("+ lead-scaled swing", dict(swing_sd=0.0, local_sd=0.0)),
        ("+ local noise", dict(swing_sd=0.0)),
        ("+ uncertain statewide swing", dict()),
    ]:
        counts = run(seats, n_draws=n_draws, **kwargs)
        rows.append({"scenario": label, **summarise(counts)})
    return pd.DataFrame(rows)[["scenario", "mean", "sd", "p05", "p95"]]


if __name__ == "__main__":
    seats = load_seat_features()
    actual = int(target(seats).sum())
    counts = run(seats, save=True)
    got = summarise(counts, actual=actual)

    print(f"{got['draws']:,} draws, BJP seats out of 293\n")
    print(f"  mean    {got['mean']:.1f}")
    print(f"  median  {got['median']:.0f}")
    print(f"  90% of draws between {got['p05']:.0f} and {got['p95']:.0f}")
    print(f"  actual  {got['actual']}, at the {got['actual_percentile']:.0f}th percentile")
    print(f"  majority (147+): {got['majority_prob']*100:.1f}% of draws\n")
    print(sensitivity(seats).to_string(index=False))
