import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json, re

# ── COLOURS ───────────────────────────────────────────
NAVY_BG  = "#0F1C2E"
PANEL_BG = "#192A3E"
FG_TEXT  = "#e3e8ef"

# ── PAGE + GLOBAL CSS ────────────────────────────────
st.set_page_config(page_title="Kenya County Opportunity Dashboard",
                   layout="wide", page_icon="📍")

MAP_TABLE_HEIGHT = 760            # 🔧 tweak here if needed
MAP_TABLE_RATIO  = [5, 3]         # 🔧 map : table width ratio  (≈62 % : 38 %)

st.markdown(
    f"""
    <style>
        html, body, [data-testid="stApp"] {{
            background:{NAVY_BG};
            color:{FG_TEXT};
        }}
        .stDataFrame {{ background:{NAVY_BG}; }}
        /* force iframe (plotly map) to fixed height */
        div.map-container iframe {{
            height:{MAP_TABLE_HEIGHT}px !important;
        }}
        /* shrink selectbox row padding */
        section[data-testid="column"] {{ padding:0 8px; }}
    </style>
    """,
    unsafe_allow_html=True)

st.title("📍 Kenya County Opportunity Dashboard")

# ── HELPER ----------------------------------------------------------
def detect(patterns, cols):
    norm = {c: re.sub(r"[\s_]", "", c.lower()) for c in cols}
    for col, slug in norm.items():
        if any(re.search(p, slug) for p in patterns):
            return col
    return None

# ── LOAD DATA -------------------------------------------------------
@st.cache_data
def load_counties():
    df  = pd.read_csv("Merged_Data_with_Opportunity_Score.csv")
    geo = json.load(open("kenya.geojson", "r", encoding="utf-8"))
    for f in geo["features"]:
        nm = f["properties"].get("COUNTY_NAM") or ""
        f["properties"]["COUNTY_KEY"] = nm.title().strip()
    return df, geo

@st.cache_data
def load_points():
    raw  = pd.read_excel("rtm_lat_log.xlsx")
    cols = list(raw.columns)
    lat  = detect([r"^lat"], cols)
    lon  = detect([r"(lon|lng)"], cols)
    dist = detect([r"distrib|dealer|partner|outlet"], cols)
    if None in (lat, lon, dist):
        st.stop()
    pts            = raw[[dist, lat, lon]].copy()
    pts.columns    = ["Distributor", "Latitude", "Longitude"]
    pts["Latitude"]= pd.to_numeric(pts["Latitude"],  errors="coerce")
    pts["Longitude"]=pd.to_numeric(pts["Longitude"], errors="coerce")
    return pts.dropna(subset=["Latitude","Longitude"])

df,  geojson = load_counties()
pts_df       = load_points()

# ── COMPACT FILTER ROW ----------------------------------------------
f1, f2 = st.columns([1, 5])           # narrow cell for filter
with f1:
    brands = ["All"] + sorted(df["BRAND"].dropna().unique())
    choose = st.selectbox("Select Brand", brands)

view_df = df if choose == "All" else df[df["BRAND"] == choose]

# ── CHOROPLETH -------------------------------------------------------
county_avg = (view_df.groupby("County", as_index=False)["AWS"]
                       .mean()
                       .assign(County=lambda d: d["County"].str.title().str.strip()))

fig = px.choropleth_mapbox(
    county_avg, geojson=geojson,
    locations="County", featureidkey="properties.COUNTY_KEY",
    color="AWS",
    color_continuous_scale="YlOrRd",
    mapbox_style="carto-darkmatter",
    center={"lat":0.23,"lon":37.9}, zoom=5.5,
    opacity=0.9, height=MAP_TABLE_HEIGHT)

fig.add_trace(go.Densitymapbox(
    lat=pts_df["Latitude"], lon=pts_df["Longitude"],
    z=[1]*len(pts_df), radius=14, opacity=0.7,
    colorscale=[[0,"rgba(0,120,255,0.25)"],
                [0.3,"rgba(0,120,255,0.55)"],
                [1,"rgba(0,120,255,0.9)"]],
    showscale=False, name="Distributor Density"))

fig.update_layout(
    paper_bgcolor=NAVY_BG, font_color=FG_TEXT,
    margin=dict(l=0,r=0,t=15,b=0))

# ── SIDE-BY-SIDE PANELS (MAP + TABLE) -------------------------------
map_col, table_col = st.columns(MAP_TABLE_RATIO)

with map_col:
    st.plotly_chart(fig, use_container_width=True,
                    config=dict(displayModeBar=True))

with table_col:
    st.markdown("### 📊 Detailed Data Table")
    st.dataframe(
        view_df[["Territory","County","BRAND","subcategory",
                 "Opportunity Score","AWS"]],
        height=MAP_TABLE_HEIGHT,
        use_container_width=True
    )
