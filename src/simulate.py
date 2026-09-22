"""Monte Carlo over the swing.

A point estimate of the seat count hides how sensitive the total is to the
swing assumption, given how many 2021 margins were under 15 points. So: draw a
swing, recount all 293 seats, repeat, keep the distribution.

Draws land in results/sims/ and are gitignored — they get large fast.
Phase 4.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIMS_DIR = ROOT / "results" / "sims"

N_DRAWS = 10_000
SEED = 2026


def run(seats, n_draws=N_DRAWS, seed=SEED):
    raise NotImplementedError("phase 4")
