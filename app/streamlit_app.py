"""Swing slider.

Drag a statewide swing, watch the seat count move. Waiting on the model.
Run with: streamlit run app/streamlit_app.py
"""

import streamlit as st

st.set_page_config(page_title="Bengal swing model", layout="wide")

st.title("Bengal election swing model")
st.caption("West Bengal assembly, 2021 to 2026")

st.info("No model yet — this is a placeholder from the repo setup commit.")

swing = st.slider(
    "Swing from TMC to BJP (percentage points)",
    min_value=-20.0,
    max_value=20.0,
    value=7.8,
    step=0.1,
    help="7.8 is roughly what actually happened in 2026.",
)
st.write(f"Swing set to {swing:+.1f} points. Seat projection goes here.")
