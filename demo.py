# ───────────────────────────────────────────────────────────────
# app.py  ·  Kenya White‑Space Dashboard (All Counties Table Only)
# ───────────────────────────────────────────────────────────────
from __future__ import annotations
import io, json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ╭─────────────── USER‑EDITABLE CONSTANTS ─────────────────────╮
GEOJSON_PATH = Path("kenya.geojson")
GEOJSON_KEY  = "properties.COUNTY_NAM"
BRANDS = [
    "4U","AFRISENSE","BELLEZA","DETREX","DIRIA","DIVA","FRESCO","FRESH FRI",
    "FRESH ZAIT","FRYKING","FRYMATE","HOTEL SOAP","MEDIMIX","MPISHI POA",
    "NDUME","ONJA","POPCO","RAINBOW","SALIT","SAWA","USHINDI","WHITEWASH",
]
COLOR_SCALES = {
    "Viridis": px.colors.sequential.Viridis,
    "Turbo":   px.colors.sequential.Turbo,
    "Plasma":  px.colors.sequential.Plasma,
    "Inferno": px.colors.sequential.Inferno,
}
MAP_STYLES = {
    "OpenStreetMap": "open-street-map",
    "Carto Light":   "carto-positron",
    "Carto Dark":    "carto-darkmatter",
    "Satellite":     "satellite-streets",
}
COUNTIES = [
    'Mombasa','Kwale','Kilifi','Tana River','Lamu','Taita-Taveta','Garissa','Wajir',
    'Mandera','Marsabit','Isiolo','Meru','Tharaka-Nithi','Embu','Kitui','Machakos',
    'Makueni','Nyandarua','Nyeri','Kirinyaga',"Murang'a",'Kiambu','Turkana',
    'West Pokot','Samburu','Trans Nzoia','Uasin Gishu','Elgeyo-Marakwet','Nandi',
    'Baringo','Laikipia','Nakuru','Narok','Kajiado','Kericho','Bomet','Kakamega',
    'Vihiga','Bungoma','Busia','Siaya','Kisumu','Homa Bay','Migori','Kisii',
    'Nyamira','Nairobi'
]
# ╰──────────────────────────────────────────────────────────────╯

# ───────────────────  Streamlit page settings  ──────────────────
st.set_page_config("Kenya White‑Space Dashboard", "🗺️", layout="wide")
st.markdown(
    "<style>#MainMenu,footer{visibility:hidden}"
    "section[data-testid='stSidebar']{width:270px}</style>",
    unsafe_allow_html=True,
)

# ────────────────────  Load GeoJSON & data  ─────────────────────
@st.cache_data
def load_geojson(path: Path) -> dict:
    if not path.exists():
        st.error(f"GeoJSON not found at {path.resolve()}"); st.stop()
    return json.loads(path.read_text(encoding="utf-8"))

@st.cache_data
def make_full_grid_df() -> pd.DataFrame:
    rng  = np.random.default_rng(42)
    grid = pd.MultiIndex.from_product([BRANDS, COUNTIES],
                                      names=["Brand","County"]).to_frame(index=False)
    grid["White_Space_Score"] = rng.uniform(0, 100, len(grid)).round(2)
    grid["County_key"]        = grid["County"].str.upper()
    return grid

geojson = load_geojson(GEOJSON_PATH)
df      = make_full_grid_df()

# ─────────────────────  Sidebar controls  ──────────────────────
st.sidebar.header("Filters & Options")
sel_brand  = st.sidebar.selectbox("Select Brand", BRANDS)
sel_scale  = st.sidebar.selectbox("Colour Scale", list(COLOR_SCALES))
sel_style  = st.sidebar.selectbox("Map Background", MAP_STYLES)
highlight_county = st.sidebar.selectbox("Highlight a County", ["(None)"]+COUNTIES)
st.sidebar.markdown("---")

# ─────────────────────  Filter for brand  ───────────────────────
brand_df = df[df["Brand"] == sel_brand]

# ───────────────────  Choropleth Map  ───────────────────────────
st.subheader(f"📊 Distribution Opportunities — {sel_brand}")

fig = px.choropleth_mapbox(
    brand_df,
    geojson         = geojson,
    locations       = "County_key",
    featureidkey    = GEOJSON_KEY,
    color           = "White_Space_Score",
    color_continuous_scale = COLOR_SCALES[sel_scale],
    range_color     = (0, 100),
    mapbox_style    = MAP_STYLES[sel_style],
    center          = {"lat": 0.4, "lon": 37.8},
    zoom            = 5.5,
    opacity         = 0.8,
    hover_data      = {"County":True,"White_Space_Score":True},
    height=650,
)

# ─── Optional highlight of a chosen county ───
if highlight_county != "(None)":
    hi_row = brand_df[brand_df["County"] == highlight_county]
    if not hi_row.empty:
        fig.add_trace(
            go.Choroplethmapbox(
                geojson = geojson,
                locations=[highlight_county.upper()],
                featureidkey=GEOJSON_KEY,
                showscale=False,
                marker_line_color="red",
                marker_line_width=4,
                z=[100], colorscale=[[0,"rgba(0,0,0,0)"],[1,"rgba(0,0,0,0)"]],
                hoverinfo="skip",
            )
        )

fig.update_layout(margin=dict(l=0,r=0,t=0,b=0))
st.plotly_chart(fig, use_container_width=True)

# ─────────────────────  All County Table View  ─────────────────────
st.subheader("📋 White Space Scores – All Counties")
sorted_df = brand_df[["County", "White_Space_Score"]].sort_values(by="White_Space_Score", ascending=False).reset_index(drop=True)
st.dataframe(sorted_df, use_container_width=True, height=400)
