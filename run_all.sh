#!/usr/bin/env bash
# Rebuild everything from data/raw/bengal_elections.db.
# Not wired up yet — each step lands in its own phase.
set -euo pipefail

cd "$(dirname "$0")"

echo "bengal-election-swing-model"
echo

echo "[1/4] features  -> data/model/       (phase 1, not written)"
# python3 -m src.features

echo "[2/4] models    -> results/          (phase 2, not written)"
# python3 -m src.models

echo "[3/4] simulate  -> results/sims/     (phase 4, not written)"
# python3 -m src.simulate

echo "[4/4] tests"
python3 -m pytest -q

echo
echo "done. app: streamlit run app/streamlit_app.py"
