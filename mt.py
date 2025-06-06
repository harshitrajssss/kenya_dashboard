import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from pathlib import Path
import numpy as np
import re

# ─── page / style ─────────────────────────────────────────
st.set_page_config(page_title="MT Dashboard",
                   layout="wide",
                   page_icon="📊")

NAVY, PANEL, FG = "#0F1C2E", "#192A3E", "#e3e8ef"
st.markdown(
    f"""
    <style>
      html,body,[data-testid="stApp"]{{background:{NAVY};color:{FG};font-family:'Segoe UI',sans-serif;}}
      h1,h2,h3,h4,h5,h6{{color:#fff;margin:0;}}
      .stDataFrame div[data-testid="stVerticalBlock"],.stTable{{background:{PANEL};}}
      .stPlotlyChart>div{{background:{NAVY}!important;}}
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── file paths ───────────────────────────────────────────
XL_FILE  = "WHITE_SPACE_SCORES_PAVANI.xlsx"
GEO_FILE = "kenya.geojson"

# ─── load Excel ───────────────────────────────────────────
@st.cache_data(show_spinner="Loading MT Excel …")
def load_mt():
    df = pd.read_excel(XL_FILE)

    # rename to simple names
    df = df.rename(columns={
        "County": "County",
        "BRAND": "Brand",
        "Client Market Share": "Client_Share",
        "Competitor Strength": "Competitor_Strength",
        "ERP GT Sales Coverage": "Sales",
        "White Space Score": "WS_Score",
        "CATEGORY": "Category",
    })

    df["County"]  = df["County"].astype(str).str.title().str.strip()
    df["Brand"]   = df["Brand"].astype(str).str.title().str.strip()
    df["Category"]= df["Category"].astype(str).str.title().str.strip()

    # convert shares to %
    if df["Client_Share"].max() <= 1:        # fraction → %
        df["Client_Share"]        *= 100
    if df["Competitor_Strength"].max() <= 1:
        df["Competitor_Strength"] *= 100

    return df

@st.cache_data(show_spinner="Loading Kenya GeoJSON …")
def load_geo():
    geo = json.loads(Path(GEO_FILE).read_text("utf-8"))
    for f in geo["features"]:
        f["properties"]["county_key"] = (
            f["properties"]["COUNTY_NAM"].title().strip()
        )
    return geo

df = load_mt()
geo = load_geo()

# ─── filters ──────────────────────────────────────────────
st.markdown("## Main Dashboard – SUMMARY (MT)")

c1, c2, _ = st.columns([1,1,6])
brand = c1.selectbox("Brand",    ["All"] + sorted(df["Brand"].unique()))
cat   = c2.selectbox("Category", ["All"] + sorted(df["Category"].unique()))

sub = df.copy()
if brand != "All":
    sub = sub[sub["Brand"] == brand]
if cat != "All":
    sub = sub[sub["Category"] == cat]

# ─── KPI cards ────────────────────────────────────────────
def kpi(label, value):
    st.markdown(
        f"""
        <div style='border:1px solid #ccc;border-radius:10px;
                    padding:1rem;background:#253348;height:160px;'>
          <h5 style='color:white;'>{label}</h5>
          <p style='font-size:0.9rem;color:white;'>{value}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

k1,k2,k3 = st.columns(3)
with k1: kpi("White-Space Score", f"{sub['WS_Score'].mean():,.0f}")
with k2: kpi("Client Share",      f"{sub['Client_Share'].mean():.1f}%")
with k3: kpi("Competitor Strength", f"{sub['Competitor_Strength'].mean():.1f}%")

st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)

left, _, right = st.columns([2,.05,1])

# ─── choropleth map ───────────────────────────────────────
with left:
    ws_by_county = sub.groupby("County", as_index=False)["WS_Score"].mean()
    counties = [f["properties"]["county_key"] for f in geo["features"]]
    map_df = pd.DataFrame({"County": counties}).merge(ws_by_county, how="left").fillna({"WS_Score": 0})

    fig_map = px.choropleth_map(
        map_df,
        geojson=geo,
        locations="County",
        featureidkey="properties.county_key",
        color="WS_Score",
        color_continuous_scale="YlOrRd",
        range_color=(0, 60),
        center={"lat": 0.23, "lon": 37.9},
        zoom=5.5,
        opacity=0.9,
        height=520,
    )
    fig_map.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor=NAVY,
        plot_bgcolor=NAVY,
        font_color=FG,
    )
    st.plotly_chart(fig_map, use_container_width=True)

# ─── bar charts ───────────────────────────────────────────
with right:
    share = (
        sub.groupby("County")[["Client_Share", "Competitor_Strength"]]
        .mean()
        .reset_index()
    )
    op = [1] * len(share)   # no opacity dimming because we filter by dropdowns
    fig_share = go.Figure()
    fig_share.add_bar(
        name="Client Share",
        x=share["County"],
        y=share["Client_Share"],
        marker_color="#00B4D8",
        marker_opacity=op,
    )
    fig_share.add_bar(
        name="Competitor Strength",
        x=share["County"],
        y=share["Competitor_Strength"],
        marker_color="#0077B6",
        marker_opacity=op,
    )
    fig_share.update_layout(
        barmode="stack",
        height=260,
        bargap=.15,
        title="Market Composition",
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis=dict(color="#9FB4CC", gridcolor="#24364F"),
        yaxis=dict(color="#9FB4CC", gridcolor="#24364F"),
        legend=dict(orientation="h", y=-0.25, bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_share, use_container_width=True)

    sales = sub.groupby("County")["Sales"].sum().reset_index()
    fig_sales = go.Figure(
        go.Bar(
            x=sales["County"],
            y=sales["Sales"],
            marker_color="#48CAE4",
        )
    )
    fig_sales.update_layout(
        height=260,
        bargap=.15,
        title="Sales (ERP GT Coverage)",
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(color="#9FB4CC", gridcolor="#24364F"),
        yaxis=dict(color="#9FB4CC", gridcolor="#24364F"),
        showlegend=False,
    )
    st.plotly_chart(fig_sales, use_container_width=True)

# ─── detail table ─────────────────────────────────────────
st.markdown("### Detailed Market Snapshot")
st.dataframe(
    sub[
        ["County", "Category", "Brand", "Sales",
         "Client_Share", "Competitor_Strength", "WS_Score"]
    ],
    height=350,
    use_container_width=True,
)

st.caption("Source: WHITE_SPACE_SCORES_PAVANI.xlsx · kenya.geojson")
