# gantt_flexible_edges.py
# Streamlit app: move bars from both ends (start offset + duration)

import io
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

# ────────────────── 1.  Page & title ───────────────────────────
st.set_page_config(page_title="Gantt – Flexible Edges", layout="wide")
st.title("Gantt Chart – adjust BOTH start and duration")

# ────────────────── 2.  Raw task list (labels + default values)
BASE_START = datetime(2025, 6, 5)
TASKS = [
    # label                       default_offset  default_span
    ("Requirements Finalization",            0,  2),
    ("UI/UX Design",                         2,  5),
    ("Backend Development",                  3, 13),
    ("Frontend Development",                 8, 13),
    ("Integration",                         21,  4),
    ("Internal Testing",                    25,  4),
    ("CI/CD Setup",                         29,  4),
    ("Server Configuration",                29,  4),
    ("Deployment to Prod",                  33,  1),
    ("Smoke Testing",                       34,  1),
    ("UAT Test Case Prep",                  33,  1),
    ("UAT Execution",                       35,  5),
    ("Bug Fix & Retest",                    40,  3),
    ("Final Sign-off",                      43,  1),
]

COLOR = {  # same palette as before
    "Requirements Finalization": "#FDB813", "UI/UX Design": "#F97306",
    "Backend Development": "#E50000", "Frontend Development": "#FF33CC",
    "Integration": "#1E90FF", "Internal Testing": "#00CED1",
    "CI/CD Setup": "#00C957", "Server Configuration": "#9ACD32",
    "Deployment to Prod": "#FF9900", "Smoke Testing": "#FF6500",
    "UAT Test Case Prep": "#FF0040", "UAT Execution": "#FF66CC",
    "Bug Fix & Retest": "#33C1FF", "Final Sign-off": "#05C3DD",
}

# ────────────────── 3.  Sidebar – two inputs per task ──────────
st.sidebar.header("Adjust each task")

offset_days = {}   # start position from project day-0
duration_days = {} # length of bar

for lbl, def_offset, def_span in TASKS:
    st.sidebar.markdown(f"**{lbl}**")
    col_off, col_dur = st.sidebar.columns(2)
    with col_off:
        offset_days[lbl] = col_off.number_input(
            "Start +days", min_value=0, max_value=60,
            value=def_offset, step=1, key=f"off_{lbl}"
        )
    with col_dur:
        duration_days[lbl] = col_dur.number_input(
            "Duration", min_value=1, max_value=30,
            value=def_span, step=1, key=f"dur_{lbl}"
        )
    st.sidebar.markdown("---")

# ────────────────── 4.  Build DataFrame ─────────────────────────
records = []
for lbl, _, _ in TASKS:
    start  = BASE_START + timedelta(days=int(offset_days[lbl]))
    finish = start + timedelta(days=int(duration_days[lbl]))
    records.append(dict(Task=lbl, Start=start, Finish=finish))
df = pd.DataFrame(records)

axis_min = datetime(2025, 6, 1)
axis_max = datetime(2025, 7, 31)

# ────────────────── 5.  Plotly timeline ─────────────────────────
fig = px.timeline(
    df, x_start="Start", x_end="Finish", y="Task",
    color="Task", color_discrete_map=COLOR
)
fig.update_yaxes(autorange="reversed")

# consistent 1-day spacing
DAY_MS = 86_400_000
fig.update_xaxes(
    dtick=DAY_MS,
    tickformat="%d %b",
    range=[axis_min, axis_max],
    tickangle=-90,  # vertical dates like your image
    tickfont=dict(
        color="#666",       # same tone as y-axis (soft grey)
        size=12,            # match y-axis size
        family="sans-serif" # clean and consistent
    ),
    showgrid=True, gridcolor="#E5E5E5", gridwidth=1,
    showline=True, mirror=True, linecolor="#999", linewidth=1,
    ticklen=6
)


fig.update_yaxes(
    showgrid=True, gridcolor="#F4F4F4", gridwidth=1,
    showline=True, mirror=True, linecolor="#444", ticklen=6,
    tickfont=dict(color="#444")
)
fig.update_traces(width=0.55)

# frame around plot
left_margin = 12 * max(len(t[0]) for t in TASKS)
fig.update_layout(
    height=650,
    plot_bgcolor="white", paper_bgcolor="white",
    margin=dict(l=left_margin, r=40, t=70, b=70),
    showlegend=False,
    title=dict(text="Gantt Chart – Dev, Deploy, UAT",
               font=dict(size=20), x=0.5),
    shapes=[dict(type="rect", xref="paper", yref="paper",
                 x0=0, y0=0, x1=1, y1=1,
                 line=dict(color="#444", width=1), layer="below")]
)

st.plotly_chart(fig, use_container_width=True)

# ────────────────── 6.  Download buttons ────────────────────────
png_buf, html_buf = io.BytesIO(), io.StringIO()
fig.write_image(png_buf, "png", width=2000, height=1000, engine="kaleido")
fig.write_html(html_buf, full_html=True, include_plotlyjs="cdn")

c1, c2 = st.columns(2)
c1.download_button("⬇️ PNG", png_buf.getvalue(), "gantt.png", "image/png")


st.caption("Now you can move bars from **both ends** – change start offset _or_ duration.")
