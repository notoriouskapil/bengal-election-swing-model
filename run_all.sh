#!/usr/bin/env bash
# Rebuild everything from data/raw/bengal_elections.db.
set -euo pipefail

cd "$(dirname "$0")"

echo "bengal-election-swing-model"
echo

echo "[1/5] features  -> data/model/seat_features.csv"
python3 -m src.features

echo
echo "[2/5] models    -> results/model_comparison.csv"
python3 -m src.models

echo
echo "[3/5] explain"
python3 -m src.explain

echo
echo "[4/5] simulate  -> results/sims/"
python3 -m src.simulate

echo
echo "[5/5] figures   -> figures/"
python3 -m src.figures

echo
echo "tests"
python3 -m pytest -q

echo
echo "done. app: streamlit run app/streamlit_app.py"
