"""Swing slider.

Drag a statewide swing, watch the seat count move. Everything here comes out
of src/, so the app can't disagree with the notebooks.

    streamlit run app/streamlit_app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import altair as alt
import pandas as pd
import streamlit as st

from src.features import load_seat_features
from src.models import apply_uniform_swing, statewide_swing, target, uniform_swing_prediction
from src.simulate import LEAD_BETA, run, summarise

TMC_GREEN = "#1f9e57"
BJP_ORANGE = "#e8720c"

st.set_page_config(page_title="Bengal swing model", layout="wide")


@st.cache_data
def get_seats():
    return load_seat_features()


seats = get_seats()
actual_swing = statewide_swing(seats)
actual_seats = int(target(seats).sum())

st.title("Bengal election swing model")
st.caption(
    f"West Bengal assembly, 2021 to 2026. {len(seats)} seats that polled in both years. "
    "Falta held no poll in 2026 and is excluded."
)

swing = st.slider(
    "Swing from TMC to BJP (percentage points)",
    min_value=-10.0,
    max_value=20.0,
    value=float(round(actual_swing, 1)),
    step=0.1,
    help=f"What actually happened was {actual_swing:.2f} points.",
)

with st.sidebar:
    st.header("Assumptions")
    lead_scaling = st.checkbox(
        "Swing scales with the seat's 2021 lead",
        value=True,
        help=(
            "BJP gained about one extra point for every ten points of lead TMC "
            "had to defend. Off = plain uniform swing."
        ),
    )
    swing_sd = st.slider(
        "Uncertainty in the statewide swing (sd, points)", 0.0, 5.0, 2.0, 0.5
    )
    n_draws = st.select_slider("Simulation draws", [1_000, 5_000, 10_000], value=5_000)
    st.caption(
        "The swing uncertainty is an assumption, not something this data can "
        "measure. One election can't tell you how wrong a forecast would have been."
    )

called = apply_uniform_swing(seats, swing)
bjp_seats = int((called == "BJP").sum())
tmc_seats = int((called == "TMC").sum())
third_seats = len(seats) - bjp_seats - tmc_seats

left, mid, right = st.columns(3)
left.metric("BJP", bjp_seats, delta=bjp_seats - actual_seats, help="vs the actual 2026 result")
mid.metric("TMC", tmc_seats, delta=tmc_seats - int((seats.winner_party_2026 == "TMC").sum()))
right.metric("Others", third_seats)

if bjp_seats >= 147:
    st.success(f"BJP majority at this swing: {bjp_seats} of {len(seats)}, 147 needed.")
else:
    st.warning(f"No BJP majority at this swing: {bjp_seats} of {len(seats)}, 147 needed.")

st.divider()

tab_curve, tab_dist, tab_misses = st.tabs(
    ["Seats against swing", "Simulated distribution", "Where it gets it wrong"]
)

with tab_curve:
    grid = [round(x * 0.25 - 10, 2) for x in range(0, 121)]
    curve = pd.DataFrame(
        {"swing": grid, "bjp_seats": [int(uniform_swing_prediction(seats, s).sum()) for s in grid]}
    )
    chart = (
        alt.Chart(curve)
        .mark_line(color=BJP_ORANGE, strokeWidth=2.5)
        .encode(
            x=alt.X("swing:Q", title="assumed two-party swing to BJP (points)"),
            y=alt.Y("bjp_seats:Q", title="BJP seats"),
            tooltip=["swing", "bjp_seats"],
        )
    )
    marks = (
        alt.Chart(pd.DataFrame({"swing": [swing]}))
        .mark_rule(color="#222", strokeDash=[5, 4])
        .encode(x="swing:Q")
    )
    actual_line = (
        alt.Chart(pd.DataFrame({"y": [actual_seats]}))
        .mark_rule(color="#8a8a8a", strokeDash=[2, 3])
        .encode(y="y:Q")
    )
    st.altair_chart((chart + marks + actual_line).properties(height=380), use_container_width=True)
    st.caption(
        f"Around the actual result one point of swing is worth about 12 seats. "
        f"The grey line is BJP's actual {actual_seats}."
    )

with tab_dist:
    counts = run(
        seats,
        n_draws=n_draws,
        swing_mean=swing,
        swing_sd=swing_sd,
        lead_beta=LEAD_BETA if lead_scaling else 0.0,
    )
    got = summarise(counts, actual=actual_seats)

    a, b, c = st.columns(3)
    a.metric("Median", f"{got['median']:.0f}")
    b.metric("90% of draws", f"{got['p05']:.0f} – {got['p95']:.0f}")
    c.metric("BJP majority", f"{got['majority_prob']*100:.0f}%")

    hist = (
        alt.Chart(pd.DataFrame({"seats": counts}))
        .mark_bar(color=BJP_ORANGE, opacity=0.85)
        .encode(
            x=alt.X("seats:Q", bin=alt.Bin(maxbins=60), title="BJP seats out of 293"),
            y=alt.Y("count()", title="draws"),
        )
    )
    st.altair_chart(hist.properties(height=360), use_container_width=True)

with tab_misses:
    pred = uniform_swing_prediction(seats, swing)
    wrong = pred != target(seats)
    st.write(f"**{int(wrong.sum())} seats called wrong** at a swing of {swing:.1f} points.")
    table = seats.loc[
        wrong,
        ["ac_no", "ac_name", "region", "winner_party_2021", "winner_party_2026", "tmc_lead_2021"],
    ].copy()
    table["called"] = ["BJP" if p else "not BJP" for p in pred[wrong]]
    st.dataframe(
        table.sort_values("tmc_lead_2021").reset_index(drop=True),
        use_container_width=True,
        height=420,
    )

st.divider()
st.caption(
    "This is a retrospective fit, not a forecast. Every parameter was fitted on "
    "the election it then predicts. See docs/model_card.md."
)
