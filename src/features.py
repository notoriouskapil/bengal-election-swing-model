"""Seat-level feature table.

Reads data/raw/bengal_elections.db and writes one row per constituency with
the 2021 result, the 2026 result and whatever else the models need. Phase 1.

Nothing here writes to the raw database. Output goes to data/model/.
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DB = ROOT / "data" / "raw" / "bengal_elections.db"
MODEL_DIR = ROOT / "data" / "model"

# Falta (ac_no 144) held no poll in 2026. Always filter on seat_status rather
# than hardcoding this, it's here so the number is written down somewhere.
SEATS_TOTAL = 294
SEATS_POLLED_2026 = 293


def connect(db_path=RAW_DB):
    """Open the raw database read-only so nothing can scribble on it."""
    if not Path(db_path).exists():
        raise FileNotFoundError(f"no database at {db_path}")
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def build_seat_features():
    """One row per seat. Not written yet."""
    raise NotImplementedError("phase 1")


if __name__ == "__main__":
    build_seat_features()
