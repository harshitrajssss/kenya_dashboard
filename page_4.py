import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import re

# ─────────────────────────────────────────
# PAGE SETUP
# ─────────────────────────────────────────
st.set_page_config(page_title="Kenya County Opportunity Dashboard", layout="wide")
st.title("📍 Kenya County Opportunity Dashboard")

# ─────────────────────────────────────────
# LOAD COUNTY DATA
# ─────────────────────────────────────────
@st.cache_data
def load_county_data():
    df = pd.read_csv("Merged_Data_with_Opportunity_Score.csv")
    with open("kenya.geojson", "r", encoding="utf-8") as f:
        geo = json.load(f)
    for feat in geo["features"]:
        name = feat["properties"].get("COUNTY_NAM")
        feat["properties"]["COUNTY_KEY"] = name.title().strip() if name else "Unknown"
    return df, geo

# ─────────────────────────────────────────
# LOAD DISTRIBUTOR POINTS
# ─────────────────────────────────────────
def _detect_column(patterns, columns):
    norm = {c: re.sub(r"[\s_]", "", c.lower()) for c in columns}
    for col, normed in norm.items():
        if any(re.search(p, normed) for p in patterns):
            return col
    return None

def load_distributor_points():
    df_raw = pd.read_excel("rtm_lat_log.xlsx")
    cols = list(df_raw.columns)

    lat_col  = _detect_column([r"^lat", r"latitude"], cols)
    lon_col  = _detect_column([r"^lon", r"lng", r"longitude"], cols)
    dist_col = _detect_column([r"distrib", r"dealer", r"partner", r"outlet"], cols)

    missing = [n for n, c in [("Latitude", lat_col), ("Longitude", lon_col), ("Distributor", dist_col)] if c is None]
    if missing:
        st.error(
            "❌ Could not find required column(s): " + ", ".join(missing) +
            "\n\nFound columns: " + ", ".join(cols) +
            "\n\nPlease correct the Excel headers and try again."
        )
        st.stop()

    df = df_raw[[dist_col, lat_col, lon_col]].copy()
    df.columns = ["Distributor", "Latitude", "Longitude"]
    df["Latitude"]  = pd.to_numeric(df["Latitude"],  errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
    df.dropna(subset=["Latitude", "Longitude"], inplace=True)
    return df

# ─────────────────────────────────────────
# LOAD EVERYTHING
# ─────────────────────────────────────────
df, geojson = load_county_data()
pts_df = load_distributor_points()

# ─────────────────────────────────────────
# COUNTY CHOROPLETH
# ─────────────────────────────────────────
st.subheader("🗺️ Opportunity Score by County")
county_avg = df.groupby("County", as_index=False)["Opportunity Score"].mean()
county_avg["County"] = county_avg["County"].str.title().str.strip()

fig = px.choropleth_mapbox(
    county_avg,
    geojson=geojson,
    locations="County",
    featureidkey="properties.COUNTY_KEY",
    color="Opportunity Score",
    color_continuous_scale="YlOrRd",
    mapbox_style="carto-positron",
    zoom=5.5,
    center={"lat": 0.23, "lon": 37.9},
    opacity=0.7
)

# ─────────────────────────────────────────
# ADD HEATMAP OVERLAY FOR ALL DISTRIBUTORS
# ─────────────────────────────────────────
fig.add_trace(
    go.Densitymapbox(
        lat=pts_df["Latitude"],
        lon=pts_df["Longitude"],
        z=[1]*len(pts_df),
        radius=12,  # smaller radius = tighter heatmap
        colorscale=[[0, "rgba(0,0,255,0.1)"], [1, "rgba(0,0,255,0.4)"]],
        showscale=False,
        opacity=0.3,
        name="Distributor Presence"
    )
)

fig.update_layout(
    margin=dict(l=0, r=0, t=30, b=0),
    paper_bgcolor="#f9f9f9",
    legend_title_text=""
)

st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────
# DETAIL TABLE
# ─────────────────────────────────────────
st.subheader("📊 Detailed Data Table")
st.dataframe(
    df[[
        "Territory", "County", "BRAND", "subcategory",
        "Opportunity Score", "AWS", "White Space Score"
    ]],
    height=400,
    use_container_width=True
)
