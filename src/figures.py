"""Charts for phase 3.

Four, each answering one question. Written to figures/ as PNG.
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.features import ROOT, load_seat_features
from src.models import run_comparison, statewide_swing, target, uniform_swing_prediction

FIG_DIR = ROOT / "figures"

TMC_GREEN = "#1f9e57"
BJP_ORANGE = "#e8720c"
GREY = "#8a8a8a"
INK = "#222222"


def _style(ax, title, xlabel=None, ylabel=None):
    ax.set_title(title, loc="left", fontsize=12, color=INK, pad=12)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9, color=INK)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9, color=INK)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GREY)
    ax.tick_params(colors=INK, labelsize=9)
    ax.grid(axis="y", color=GREY, alpha=0.18, linewidth=0.6)
    ax.set_axisbelow(True)


def fig_local_swing_spread(seats):
    """Uniform swing assumes every seat moves alike. Here's how far off that is."""
    statewide = statewide_swing(seats)
    local = (seats["swing_bjp"] - seats["swing_tmc"]) / 2.0

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(local, bins=35, color=BJP_ORANGE, alpha=0.8, edgecolor="white", linewidth=0.5)
    ax.axvline(statewide, color=INK, linestyle="--", linewidth=1.4)
    ax.text(
        statewide + 0.5,
        ax.get_ylim()[1] * 0.92,
        f"statewide {statewide:.1f}",
        fontsize=9,
        color=INK,
    )
    _style(
        ax,
        f"Every seat's own swing, against the one number the baseline uses\n"
        f"sd {local.std():.1f} points, range {local.min():.0f} to {local.max():.0f}",
        "two-party swing to BJP (points)",
        "seats",
    )
    fig.tight_layout()
    fig.savefig(FIG_DIR / "01_local_swing_spread.png", dpi=150)
    plt.close(fig)


def fig_miss_by_tipping_distance(seats):
    """The baseline fails where the swing is decisive, not where seats are close."""
    statewide = statewide_swing(seats)
    tipping = 2 * statewide
    dist = (seats["tmc_lead_2021"] - tipping).abs()
    missed = (uniform_swing_prediction(seats) != target(seats)).values

    frame = pd.DataFrame({"dist": dist, "missed": missed})
    frame["band"] = pd.cut(
        frame["dist"], [0, 3, 6, 10, 20, 200], labels=["0-3", "3-6", "6-10", "10-20", "20+"]
    )
    grouped = frame.groupby("band", observed=True)["missed"].agg(["sum", "count", "mean"])

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(
        grouped.index.astype(str), grouped["mean"] * 100, color=BJP_ORANGE, width=0.62
    )
    for bar, (n, total) in zip(bars, zip(grouped["sum"], grouped["count"])):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.9,
            f"{n}/{total}",
            ha="center",
            fontsize=9,
            color=INK,
        )
    _style(
        ax,
        f"Where uniform swing gets it wrong\n"
        f"a {statewide:.1f}-point swing moves a margin by {tipping:.1f}, so this is "
        f"distance from that line",
        f"2021 TMC lead, distance from {tipping:.1f} points",
        "seats called wrong (%)",
    )
    fig.tight_layout()
    fig.savefig(FIG_DIR / "02_miss_by_tipping_distance.png", dpi=150)
    plt.close(fig)


def fig_model_comparison(seats):
    table = run_comparison(seats).sort_values("accuracy")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colours = [GREY if f == "none" else BJP_ORANGE for f in table["features"]]
    bars = ax.barh(table["model"], table["seats_correct"], color=colours, height=0.62)
    for bar, acc in zip(bars, table["accuracy"]):
        ax.text(
            bar.get_width() - 4,
            bar.get_y() + bar.get_height() / 2,
            f"{acc*100:.1f}%",
            va="center",
            ha="right",
            fontsize=9,
            color="white",
        )
    ax.set_xlim(180, 293)
    _style(ax, "Seats called right, out of 293\ngrey = no features, cross-validated over 5 folds", "seats correct")
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GREY, alpha=0.18, linewidth=0.6)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "03_model_comparison.png", dpi=150)
    plt.close(fig)


def fig_swing_curve(seats):
    """How the seat total responds to the swing you assume."""
    swings = np.arange(-5, 21, 0.25)
    counts = [uniform_swing_prediction(seats, s).sum() for s in swings]
    statewide = statewide_swing(seats)
    actual = int(target(seats).sum())

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(swings, counts, color=BJP_ORANGE, linewidth=2)
    ax.axhline(actual, color=GREY, linestyle=":", linewidth=1.2)
    ax.axvline(statewide, color=INK, linestyle="--", linewidth=1.2)
    ax.plot([statewide], [uniform_swing_prediction(seats, statewide).sum()], "o", color=INK, ms=6)
    ax.text(statewide + 0.4, 30, f"actual swing {statewide:.1f}", fontsize=9, color=INK)
    ax.text(-4.6, actual + 6, f"BJP actually won {actual}", fontsize=9, color=GREY)
    _style(
        ax,
        "Around the actual result, one point of swing is worth about 12 seats\n"
        "which is why the seat total is so sensitive to the assumption",
        "assumed two-party swing to BJP (points)",
        "BJP seats the baseline calls",
    )
    fig.tight_layout()
    fig.savefig(FIG_DIR / "04_swing_curve.png", dpi=150)
    plt.close(fig)


def build_all():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    seats = load_seat_features()
    fig_local_swing_spread(seats)
    fig_miss_by_tipping_distance(seats)
    fig_model_comparison(seats)
    fig_swing_curve(seats)
    return sorted(p.name for p in FIG_DIR.glob("*.png"))


if __name__ == "__main__":
    for name in build_all():
        print("  figures/" + name)
