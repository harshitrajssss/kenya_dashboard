# ─────────────────────────────────────────────────────────────────────────────
#  Pwani – 5-Page Streamlit Suite
#  (merges your three separate apps into one multi-page experience)
#  Author: Harshit · Last update: 2025-05-20
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json, re
from pathlib import Path
import importlib.util
from sklearn.cluster import KMeans

# ╭─────────────────────────  GLOBAL CONFIG  ─────────────────────────╮
st.set_page_config(page_title="Pwani Dashboards",
                   layout="wide",
                   initial_sidebar_state="collapsed",
                   page_icon="📊")

NAVY_BG  = "#0F1C2E"      # very-dark app background (shared)
PANEL_BG = "#192A3E"      # card / panel background
FG_TEXT  = "#e3e8ef"
ACCENT   = "#9FC5FF"      # (used on Opportunity page)

# ── SHARED CSS (injected once) ──────────────────────────────────────
st.markdown(
    f"""
    <style>
        html, body, [data-testid="stApp"] {{
            background:{NAVY_BG};
            color:{FG_TEXT};
            font-family:'Segoe UI',sans-serif;
        }}
        h1,h2,h3,h4,h5,h6 {{ color:#ffffff; margin:0; }}
        /* Plotly + data-frame defaults */
        .stDataFrame div[data-testid="stVerticalBlock"],
        .stTable                                      {{ background:{PANEL_BG}; }}
        .stPlotlyChart > div                          {{ background:{NAVY_BG}!important; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ╭───────────────────────────────  PAGE 1  ─────────────────────────╮
# (this is your original “Main Dashboard – SUMMARY” page)
# -------------------------------------------------------------------
#  • uses GT_DF / TERR_GEO / RTM_DF / COUNTY_GEO / COMP_DF
# -------------------------------------------------------------------
GT_FILE   = "GT_DATA_122_merged_filled.xlsx"
RTM_FILE  = "rtm_std_follow_GT_final (1).csv"
COUNTY_GJ = "kenya.geojson"
TERR_GJ   = "kenya_territories (1).geojson"
COMP_FILE = "PWANI_COMP_STD_final_confirmed.xlsx"

if importlib.util.find_spec("openpyxl") is None:
    st.error("⚠️  Missing dependency →  pip install openpyxl")
    st.stop()

@st.cache_data(show_spinner="Loading GT + territory data …")
def load_gt_terr():
    gt = (
        pd.read_excel(GT_FILE)
        .rename(columns=str.strip)
        .rename(columns={"brand": "Brand", "Markets": "Territory"})
    )
    gt["Territory"] = gt["Territory"].str.title().str.strip()
    gt["Brand"]     = gt["Brand"].str.title().str.strip()
    gt["TERR_KEY"]  = gt["Territory"]

    terr = json.loads(Path(TERR_GJ).read_text("utf-8"))
    for f in terr["features"]:
        f["properties"]["TERR_KEY"] = f["properties"]["TERRITORY"].title().strip()
    return gt, terr

@st.cache_data(show_spinner="Loading ALL datasets …")
def load_all_main():
    gt, terr = load_gt_terr()

    rtm = pd.read_csv(RTM_FILE)
    rtm.columns = rtm.columns.str.strip().str.title()
    rtm[["Territory", "County", "Brand"]] = rtm[["Territory", "County", "Brand"]].apply(
        lambda s: s.str.title().str.strip())

    county = json.loads(Path(COUNTY_GJ).read_text("utf-8"))
    for f in county["features"]:
        f["properties"]["COUNTY_KEY"] = (
            f["properties"].get("COUNTY_NAM") or f["properties"].get("NAME", "")
        ).title().strip()

    comp_df = pd.read_excel(COMP_FILE)
    comp_df.columns = comp_df.columns.str.strip()
    comp_df.rename(columns={"Market": "Territory"}, inplace=True)
    comp_df["Territory"]  = comp_df["Territory"].str.title().str.strip()
    comp_df["BRAND"]      = comp_df["BRAND"].str.title().str.strip()
    comp_df["Competitor"] = comp_df["Competitor"].str.title().str.strip()

    return rtm

RTM_DF= load_all_main()

SALES   = "ERP GT Sales Coverage"
CS      = "Client Market Share"
COMP    = "Competitor Strength"
WS      = "White Space Score"
AWS     = "Aws"
percent = lambda v: v*100 if v.max() <= 1 else v
AXIS    = dict(color="#9FB4CC", gridcolor="#24364F")
COLOR_SCALE_WS = [
    [0.00, "#012E57"], [0.25, "#004E89"],
    [0.50, "#006DA8"], [0.75, "#0090C6"], [1.00, "#00B4D8"],
]

# ─────────────────────────────────────────────────────────────────────────
#  PAGE 1 · Main Dashboard – SUMMARY  (with blue density overlay)
# ─────────────────────────────────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────
#  Unified Main Dashboard  (GT-Territory  ➜  MT-County toggle)
#  –  KPI cards, map, stacked bar, sales bar, data table
# ────────────────────────────────────────────────────────────────────
#  Requirements (already in your file):
#     • GT_DF, TERR_GEO   – from load_all_main()
#     • MT_DF             – from load_mt()  (see earlier insert)
#     • COUNTY_GEO        – from load_county_geo()
#     • global styles / colours / AXIS / NAVY_BG / PANEL_BG / FG_TEXT
# ────────────────────────────────────────────────────────────────────

def page_main_dashboard():
    st.markdown("## Main Dashboard")

    # ── DATA-SOURCE TOGGLE  (GT vs MT) ───────────────────────────────
    src = st.selectbox(
        "Data Source",
        ("GT – Territory View", "MT – County View"),
        help="Switch between the original GT territory view and the new MT county view."
    )

    if src.startswith("GT"):
        df        = GT_DF.copy()
        geo       = TERR_GEO
        region    = "Territory"
        key_col   = "TERR_KEY"
        centre    = {"lat": 0.23, "lon": 37.9}
    else:
        df        = MT_DF.copy()
        geo       = COUNTY_GEO
        region    = "County"
        key_col   = "COUNTY_KEY"
        centre    = {"lat": 0.23, "lon": 37.9}

    # ── FILTERS ──────────────────────────────────────────────────────
    f1, f2, _ = st.columns([1, 1, 6])
    brand_sel  = f1.selectbox("Brand",  ["All"] + sorted(df["Brand"].unique()))
    region_sel = f2.selectbox(region,   ["All"] + sorted(df[region].unique()))

    view = df.copy()
    if brand_sel  != "All": view = view[view["Brand"]  == brand_sel]
    if region_sel != "All": view = view[view[region]   == region_sel]

    pct = lambda s: (s*100 if s.max() <= 1 else s).round(2)

    # ── KPI CARDS ────────────────────────────────────────────────────
    k1, k2, k3 = st.columns(3)
    def kpi(col, title, value):
        col.markdown(
            f"<div style='border:1px solid #ccc;border-radius:10px;"
            f"padding:1rem;background:#253348;height:160px;'>"
            f"<h5 style='margin:0;color:#fff'>{title}</h5>"
            f"<p style='font-size:1.3rem;color:#fff'>{value}</p></div>",
            unsafe_allow_html=True)
    kpi(k1, "White Space Score",     f"{view['White Space Score'].mean():.0f}")
    kpi(k2, "Client Market Share",   f"{pct(view['Client Market Share']).mean():.1f}%")
    kpi(k3, "Competitor Strength",   f"{pct(view['Competitor Strength']).mean():.1f}%")

    st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)

    # ── LAYOUT  (Map  +  Bars) ───────────────────────────────────────
    left, _, right = st.columns([2, .1, 1])

    # —— Choropleth MAP —— -------------------------------------------
    with left:
        base   = df if brand_sel == "All" else df[df["Brand"] == brand_sel]
        agg_ws = base.groupby(key_col, as_index=False)["White Space Score"].mean()
        keys   = [f["properties"][key_col] for f in geo["features"]]
        mdf    = pd.DataFrame({key_col: keys}).merge(agg_ws, how="left").fillna({"White Space Score": 0})

        mdf["plot_ws"] = mdf["White Space Score"]
        if region_sel != "All":
            mdf.loc[mdf[key_col] != region_sel, "plot_ws"] = 0

        fig_map = px.choropleth_mapbox(
            mdf, geojson=geo, locations=key_col, featureidkey=f"properties.{key_col}",
            color="plot_ws", color_continuous_scale="YlOrRd",
            range_color=(0, 60),
            mapbox_style="carto-darkmatter",
            center=centre, zoom=5.5, opacity=0.9, height=520
        )
        # blue overlay (stylistic)
        fig_map.update_layout(
            mapbox=dict(layers=[dict(
                sourcetype="geojson", type="fill", below="traces",
                source={"type":"FeatureCollection","features":[{
                    "type":"Feature","geometry":{"type":"Polygon","coordinates":[
                        [[10,-35],[70,-35],[70,25],[10,25],[10,-35]]]} }]},
                color="rgba(0,120,255,0.15)")]),
            paper_bgcolor=NAVY_BG, plot_bgcolor=NAVY_BG,
            font_color=FG_TEXT, margin=dict(l=0,r=0,t=30,b=0)
        )
        st.plotly_chart(fig_map, use_container_width=True)

    # —— RIGHT-HAND BARS —— ------------------------------------------
    with right:
        comp = (df if brand_sel=="All" else df[df["Brand"]==brand_sel]) \
               .groupby(region, as_index=False)[["Client Market Share","Competitor Strength"]].mean()
        comp["Client Market Share"]  = pct(comp["Client Market Share"])
        comp["Competitor Strength"]  = pct(comp["Competitor Strength"])
        op   = [1 if (region_sel=="All" or r==region_sel) else .3 for r in comp[region]]

        fig_stack = go.Figure()
        fig_stack.add_bar(name="Client Share", x=comp[region], y=comp["Client Market Share"],
                          marker_opacity=op, marker_color="#00B4D8")
        fig_stack.add_bar(name="Competitor Strength", x=comp[region], y=comp["Competitor Strength"],
                          marker_opacity=op, marker_color="#0077B6")
        fig_stack.update_layout(
            barmode="stack", bargap=.15, height=260, title="Market Composition",
            paper_bgcolor=PANEL_BG, plot_bgcolor=PANEL_BG,
            margin=dict(l=0,r=0,t=30,b=0), xaxis=AXIS, yaxis=AXIS,
            legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h",
                        yanchor="bottom", y=-.25))
        st.plotly_chart(fig_stack, use_container_width=True)

        sales = (df if brand_sel=="All" else df[df["Brand"]==brand_sel]) \
                .groupby(region, as_index=False)["ERP GT Sales Coverage"].sum()
        s_op  = [1 if (region_sel=="All" or r==region_sel) else .3 for r in sales[region]]
        fig_sales = go.Figure(go.Bar(x=sales[region], y=sales["ERP GT Sales Coverage"],
                                     marker_opacity=s_op, marker_color="#48CAE4"))
        fig_sales.update_layout(
            height=260, title="ERP GT Sales Coverage",
            paper_bgcolor=PANEL_BG, plot_bgcolor=PANEL_BG, bargap=.15,
            margin=dict(l=0,r=0,t=40,b=0), xaxis=AXIS, yaxis=AXIS, showlegend=False)
        st.plotly_chart(fig_sales, use_container_width=True)

    # ── COMPLETE TABLE ───────────────────────────────────────────────
    st.markdown("### Detailed Dataset")
    st.dataframe(df, height=350, use_container_width=True)
    st.caption("Sources – GT KPI Excel & Territory GeoJSON  •  MT White-Space Score & County GeoJSON")


# ────────────────────────────────────────────────────────────────────
#  NAVIGATION update  ➜ remove “MT Dashboard” entry
# ────────────────────────────────────────────────────────────────────


# ╭───────────────────────────────  PAGE 2  ─────────────────────────╮
# Territory Deep-Dive  (unchanged logic, wrapped into a function)
# -------------------------------------------------------------------
def page_territory_deep_dive():

    # ── COMPETITOR TEXT ANALYSIS  (Reasons for outperformance) ──────────
    TEXT_CSV = "all_brands_competitive_analysis_20250530_140609.csv"

    @st.cache_data(show_spinner="Loading competitor-analysis text …")
    def load_comp_text():
        df = pd.read_csv(TEXT_CSV)
        # Normalise naming
        df.columns = df.columns.str.strip()
        df["Brand"]      = df["Brand"].astype(str).str.title().str.strip()
        df["Competitor"] = df["Competitor"].astype(str).str.title().str.strip()
        df["Territory"]  = df["Territory"].astype(str).str.title().str.strip()
        # make % numeric helper
        for col in ["Brand_Market_Share", "Competitor_Market_Share"]:
            if col in df.columns:
                df[col+"_num"] = (df[col].str.replace("%","").astype(float)
                                            .round(2).fillna(0))
        return df

    COMP_TXT_DF = load_comp_text()

    # --------------------------------------------------------------------- #
    # Territory Deep-Dive Dashboard
    # --------------------------------------------------------------------- #
    px.defaults.template = "plotly_dark"
    st.markdown("## Territory Deep Dive")

    # ── FILTERS & KPI METRICS ─────────────────────────────────────────────
    c1, c2, c3, c4, c5, c6 = st.columns([1, 1, 1, 1, 1, 1])
    territory = c1.selectbox("Territory", sorted(GT_DF["Territory"].unique()))
    brand     = c2.selectbox("Brand", ["All"] + sorted(GT_DF["Brand"].unique()))

    sub_df = GT_DF[GT_DF["Territory"] == territory]
    if brand != "All":
        sub_df = sub_df[sub_df["Brand"] == brand]

    for col, (lbl, val, cls) in zip([c3, c4, c5, c6], [
        ("Total Sales",        f"{sub_df[SALES].sum():,.0f}",             ""),
        ("Market Share",       f"{percent(sub_df[CS]).mean():.1f}%",      "number-green"),
        ("Competitor Strength",f"{percent(sub_df[COMP]).mean():.1f}%",    "number-red"),
        ("White Space",        f"{sub_df[WS].mean():,.0f}",               "")
    ]):
        col.markdown(
            f"<div class='metric'>{lbl}</div>"
            f"<div class='number {cls}'>{val}</div>",
            unsafe_allow_html=True)

    rtm_sel = RTM_DF[RTM_DF["Territory"] == territory]
    if brand != "All":
        rtm_sel = rtm_sel[rtm_sel["Brand"] == brand]

    left, right = st.columns(2)

    # ── LEFT COLUMN : RTM Map with Full Blue Overlay ──────────────────────
    with left:
        st.markdown("### RTM Insights (Hot Zones)")

        counties = rtm_sel["County"].unique()
        map_df = (
            pd.DataFrame({"COUNTY_KEY": counties})
            .merge(
                rtm_sel[["County", AWS]].rename(columns={"County": "COUNTY_KEY"}),
                how="left"
            )
            .fillna({AWS: 0})
        )

        county_sub = {
            "type": "FeatureCollection",
            "features": [
                f for f in COUNTY_GEO["features"]
                if f["properties"]["COUNTY_KEY"] in counties
            ]
        }

        mfig = px.choropleth_mapbox(
            map_df,
            geojson=county_sub,
            locations="COUNTY_KEY",
            featureidkey="properties.COUNTY_KEY",
            color=AWS,
            color_continuous_scale="YlOrRd",
            mapbox_style="carto-darkmatter",
            center={"lat": 0.23, "lon": 37.9},
            zoom=6,
            opacity=0.9,
            height=330
        )

        # Territory outline (white border)
        terr_poly = next(
            f for f in TERR_GEO["features"]
            if f["properties"]["TERR_KEY"] == territory
        )
        mfig.add_trace(
            go.Choroplethmapbox(
                geojson=terr_poly,
                locations=[territory],
                featureidkey="properties.TERR_KEY",
                z=[0],
                colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                showscale=False,
                marker_line_color="#e2e8f0",
                marker_line_width=1.3,
                hoverinfo="skip"
            )
        )

        # 🔵 Full-screen blue overlay
        mfig.update_layout(
            mapbox=dict(
                style="carto-darkmatter",
                layers=[
                    dict(
                        sourcetype="geojson",
                        type="fill",
                        below="traces",
                        source={
                            "type": "FeatureCollection",
                            "features": [{
                                "type": "Feature",
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [[
                                        [10, -35], [70, -35],
                                        [70, 25], [10, 25],
                                        [10, -35]
                                    ]]
                                }
                            }]
                        },
                        color="rgba(0,120,255,0.15)"
                    )
                ]
            ),
            paper_bgcolor=NAVY_BG,
            plot_bgcolor=NAVY_BG,
            font_color=FG_TEXT,
            margin=dict(l=0, r=0, t=10, b=10)
        )

        st.plotly_chart(mfig, use_container_width=True)

    # ── RIGHT COLUMN : Histogram ───────────────────────────────────────────
    with right:
        st.markdown("### White Space Score Distribution")
        hist = px.histogram(
            rtm_sel, x=AWS, nbins=5, labels={AWS: "AWS Score"},
            color_discrete_sequence=["#38bdf8"])
        hist.update_layout(
            height=330, bargap=0.5,
            paper_bgcolor=PANEL_BG, plot_bgcolor=PANEL_BG,
            xaxis=AXIS, yaxis=AXIS,
            margin=dict(l=0, r=0, t=10, b=10)
        )
        st.plotly_chart(hist, use_container_width=True)

    # ── COMPETITOR PANEL (unchanged) ───────────────────────────────────────
    # ── COMPETITOR PANEL (numeric bar + narrative text) ───────────────────
    # ──────────────────────────────────────────────────────────────────────────
#  BEAUTIFIED  Key Competitor Analysis  · full replacement panel
# ──────────────────────────────────────────────────────────────────────────
    import re, html

    # 1️⃣  GLOBAL CSS (inject once – put at top of your app only once)
    st.markdown("""
    <style>
    .reason-card{
        border:1px solid #2e3744;
        border-radius:10px;
        padding:1.05rem 1.3rem;
        margin-bottom:1.2rem;
        background:#1d2838;
    }
    .reason-card h5{
        margin:0 0 .4rem 0;
        font-weight:600;
        color:#38bdf8;
    }
    .reason-card p{
        color:#cbd5e1;
        font-size:.92rem;
        line-height:1.45rem;
        margin:.25rem 0 .7rem 0;
    }
    .reason-card ul{
        margin:0 0 .2rem 1.2rem;
        padding-left:0;
    }
    .reason-card li{
        color:#cbd5e1;
        font-size:.88rem;
        line-height:1.35rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # 2️⃣  helper: bullet detector + HTML builder
    _bullet_pat = re.compile(r"^\s*(?:-|\•|\d+\)|\d+\.)\s+(.*)$")

    def _build_reason_html(territory:str, raw:str)->str:
        """Turn raw multi-line reason text into a styled HTML card."""
        raw = (raw or "").strip()
        paras, bullets = [], []

        for ln in raw.splitlines():
            ln = ln.strip()
            if not ln:
                continue
            m = _bullet_pat.match(ln)
            if m:
                bullets.append(html.escape(m.group(1)))
            else:
                paras.append(html.escape(ln))

        h  = [f"<div class='reason-card'><h5>{html.escape(territory)}</h5>"]
        if paras:
            h.append("<p>" + " ".join(paras) + "</p>")
        if bullets:
            h.append("<ul>" + "".join(f"<li>{b}</li>" for b in bullets) + "</ul>")
        h.append("</div>")
        return "".join(h)

    # 3️⃣  FULL PANEL  (replace your old container)
    with st.container():
        st.markdown("### Key Competitor Analysis")

        # ── choose brand & competitor numerics (unchanged logic) ──────────
        if brand == "All":
            st.info("Select a specific **brand** above to view competitor analysis.")
            sel_comp = None
        else:
            comp_rows = COMP_DF[(COMP_DF["Territory"] == territory) &
                                (COMP_DF["BRAND"]     == brand)]
            if comp_rows.empty:
                st.warning("No numeric competitor data for this territory & brand.")
                sel_comp = None
            else:
                sel_comp = st.selectbox("Select Competitor",
                                        sorted(comp_rows["Competitor"].unique()))
                row = comp_rows[comp_rows["Competitor"] == sel_comp].iloc[0]
                client_val = row["Pwani Market Share (%)"]
                comp_val   = row["Competitor Market Share (%)"]
                total_val  = client_val + comp_val

                fig_strip = go.Figure()
                fig_strip.add_bar(y=["Market"], x=[client_val],
                                orientation='h', marker_color="#38bdf8",
                                text=[f"Client {client_val:.1f}%"],
                                textposition="inside")
                fig_strip.add_bar(y=["Market"], x=[comp_val],
                                orientation='h', marker_color="#64748b",
                                text=[f"{sel_comp} {comp_val:.1f}%"],
                                textposition="inside")
                fig_strip.update_layout(
                    barmode="stack", height=140,
                    title=f"Total Market Value: {total_val:.1f}%",
                    margin=dict(l=20,r=20,t=40,b=10),
                    paper_bgcolor=PANEL_BG, plot_bgcolor=PANEL_BG,
                    xaxis=dict(visible=False), yaxis=dict(visible=False),
                    font=dict(color="#e3e8ef"), showlegend=False)
                st.plotly_chart(fig_strip, use_container_width=True)

        # ── narrative cards pulled from COMP_TXT_DF ────────────────────────
        if sel_comp:
            txt_rows = COMP_TXT_DF[(COMP_TXT_DF["Brand"]      == brand) &
                                (COMP_TXT_DF["Competitor"] == sel_comp)]
            if txt_rows.empty:
                st.info("No narrative analysis found for this competitor.")
            else:
                st.markdown("#### Territory-wise Reasons")
                # loop through each territory row & render prettily
                for _, r in txt_rows.iterrows():
                    terr   = r["Territory"]
                    reason = (r.get("Reasons_Outperformance") or
                            r.get("Reason") or "")
                    st.markdown(_build_reason_html(terr, reason),
                                unsafe_allow_html=True)


               

    st.caption("Data sources: GT KPI Excel ▪ RTM AWS CSV ▪ Kenya GeoJSONs ▪ Competitor Excel")

# ╭───────────────────────────────  PAGE 3  ─────────────────────────╮

# ───────────────────────── imports
# Page 3 – SKU-Cluster Dashboard (SKU filter only affects price buckets)
# Page 3 – SKU Cluster Dashboard
# Brand-aware SKU filter (affects price bucket panel only)

import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objs as go
import json
from pathlib import Path
from sklearn.cluster import KMeans

# ───────── paths
GT_FILE  = Path("GT_DATA_122_merged_filled.xlsx")
RTM_FILE = Path("RTM_MONTH DATA.csv")
GEO_FILE = Path("kenya_territories (1).geojson")

# ───────── theme + colour helpers
PANEL_BG = "#0e1b2c"
BASE_COLOURS = {
    "RED": "#E74C3C", "YELLOW": "#F1C40F", "GREEN": "#2ECC71",
    "BLUE": "#3498DB", "WHITE": "#ECF0F1", "BLACK": "#34495E",
    "PURPLE": "#9B59B6", "ORANGE": "#E67E22",
}
def colour_for(cluster: str) -> str:
    first = str(cluster).split()[0].upper()
    return BASE_COLOURS.get(first, "#95A5A6")

def ensure_str_col(df: pd.DataFrame, name: str, *src):
    """Guarantee df[name] exists as string Series; pull from first src col."""
    for c in src:
        if c in df.columns:
            df[name] = df[c].astype(str)
            break
    if name not in df.columns:
        df[name] = pd.Series([""] * len(df), dtype=str)
    df[name] = df[name].str.upper().str.strip()

# ───────── load GT
@st.cache_data(show_spinner="Loading GT …")
def load_gt():
    df = pd.read_excel(GT_FILE)
    df = df.rename(columns={
        "Markets": "MARKET", "SKU_CLUSTER": "CLUSTER",
        "Market_Share": "SHARE_PCT", "Total_brand": "SALES_VAL",
        "avg_price": "AVG_PRICE",
    })
    ensure_str_col(df, "MARKET")
    ensure_str_col(df, "CLUSTER")
    ensure_str_col(df, "BRAND", "brand", "Brand")
    ensure_str_col(df, "SKU",   "SKU")
    df["SHARE_PCT"] = pd.to_numeric(df["SHARE_PCT"], errors="coerce").fillna(0)
    df["BUBBLE_SIZE"] = (df["SHARE_PCT"]*100).clip(lower=1)*20
    df["SHARE_LABEL"] = (df["SHARE_PCT"]*100).round(1).astype(str) + "%"
    return df

# ───────── load RTM
@st.cache_data(show_spinner="Loading RTM …")
def load_rtm():
    rtm = pd.read_csv(RTM_FILE)
    ensure_str_col(rtm, "MARKET", "REGION_NAME", "Markets")
    ensure_str_col(rtm, "BRAND",  "Brand")
    ensure_str_col(rtm, "SKU",    "SKU")
    if "Volume" in rtm.columns and "VOLUME" not in rtm.columns:
        rtm = rtm.rename(columns={"Volume": "VOLUME"})
    return rtm

# ───────── load map
@st.cache_data(show_spinner="Loading map …")
def load_map():
    poly = gpd.read_file(GEO_FILE).rename(
        columns={"TERRITORY": "MARKET", "REGION_NAME": "MARKET"})
    poly["MARKET"] = poly["MARKET"].str.upper()
    poly = poly.to_crs(3857); poly["geometry"] = poly.geometry.centroid
    poly = poly.to_crs(4326)
    poly["lon"] = poly.geometry.x; poly["lat"] = poly.geometry.y
    cent = poly[["MARKET","lon","lat"]].copy()
    return cent, poly

# ───────── bubble map
def draw_cluster_map(df, cent, poly):
    grid = (
        df[["MARKET","CLUSTER","SHARE_PCT","BUBBLE_SIZE","SHARE_LABEL"]]
        .drop_duplicates()
        .merge(cent, on="MARKET", how="left")
    )
    colour_map = {c: colour_for(c) for c in grid["CLUSTER"].unique()}
    outline = go.Choroplethmapbox(
        geojson=json.loads(poly.to_json()), locations=poly["MARKET"],
        z=[0]*len(poly), showscale=False,
        marker=dict(line=dict(color="rgba(200,200,200,0.4)", width=0.5)))
    px_fig = px.scatter_mapbox(
        grid, lat="lat", lon="lon",
        size="BUBBLE_SIZE", size_max=50,
        color="CLUSTER", color_discrete_map=colour_map,
        hover_data=dict(MARKET=True, CLUSTER=True, SHARE_LABEL=True,
                        lat=False, lon=False, BUBBLE_SIZE=False))
    fig = go.Figure([outline] + list(px_fig.data))
    fig.update_layout(mapbox_style="carto-darkmatter",
        mapbox_zoom=5.4, mapbox_center=dict(lat=0.25, lon=37.6),
        height=260, margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor=PANEL_BG, plot_bgcolor=PANEL_BG)
    st.plotly_chart(fig, use_container_width=True)

# ───────── main page
def page_sku_dashboard():
    st.title("SKU-Cluster Dashboard")

    gt  = load_gt()
    rtm = load_rtm()
    cent, poly = load_map()

    # FILTERS
    f = st.columns(5)
    market_sel  = f[0].selectbox("Market", ["ALL"]+sorted(gt["MARKET"].unique()))
    brand_sel   = f[1].selectbox("Brand",  ["ALL"]+sorted(gt["BRAND"].unique()))
    cluster_sel = f[2].selectbox(
        "Cluster",
        ["ALL"] + sorted(gt["CLUSTER"].dropna().astype(str).unique()))
    # SKU list from RTM after market & brand filter
    rtm_pool = rtm.copy()
    if market_sel != "ALL": rtm_pool = rtm_pool[rtm_pool["MARKET"] == market_sel]
    if brand_sel  != "ALL": rtm_pool = rtm_pool[rtm_pool["BRAND"]  == brand_sel]
    sku_sel = f[3].selectbox("SKU (price panel only)",
                             ["ALL"]+sorted(rtm_pool["SKU"].dropna().unique()))

    period_sel = f[4].selectbox("Period", ["LAST 12 MONTHS"])

    # GT filters (SKU not applied)
    gt_filt = gt.copy()
    if market_sel  != "ALL": gt_filt = gt_filt[gt_filt["MARKET"]  == market_sel]
    if brand_sel   != "ALL": gt_filt = gt_filt[gt_filt["BRAND"]   == brand_sel]
    if cluster_sel != "ALL": gt_filt = gt_filt[gt_filt["CLUSTER"] == cluster_sel]
    if gt_filt.empty:
        st.warning("No GT rows for filters."); return

    # RTM filters (includes SKU)
    rtm_filt = rtm.copy()
    if market_sel != "ALL": rtm_filt = rtm_filt[rtm_filt["MARKET"] == market_sel]
    if brand_sel  != "ALL": rtm_filt = rtm_filt[rtm_filt["BRAND"]  == brand_sel]
    if sku_sel    != "ALL": rtm_filt = rtm_filt[rtm_filt["SKU"]    == sku_sel]

    # Layout panels
    c1,c2 = st.columns(2); c3,c4 = st.columns(2)

    # 1 Cluster share
    with c1:
        st.subheader("Cluster Share")
        share = gt_filt.groupby("CLUSTER")["SHARE_PCT"].sum().reset_index()
        share["Percent"] = (share["SHARE_PCT"] / share["SHARE_PCT"].sum()*100).round(1)
        fig = px.bar(share, x="Percent", y="CLUSTER", orientation="h",
                     text="Percent",
                     color="CLUSTER",
                     color_discrete_map={c:colour_for(c) for c in share["CLUSTER"]})
        fig.update_traces(texttemplate="%{text:.1f}%")
        fig.update_layout(height=260,paper_bgcolor=PANEL_BG,plot_bgcolor=PANEL_BG,
                          showlegend=False,margin=dict(l=0,r=0,t=5,b=5))
        st.plotly_chart(fig,use_container_width=True)

    # 2 Price buckets (SKU aware)
    with c2:
        st.subheader("Price Buckets (RTM)")
        if {"AVERAGE_BASE_PRICE","VOLUME"}.issubset(rtm_filt.columns):
            tmp = rtm_filt.dropna(subset=["AVERAGE_BASE_PRICE","VOLUME"])
            if tmp["AVERAGE_BASE_PRICE"].nunique() >= 4:
                km = KMeans(n_clusters=4,n_init="auto").fit(
                    tmp[["AVERAGE_BASE_PRICE"]], sample_weight=tmp["VOLUME"])
                tmp["Bucket"] = km.labels_
                centers = km.cluster_centers_.flatten()
                vol = tmp.groupby("Bucket")["VOLUME"].sum()
                bars = pd.DataFrame({"Center":centers,"Volume":vol}).sort_values("Volume")
                bars["Label"]="₹"+bars["Center"].round().astype(int).astype(str)
                fig = px.bar(bars,y="Label",x="Volume",orientation="h",
                             color_discrete_sequence=["#F04E4E"])
                fig.update_layout(height=260,paper_bgcolor=PANEL_BG,plot_bgcolor=PANEL_BG,
                                  showlegend=False,margin=dict(l=30,r=10,t=30,b=20))
                st.plotly_chart(fig,use_container_width=True)
            else:
                st.info("Not enough RTM price variation.")
        else:
            st.info("RTM price / volume columns missing.")

    # 3 PED vs sales (SKU ignored)
    with c3:
        st.subheader("PED vs Sales")
        if {"PED","SALES_VAL"}.issubset(gt_filt.columns):
            ped_df = gt_filt.dropna(subset=["PED","SALES_VAL"])
            if not ped_df.empty:
                fig = px.scatter(
                    ped_df, x="PED", y="SALES_VAL",
                    size="SHARE_PCT", size_max=40,
                    color="CLUSTER",
                    color_discrete_map={c:colour_for(c) for c in ped_df["CLUSTER"].unique()})
                fig.update_layout(height=300,paper_bgcolor=PANEL_BG,
                                  plot_bgcolor=PANEL_BG,margin=dict(l=0,r=0,t=5,b=5))
                st.plotly_chart(fig,use_container_width=True)
            else:
                st.info("No PED & Sales rows.")
        else:
            st.info("Missing PED or SALES_VAL columns.")

    # 4 Map (SKU ignored)
    with c4:
        st.subheader("Territory Bubble Map")
        draw_cluster_map(gt_filt, cent, poly)





# ╭───────────────────────────────  PAGE 4  ─────────────────────────╮
# Territory–Brand Opportunity Dashboard  (your second standalone app)
# -------------------------------------------------------------------
#  — logic identical, wrapped into function; only set_page_config removed
# -------------------------------------------------------------------
# ╭───────────────────────────────  PAGE 4 NEW  ─────────────────────────╮
# Territory–Brand Opportunity  (replaces the old markdown-driven page)
# -----------------------------------------------------------------------
# ╭───────────────────────────────  PAGE 4  ─────────────────────────╮
# Territory–Brand Opportunity Dashboard (full-width report page)
# -------------------------------------------------------------------
# ─── PAGE 4 · Territory–Brand Opportunity Dashboard ─────────────────────
def page_opportunity_dashboard():
    import re, pandas as pd, streamlit as st, pathlib

    # ── data loads (identical) ───────────────────────────────────────────
    gt_data         = pd.read_excel('data_files/GT_DATA_122_merged_filled.xlsx')
    percentage_data = pd.read_excel('data_files/Province Percentage 250410 (1) (1).xlsx')
    top_location_data = pd.read_csv('data_files/Top_3_Brand_Locations.csv')

    # --- helper functions (unchanged) ------------------------------------
    def executive_summary_retirver(text):
        m = re.search(r'## 1. Executive Summary\s*(.*?)(?=\n##|\Z)', text, re.DOTALL)
        return m.group(1).strip() if m else ""

    def extract_territory_block(text, territory_name):
        m = re.search(rf"### {territory_name}\n(.*?)(?=\n### [A-Z ]+|\Z)", text, re.DOTALL)
        return m.group(0).strip() if m else None

    def extract_data(txt):
        ws  = re.search(r"\*\*White Space Score\*\*:\s*([\d.]+)", txt)
        cs  = re.search(r"\*\*Client Share\*\*:\s*([\d.]+)%", txt)
        ins = re.findall(r'### Insights\s*(.*?)(?=\n###|\n##|\Z)', txt, re.DOTALL)
        return {
            "white_space_scores": ws.group(1)+' %' if ws else None,
            "client_shares": cs.group(1)+' %' if cs else None,
            "insights": [' '.join(i.strip().split()) for i in ins],
        }

    def get_top_location(territory, brand):
        rows = top_location_data[(top_location_data['Territory']==territory) &
                                 (top_location_data['Brand']==brand)]
        return ','.join(rows['Top 3 Performing Location'].values)

    def text_extractor(territories, brand):
        data_dict = {"Territory":[], "White Space Scores":[], "Client Shares":[],
                     "Summary":[], "High Potential Regions":[]}
        try:
            md_path = pathlib.Path(f"md_files/{brand}.md")
            content = md_path.read_text(encoding='utf-8')
            exec_sum = executive_summary_retirver(content)
            for terr in territories:
                block = extract_territory_block(content, terr)
                if not block: continue
                d       = extract_data(block)
                top_loc = get_top_location(terr, brand)
                data_dict["Territory"].append(terr)
                data_dict["White Space Scores"].append(d["white_space_scores"])
                data_dict["Client Shares"].append(d["client_shares"])
                data_dict["Summary"].append(' '.join(d["insights"]))
                data_dict["High Potential Regions"].append(top_loc)
            return data_dict, exec_sum
        except FileNotFoundError:
            st.error(f"Markdown for {brand} not found.")
            return {}, ""

    def Population_percentage_per_brand(brand,territory):
        try:    
        
            data=percentage_data[percentage_data['Territory']==territory]

            if data.empty:
                return None, None, None  # or raise an error

            total_population = data['Total Population'].sum()

            # Assuming only one row should match per territory
            brand_percentage = data[brand].iloc[0]  # get the scalar value
            brand_population = (brand_percentage / 100) * total_population


            brand_percentage=f"Target Audience Fit: {brand_percentage:.2f}%"
            brand_population=f"Target Audience Population: {brand_population:,.0f}"
            total_population=f"Total Population of {territory}: {total_population:,.0f}"


            return total_population, brand_percentage, brand_population
        except KeyError:
            st.error(f"Error: Column '{brand}' not found in the percentage data.")
            return None
        except Exception as e:  
            st.error(f"An error occurred: {e}")
            return None

    def average_ws(brand):
        return round(gt_data[gt_data['brand']==brand]['White Space Score'].mean(),2)

    # ── UI layout identical to original ──────────────────────────────────
    st.title("Export and Report Section")

    col1, col2, col3 = st.columns([1.5,1.5,3])
    with col1:
        brands = sorted(gt_data['brand'].unique())
        default_index = brands.index("USHINDI BAR") if "USHINDI BAR" in brands else 0
        brand = st.selectbox("Brand", brands, index=default_index)
        
    territories = ["CENTRAL","COAST","LAKE","NAIROBI","RIFT VALLEY"]
    table, exec_sum = text_extractor(territories, brand)

    col_a,_ = st.columns([4,1])
    with col_a: st.subheader(f"{brand} - Report")
    st.markdown("---")

    # metric boxes
    col1, col2, col3 = st.columns(3)
    def info_box(title, content):
        st.markdown(f"""
            <div style='border:1px solid #ccc;border-radius:10px;
                        padding:1rem;background:#253348;height:180px;overflow-y:auto'>
                <h5 style='margin:0;color:#fff'>{title}</h5>
                <p style='font-size:0.9rem;color:#fff'>{content}</p>
            </div>""", unsafe_allow_html=True)

    with col1:
        territory=st.selectbox('Select the Territory',percentage_data['Territory'].unique())
        total_population, brand_population_percentage, brand_population = Population_percentage_per_brand(brand,territory)
        st.write(total_population)
        st.write(brand_population_percentage)
        st.write(brand_population)
    with col2: info_box("Average White Space Score", f"{average_ws(brand)} %")
    with col3: info_box("Executive Summary", exec_sum.split('\n\n')[0])
    st.markdown("---")

    # table
    st.subheader("Detailed Metric Table")
    df = pd.DataFrame(table)
    st.markdown("""
        <style>
        .styled-table{width:100%;border-collapse:collapse;margin-top:1rem;font-size:.9rem;
        font-family:'Segoe UI',sans-serif;background:#253348;color:#fff;text-align:center;}
        .styled-table thead tr{background:#253348;color:#fff;}
        .styled-table th,.styled-table td{padding:12px 15px;border:2px solid #fff;text-align:center;}
        .styled-table tbody tr:nth-child(even){background:#354761;}
        </style>
    """, unsafe_allow_html=True)
    st.markdown(df.to_html(classes='styled-table', index=False, escape=False), unsafe_allow_html=True)

    # PDF downloader
    st.markdown("---")
    st.subheader(f"Detailed Report for {brand}")
    report_map = {f"{brand} – {t.title()}":t for t in territories}
    report_map[f"{brand} – For all territories"] = "Complete"
    choice = st.selectbox("Report list", ["Select"]+list(report_map.keys()))
    if choice != "Select":
        loc = report_map[choice]
        path = pathlib.Path(f"Reports/{brand} {loc}.pdf")
        if path.exists():
            st.download_button("Download PDF Report", data=path.read_bytes(),
                               file_name=path.name, mime="application/pdf")
        else:
            st.error(f"⚠️ Report file not found: {path}")



# ╭───────────────────────────────  PAGE 5  ─────────────────────────╮
# Kenya County Opportunity Dashboard  (your third standalone app)
# -------------------------------------------------------------------
MAP_TABLE_HEIGHT = 760
MAP_TABLE_RATIO  = [5, 3]

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
    lat  = next((c for c in cols if re.search(r"^lat", c, re.I)), None)
    lon  = next((c for c in cols if re.search(r"(lon|lng)", c, re.I)), None)
    dist = next((c for c in cols if re.search(r"distrib|dealer|partner|outlet", c, re.I)), None)
    if None in (lat, lon, dist):
        st.stop()
    pts            = raw[[dist, lat, lon]].copy()
    pts.columns    = ["Distributor", "Latitude", "Longitude"]
    pts["Latitude"]= pd.to_numeric(pts["Latitude"],  errors="coerce")
    pts["Longitude"]=pd.to_numeric(pts["Longitude"], errors="coerce")
    return pts.dropna(subset=["Latitude","Longitude"])

def page_kenya_dashboard():
    st.markdown("## Kenya County Opportunity Dashboard")

    df,  geojson = load_counties()
    pts_df       = load_points()

    f1, f2 = st.columns([1, 5])
    with f1:
        brands = ["All"] + sorted(df["BRAND"].dropna().unique())
        choose = st.selectbox("Select Brand", brands)

    view_df = df if choose == "All" else df[df["BRAND"] == choose]

    county_avg = (view_df.groupby("County", as_index=False)["Opportunity Score"]
                           .mean()
                           .assign(County=lambda d: d["County"].str.title().str.strip()))

    fig = px.choropleth_mapbox(
        county_avg, geojson=geojson,
        locations="County", featureidkey="properties.COUNTY_KEY",
        color="Opportunity Score",
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

def page_readme():
    st.title("📖 Pwani Kenya Dashboard – User Guide")

    st.markdown("""
## What’s Inside?

This dashboard is a five-page suite that moves from **high-level market health** to **granular SKU pricing** and ends with **downloadable brand reports**.  
All pages share the same dark theme and respond instantly to filters.

| Page | Name | 30-sec Purpose |
|------|------|----------------|
| **1** | **Main Dashboard – SUMMARY** | National snapshot of key KPIs.<br>Filter by **Brand** or **Territory** to update KPIs, interactive map and two sales / share charts. |
| **2** | **Territory Deep-Dive** | Drill into a single territory: hot-zone map, KPI strip, competitor vs. client bar, AWS histogram to understand AWS distribution in territory. |
| **3** | **SKU-Level Analysis** | Cluster performance, *quarterly* pricing impact, PED bubbles and market-share change. |
| **4** | **Distribution Opportunities** | Geo heat-map of distributor reach + opportunity matrix to rank under-penetrated regions. |
| **5** | **Export & Report** | Brand-level report builder with executive summary, KPI cards, high-potential list and one-click PDF/CSV/XLSX export. |

---

## Key Metrics / Parameters

| Metric | Where Used | Quick Definition |
|--------|-----------|------------------|
| **White Space Score** | Pages 1-2 | Market potential not yet captured (0-100). |
| **Client Share** | Pages 1-2 | `(Brand Sales / Total Market Sales) × 100` |
| **Competitor Strength** | Pages 1-2 | Aggregate share of all competitors in scope. |
| **AWS** (RTM) | Pages 1-2 | RTM “hot-zone” opportunity score (0-50+). |
| **PED** | Pages 3 | Price Elasticity of Demand (∆Qty / ∆Price). |
| **Opportunity Score** | Page 4 | `0.6×White Space + 0.1×RTM – 0.3×GT Coverage + 100` |


---

## Quick Navigation Tips

* **Filters drive everything** – each page’s dropdowns update maps, charts and KPI cards in real-time.  
* Hover on choropleth maps and bars to see tooltips with exact numbers.  
* Use the **Export & Report** page to download PDF or CSV packs branded per territory.

---

### Data Sources

* **GT Channel**: sales, market share, SKU clusters.  
* **RTM Monthly**: average base price, volume, PED, hot-zone coordinates.  
* **GeoJSON**: Kenya county + territory shapes.  
* **Distributor Lat-Longs**: RTM coverage (20 km urban / 30 km rural).  

> All data tables are cached in memory for snappy page switches 🔄.

---

### Version Notes

* **v1.0** (2025-05-20) – initial 6-page release  
""")

# ──────────────────────────────────────────────────────────────────────────────
#  PAGE · MT Dashboard  (county-level clone of “Main Dashboard – SUMMARY”)
#  • Data source  : MT_WHITE_SPACE_SCORE_CLEANED.xlsx  (one row per county × brand)
#  • Map geometry : kenya.geojson   (47 counties, field = COUNTY_NAM)
# ──────────────────────────────────────────────────────────────────────────────
#  Insert this block BELOW the existing imports / constants and ABOVE the
#  PAGE_FUNCS definition in your main Streamlit file.  Nothing else needs to
#  change apart from adding the page to the sidebar list (see bottom).
# ──────────────────────────────────────────────────────────────────────────────

# ———————————————————
# Additional constants
# ———————————————————
MT_FILE      = "MT_WHITE_SPACE_SCORE_CLEANED.xlsx"   # cleaned file you produced
COUNTY_GJ    = "kenya.geojson"                       # same file already uploaded
WS_COL       = "White Space Score"
CS_COL       = "Client Market Share"
COMP_COL     = "Competitor Strength"
SALES_COL    = "ERP GT Sales Coverage"

# ———————————————————
# Data loaders (cached)
# ———————————————————
@st.cache_data(show_spinner="Loading MT White-Space data …")
def load_mt():
    if not Path(MT_FILE).exists():
        st.error(f"❌ {MT_FILE} not found"); st.stop()
    df = pd.read_excel(MT_FILE)

    # rename / strip
    df.columns = df.columns.str.strip()
    df["County"] = df["County"].astype(str).str.title().str.strip()
    if "Brand" not in df.columns and "BRAND" in df.columns:
        df.rename(columns={"BRAND": "Brand"}, inplace=True)
    df["Brand"] = df["Brand"].astype(str).str.title().str.strip()

    # key used by choropleth
    df["COUNTY_KEY"] = df["County"]
    # numeric guards
    for c in [WS_COL, CS_COL, COMP_COL, SALES_COL]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
        else:
            st.error(f"Column “{c}” missing in {MT_FILE}"); st.stop()

    return df

@st.cache_data(show_spinner="Loading Kenya county GeoJSON …")
def load_county_geo():
    if not Path(COUNTY_GJ).exists():
        st.error(f"❌ {COUNTY_GJ} not found"); st.stop()
    geo = json.loads(Path(COUNTY_GJ).read_text("utf-8"))
    # normalise the name field to COUNTY_KEY
    for feat in geo["features"]:
        nm = feat["properties"].get("COUNTY_NAM") or feat["properties"].get("NAME", "")
        feat["properties"]["COUNTY_KEY"] = str(nm).title().strip()
    return geo

MT_DF   = load_mt()
COUNTY_GEO = load_county_geo()

# ———————————————————
# Helper: percent formatter
percent_fmt = lambda s: (s*100 if s.max() <= 1 else s).round(2)

# ———————————————————
def page_mt_dashboard():
    st.markdown("## MT Dashboard – County Summary")

    # ── FILTERS
    f_brand, f_cnty, _ = st.columns([1, 1, 6])
    brand_sel = f_brand.selectbox("Brand",  ["All"] + sorted(MT_DF["Brand"].unique()))
    cnty_sel  = f_cnty.selectbox("County", ["All"] + sorted(MT_DF["County"].unique()))

    view = MT_DF.copy()
    if brand_sel != "All": view = view[view["Brand"] == brand_sel]
    if cnty_sel  != "All": view = view[view["County"] == cnty_sel]

    # ── KPI CARDS
    k1, k2, k3 = st.columns(3)
    def card(col, title, value):
        col.markdown(
            f"<div style='border:1px solid #ccc;border-radius:10px;"
            f"padding:1rem;background:#253348;height:160px;'>"
            f"<h5 style='margin:0;color:#fff'>{title}</h5>"
            f"<p style='font-size:1.3rem;color:#fff'>{value}</p></div>",
            unsafe_allow_html=True)

    card(k1, "White Space Score", f"{view[WS_COL].mean():.0f}")
    card(k2, "Client Market Share", f"{percent_fmt(view[CS_COL]).mean():.1f}%")
    card(k3, "Competitor Strength", f"{percent_fmt(view[COMP_COL]).mean():.1f}%")

    st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)

    # ── LAYOUT : map + bars
    left, _, right = st.columns([2, .1, 1])

    # —— Choropleth map ——
    with left:
        base      = MT_DF if brand_sel == "All" else MT_DF[MT_DF["Brand"] == brand_sel]
        agg_ws    = base.groupby("COUNTY_KEY", as_index=False)[WS_COL].mean()
        keys_full = [f["properties"]["COUNTY_KEY"] for f in COUNTY_GEO["features"]]
        mdf = pd.DataFrame({"COUNTY_KEY": keys_full}).merge(agg_ws, how="left").fillna({WS_COL:0})
        mdf["plot_ws"] = mdf[WS_COL]
        if cnty_sel != "All":
            mdf.loc[mdf["COUNTY_KEY"] != cnty_sel, "plot_ws"] = 0

        fig_map = px.choropleth_mapbox(
            mdf, geojson=COUNTY_GEO, locations="COUNTY_KEY",
            featureidkey="properties.COUNTY_KEY",
            color="plot_ws", color_continuous_scale="YlOrRd",
            range_color=(0, 60),
            mapbox_style="carto-darkmatter",
            center={"lat":0.23, "lon":37.9}, zoom=5.5,
            opacity=0.9, height=520
        )
        # optional blue overlay for brand look
        fig_map.update_layout(
            mapbox=dict(layers=[dict(
                sourcetype="geojson", type="fill", below="traces",
                source={"type":"FeatureCollection","features":[{
                    "type":"Feature","geometry":{"type":"Polygon","coordinates":[
                        [[10,-35],[70,-35],[70,25],[10,25],[10,-35]]]} }]},
                color="rgba(0,120,255,0.15)")]),
            paper_bgcolor=NAVY_BG, plot_bgcolor=NAVY_BG,
            font_color=FG_TEXT, margin=dict(l=0,r=0,t=30,b=0)
        )
        st.plotly_chart(fig_map, use_container_width=True)

    # —— Right-hand bar panels ——
    with right:
        share = (MT_DF if brand_sel=="All" else MT_DF[MT_DF["Brand"]==brand_sel]) \
                .groupby("County", as_index=False)[[CS_COL, COMP_COL]].mean()
        share[CS_COL]   = percent_fmt(share[CS_COL])
        share[COMP_COL] = percent_fmt(share[COMP_COL])
        op = [1 if (cnty_sel=="All" or c==cnty_sel) else .3 for c in share["County"]]

        fig_stack = go.Figure()
        fig_stack.add_bar(name="Client Share", x=share["County"], y=share[CS_COL],
                          marker_opacity=op, marker_color="#00B4D8")
        fig_stack.add_bar(name="Competitor Strength", x=share["County"], y=share[COMP_COL],
                          marker_opacity=op, marker_color="#0077B6")
        fig_stack.update_layout(
            barmode="stack", bargap=.15, height=260, title="Market Composition",
            paper_bgcolor=PANEL_BG, plot_bgcolor=PANEL_BG,
            margin=dict(l=0,r=0,t=30,b=0), xaxis=AXIS, yaxis=AXIS,
            legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=-.25))
        st.plotly_chart(fig_stack, use_container_width=True)

        sales = (MT_DF if brand_sel=="All" else MT_DF[MT_DF["Brand"]==brand_sel]) \
                .groupby("County", as_index=False)[SALES_COL].sum()
        sales_op = [1 if (cnty_sel=="All" or c==cnty_sel) else .3 for c in sales["County"]]
        fig_sales = go.Figure(go.Bar(x=sales["County"], y=sales[SALES_COL],
                                     marker_opacity=sales_op, marker_color="#48CAE4"))
        fig_sales.update_layout(
            height=260, title="ERP GT Sales Coverage",
            paper_bgcolor=PANEL_BG, plot_bgcolor=PANEL_BG, bargap=.15,
            margin=dict(l=0,r=0,t=40,b=0), xaxis=AXIS, yaxis=AXIS, showlegend=False)
        st.plotly_chart(fig_sales, use_container_width=True)

    # ── Data table
    st.markdown("### Full MT Dataset")
    st.dataframe(MT_DF, height=350, use_container_width=True)
    st.caption("Data: MT White-Space Score (cleaned)  ▪  Geometry: Kenya Counties GeoJSON")

# ╭───────────────────────────────  NAVIGATION  ─────────────────────╮
PAGE_FUNCS = {
    "README / Guide":              page_readme,  
    "Main Dashboard":              page_main_dashboard,
    "Territory Deep Dive":         page_territory_deep_dive,
    "SKU-Level Analysis":          page_sku_dashboard,
    "Kenya County Opportunity":    page_kenya_dashboard,       # now 4 th
    "Territory–Brand Opportunity": page_opportunity_dashboard, # now 5 th
}

choice = st.sidebar.radio("Navigate",
                          ["README / Guide",
                           "Main Dashboard",
                           "Territory Deep Dive",
                           "SKU-Level Analysis",
                           "Kenya County Opportunity",
                           "Territory–Brand Opportunity"],     # order matters
                          index=0)

PAGE_FUNCS[choice]()


So, I have uploaded a code for my dashboard, 5 pages, this is code. So, analyze this code completely. Now, there will be few changes I will be introducing in different pages. So, you have to understand the changes and keep everything same and add the changes in the code. So, you are a professional in doing this. So, take your time and analyze the code and then as I will give the command, you will make changes in this code.