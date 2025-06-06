import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from pathlib import Path
import importlib.util

# ───── Page Setup ─────
st.set_page_config(page_title="Territory Deep Dive", layout="wide", initial_sidebar_state="collapsed")
NAVY, PANEL = "#0F1C2E", "#192A3E"
px.defaults.template = "plotly_dark"

st.markdown(f"""
<style>
body,.stApp{{background:{NAVY};color:#e3e8ef}}
h1,h2,h3,h4,h5{{color:#e3e8ef;margin:0}}
label div[data-baseweb="select"] div{{background:#1e293b !important;color:#e3e8ef !important}}
.metric{{font-size:.85rem;color:#7f9ab4;text-transform:uppercase;letter-spacing:.3px;margin-bottom:.25rem}}
.number{{font-size:1.55rem;font-weight:600}}
.number-green{{color:#34D399 !important}}
.number-red{{color:#F87171 !important}}
</style>
""", unsafe_allow_html=True)

# ───── File Paths ─────
GT_FILE, RTM_FILE = "GT_DATA_122_merged_filled.xlsx", "rtm_std_follow_GT_final (1).csv"
COUNTY_GJ, TERR_GJ = "kenya.geojson", "kenya_territories (1).geojson"
COMP_FILE = "PWANI_COMP_STD_final_confirmed.xlsx"

if importlib.util.find_spec("openpyxl") is None:
    st.error("⚠️ Install dependency →  pip install openpyxl")
    st.stop()

# ───── Load Data ─────
@st.cache_data(show_spinner="Loading data…")
def load_all():
    gt = pd.read_excel(GT_FILE).rename(columns=str.strip)
    gt.rename(columns={"brand": "Brand", "Markets": "Territory"}, inplace=True)
    gt["Territory"] = gt["Territory"].str.title().str.strip()
    gt["Brand"] = gt["Brand"].str.title().str.strip()

    rtm = pd.read_csv(RTM_FILE)
    rtm.columns = rtm.columns.str.strip().str.title()
    rtm[["Territory", "County", "Brand"]] = rtm[["Territory", "County", "Brand"]].apply(lambda s: s.str.title().str.strip())

    county = json.loads(Path(COUNTY_GJ).read_text("utf-8"))
    for f in county["features"]:
        f["properties"]["COUNTY_KEY"] = (f["properties"].get("COUNTY_NAM") or f["properties"].get("NAME", "")).title().strip()

    terr = json.loads(Path(TERR_GJ).read_text("utf-8"))
    for f in terr["features"]:
        f["properties"]["TERR_KEY"] = f["properties"]["TERRITORY"].title().strip()

    comp_df = pd.read_excel(COMP_FILE)
    comp_df.columns = comp_df.columns.str.strip()
    comp_df.rename(columns={"Market":"Territory"}, inplace=True)
    comp_df["Territory"] = comp_df["Territory"].str.title().str.strip()
    comp_df["BRAND"] = comp_df["BRAND"].str.title().str.strip()
    comp_df["Competitor"] = comp_df["Competitor"].str.title().str.strip()

    return gt, rtm, county, terr, comp_df

GT_DF, RTM_DF, COUNTY_GEO, TERR_GEO, COMP_DF = load_all()

# ───── Constants ─────
SALES, CS, COMP, WS, AWS = "ERP GT Sales Coverage", "Client Market Share", "Competitor Strength", "White Space Score", "Aws"
AXIS = dict(color="#9FB4CC", gridcolor="#24364F")
percent = lambda s: s*100 if s.max() <= 1 else s

# ───── Title ─────
st.markdown("## Territory Deep Dive")

# ───── KPI & Filter Panel ─────
with st.container():
    st.markdown(f"<div style='background:{PANEL}; padding:1.4rem 1rem; border-radius:8px; margin-bottom:24px;'>", unsafe_allow_html=True)

    c1, c2, c3, c4, c5, c6 = st.columns([1,1,1,1,1,1])
    territory = c1.selectbox("Territory", sorted(GT_DF["Territory"].unique()))
    brand = c2.selectbox("Brand", ["All"] + sorted(GT_DF["Brand"].unique()))

    sub_df = GT_DF[GT_DF["Territory"] == territory]
    if brand != "All":
        sub_df = sub_df[sub_df["Brand"] == brand]

    for col, (lbl, val, cls) in zip([c3,c4,c5,c6],[
        ("Total Sales", f"{sub_df[SALES].sum():,.0f}", ""),
        ("Market Share", f"{percent(sub_df[CS]).mean():.1f}%", "number-green"),
        ("Competitor Strength", f"{percent(sub_df[COMP]).mean():.1f}%", "number-red"),
        ("White Space", f"{sub_df[WS].mean():,.0f}", "")
    ]):
        col.markdown(f"<div class='metric'>{lbl}</div><div class='number {cls}'>{val}</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ───── Filter RTM Slice ─────
rtm_sel = RTM_DF[RTM_DF["Territory"] == territory]
if brand != "All":
    rtm_sel = rtm_sel[rtm_sel["Brand"] == brand]

# ───── Main Visuals ─────
left,right = st.columns(2)
with left:
    st.markdown("### RTM Insights (Hot Zones)")
    counties = rtm_sel["County"].unique()
    map_df = pd.DataFrame({"COUNTY_KEY": counties}).merge(
        rtm_sel[["County", AWS]].rename(columns={"County":"COUNTY_KEY"}), how="left"
    ).fillna({AWS:0})
    county_sub = {"type":"FeatureCollection","features":[f for f in COUNTY_GEO["features"] if f["properties"]["COUNTY_KEY"] in counties]}
    terr_poly = next(f for f in TERR_GEO["features"] if f["properties"]["TERR_KEY"]==territory)
    mfig = px.choropleth(map_df, geojson=county_sub, locations="COUNTY_KEY", featureidkey="properties.COUNTY_KEY", color=AWS, color_continuous_scale="Blues")
    mfig.add_trace(go.Choropleth(geojson=terr_poly, locations=[territory], featureidkey="properties.TERR_KEY", z=[0], colorscale=[[0,"rgba(0,0,0,0)"],[1,"rgba(0,0,0,0)"]], showscale=False, marker_line_color="#e2e8f0", marker_line_width=1.3))
    mfig.update_geos(fitbounds="locations", visible=False, bgcolor=PANEL, lakecolor=PANEL, landcolor=PANEL)
    mfig.update_layout(height=330, paper_bgcolor=PANEL, plot_bgcolor=PANEL, xaxis=AXIS, yaxis=AXIS, margin=dict(l=0,r=0,t=10,b=10))
    st.plotly_chart(mfig, use_container_width=True)

with right:
    st.markdown("### White Space Score Distribution")
    hist = px.histogram(rtm_sel, x=AWS, nbins=6, labels={AWS:"AWS Score"}, color_discrete_sequence=["#38bdf8"])
    hist.update_layout(height=330, bargap=0.5, paper_bgcolor=PANEL, plot_bgcolor=PANEL, xaxis=AXIS, yaxis=AXIS, margin=dict(l=0,r=0,t=10,b=10))
    st.plotly_chart(hist, use_container_width=True)

# ───── Key Competitor Analysis ─────
with st.container():
    st.markdown(f"<div style='background:{PANEL}; padding:1.5rem 1rem; border-radius:8px; margin-top:30px;'>", unsafe_allow_html=True)
    st.markdown("### Key Competitor Analysis")

    if brand == "All":
        st.info("Please select a specific brand above to view competitor analysis.")
    else:
        comp_df_filtered = COMP_DF[(COMP_DF["Territory"] == territory) & (COMP_DF["BRAND"] == brand)]
        if comp_df_filtered.empty:
            st.warning("No competitor data available for this territory + brand.")
        else:
            competitor = st.selectbox("Select Competitor", sorted(comp_df_filtered["Competitor"].unique()))
            row = comp_df_filtered[comp_df_filtered["Competitor"] == competitor].iloc[0]
            client_share = row["Pwani Market Share (%)"]
            comp_share = row["Competitor Market Share (%)"]
            total = client_share + comp_share
            client_pct = comp_pct = 0 if total==0 else (client_share/total*100, comp_share/total*100)[0]
            comp_pct = 100-client_pct
            fig_strip = go.Figure()
            fig_strip.add_trace(go.Bar(y=["Market"], x=[client_pct], name="Client Share", orientation='h', marker_color="#38bdf8", text=[f"Client: {client_pct:.1f}%"], textposition="inside"))
            fig_strip.add_trace(go.Bar(y=["Market"], x=[comp_pct], name="Competitor Share", orientation='h', marker_color="#64748b", text=[f"Competitor: {comp_pct:.1f}%"], textposition="inside"))
            fig_strip.update_layout(barmode="stack", height=120, margin=dict(l=20,r=20,t=10,b=10), paper_bgcolor=PANEL, plot_bgcolor=PANEL, xaxis=dict(showgrid=False, visible=False), yaxis=dict(showgrid=False, visible=False))
            st.plotly_chart(fig_strip, use_container_width=True)
            st.text_area("Reason for Performance", placeholder="Enter explanation for under or over-performance...", key="reason_input")

    st.markdown("</div>", unsafe_allow_html=True)

# ───── Footer ─────
st.caption("Data sources: GT KPI Excel ▪ RTM AWS CSV ▪ Kenya GeoJSONs ▪ Competitor Excel")
