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

    return gt, terr, rtm, county, comp_df

GT_DF, TERR_GEO, RTM_DF, COUNTY_GEO, COMP_DF = load_all_main()

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
def page_main_dashboard():
    st.markdown("## Main Dashboard – SUMMARY")

    # FILTERS
    col_brand, col_terr, _ = st.columns([1, 1, 6])
    brand = col_brand.selectbox("Brand", ["All"] + sorted(GT_DF["Brand"].unique()))
    terr  = col_terr.selectbox("Territory", ["All"] + sorted(GT_DF["Territory"].unique()))

    kpi_df = GT_DF.copy()
    if brand != "All":
        kpi_df = kpi_df[kpi_df["Brand"] == brand]
    if terr != "All":
        kpi_df = kpi_df[kpi_df["Territory"] == terr]

    # KPI METRICS
    c1, c2, c3 = st.columns(3)
    c1.metric("White Space Score",   f"{kpi_df[WS].mean():,.0f}")
    c2.metric("Client Share",        f"{percent(kpi_df[CS]).mean():.1f}%")
    c3.metric("Competitor Strength", f"{percent(kpi_df[COMP]).mean():.1f}%")

    # MAP + BAR LAYOUT
    left, _, right = st.columns([2, 0.1, 1])

    # --- MAP PANEL ---
    with left:
        base = GT_DF if brand == "All" else GT_DF[GT_DF["Brand"] == brand]
        agg = base.groupby("TERR_KEY", as_index=False)[WS].mean()
        terr_keys = [f["properties"]["TERR_KEY"] for f in TERR_GEO["features"]]
        mdf = pd.DataFrame({"TERR_KEY": terr_keys}).merge(agg, how="left").fillna({WS: 0})
        if terr != "All":
            mdf["plot_ws"] = 0
            mdf.loc[mdf["TERR_KEY"] == terr, "plot_ws"] = mdf.loc[mdf["TERR_KEY"] == terr, WS]
        else:
            mdf["plot_ws"] = mdf[WS]

        fig_map = px.choropleth_mapbox(
            mdf,
            geojson=TERR_GEO,
            locations="TERR_KEY",
            featureidkey="properties.TERR_KEY",
            color="plot_ws",
            color_continuous_scale="YlOrRd",
            range_color=(0, 60),
            mapbox_style="carto-darkmatter",
            center={"lat": 0.23, "lon": 37.9},
            zoom=5.5,
            opacity=0.9,
            height=520
        )

        # ✅ FULL-SCREEN BLUE OVERLAY
        fig_map.update_layout(
            mapbox=dict(
                style="carto-darkmatter",
                layers=[
                    # Optional Kenya tint
                    dict(
                        sourcetype="geojson",
                        source=TERR_GEO,
                        below="traces",
                        type="fill",
                        color="rgba(0,120,255,0.10)"
                    ),
                    # Full rectangle to overlay entire map view
                    dict(
                        sourcetype="geojson",
                        type="fill",
                        below="traces",
                        source={
                            "type": "FeatureCollection",
                            "features": [
                                {
                                    "type": "Feature",
                                    "geometry": {
                                        "type": "Polygon",
                                        "coordinates": [[
                                            [10, -35], [70, -35],
                                            [70, 25], [10, 25],
                                            [10, -35]
                                        ]]
                                    }
                                }
                            ]
                        },
                        color="rgba(0,120,255,0.15)"
                    )
                ]
            ),
            paper_bgcolor=NAVY_BG,
            plot_bgcolor=NAVY_BG,
            font_color=FG_TEXT,
            margin=dict(l=0, r=0, t=30, b=0)
        )

        st.plotly_chart(fig_map, use_container_width=True)

    # --- BARS PANEL ---
    with right:
        chart_df = GT_DF if brand == "All" else GT_DF[GT_DF["Brand"] == brand]
        share = chart_df.groupby("Territory", as_index=False)[[CS, COMP]].mean()
        share[CS], share[COMP] = percent(share[CS]), percent(share[COMP])
        op = [1 if (terr == 'All' or t == terr) else 0.3 for t in share["Territory"]]

        fig_stack = go.Figure()
        fig_stack.add_bar(name="Client Share",
                          x=share["Territory"], y=share[CS],
                          marker_opacity=op, marker_color="#00B4D8")
        fig_stack.add_bar(name="Competitor Strength",
                          x=share["Territory"], y=share[COMP],
                          marker_opacity=op, marker_color="#0077B6")
        fig_stack.update_layout(
            barmode="stack", bargap=.15, height=260,
            title="Market Composition",
            paper_bgcolor=PANEL_BG, plot_bgcolor=PANEL_BG,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=AXIS, yaxis=AXIS,
            legend=dict(bgcolor="rgba(0,0,0,0)",
                        orientation="h", yanchor="bottom", y=-.25)
        )
        st.plotly_chart(fig_stack, use_container_width=True)

        sales = chart_df.groupby("Territory", as_index=False)[SALES].sum()
        s_op = [1 if (terr == 'All' or t == terr) else 0.3 for t in sales["Territory"]]
        fig_sales = go.Figure(go.Bar(
            x=sales["Territory"], y=sales[SALES],
            marker_opacity=s_op, marker_color="#48CAE4"))
        fig_sales.update_layout(
            height=260, title="Sales",
            paper_bgcolor=PANEL_BG, plot_bgcolor=PANEL_BG,
            bargap=.15,
            margin=dict(l=0, r=0, t=40, b=0),
            xaxis=AXIS, yaxis=AXIS,
            showlegend=False
        )
        st.plotly_chart(fig_sales, use_container_width=True)

    # --- DETAIL TABLE ---
    st.markdown("### Detailed Market Snapshot")
    want_cols = ["Territory", "Category", "Brand", "Market_Share",
                 "Z_score", "PED", "SKU_CLUSTER", "TA_Fit", "Client"]
    available = [c for c in want_cols if c in GT_DF.columns]
    detail_df = GT_DF[available].copy()

    st.markdown("<div class='custom-table-container'>", unsafe_allow_html=True)
    st.dataframe(detail_df, height=350, use_container_width=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    st.caption("Sources: GT Excel ▪ Territory GeoJSON")


# ╭───────────────────────────────  PAGE 2  ─────────────────────────╮
# Territory Deep-Dive  (unchanged logic, wrapped into a function)
# -------------------------------------------------------------------
def page_territory_deep_dive():
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
    with st.container():
        st.markdown("### Key Competitor Analysis")

        if brand == "All":
            st.info("Please select a specific brand above to view competitor analysis.")
        else:
            comp_df_filtered = COMP_DF[
                (COMP_DF["Territory"] == territory) & (COMP_DF["BRAND"] == brand)
            ]

            if comp_df_filtered.empty:
                st.warning("No competitor data available for this territory + brand.")
            else:
                c1, _ = st.columns([1, 5])
                competitor = c1.selectbox(
                    "Select Competitor",
                    sorted(comp_df_filtered["Competitor"].unique())
                )

                row = comp_df_filtered[comp_df_filtered["Competitor"] == competitor].iloc[0]
                client_val = row["Pwani Market Share (%)"]
                comp_val   = row["Competitor Market Share (%)"]
                total_val  = client_val + comp_val

                fig_strip = go.Figure()
                fig_strip.add_trace(go.Bar(
                    y=["Market"], x=[client_val],
                    name="Client Share", orientation='h',
                    marker_color="#38bdf8",
                    text=[f"Client: {client_val:.1f}"], textposition="inside"
                ))
                fig_strip.add_trace(go.Bar(
                    y=["Market"], x=[comp_val],
                    name="Competitor Share", orientation='h',
                    marker_color="#64748b",
                    text=[f"Competitor: {comp_val:.1f}"], textposition="inside"
                ))

                fig_strip.update_layout(
                    barmode="stack",
                    height=140,
                    title=f"Total Market Value: {total_val:.1f}",
                    margin=dict(l=20, r=20, t=40, b=10),
                    paper_bgcolor=PANEL_BG,
                    plot_bgcolor=PANEL_BG,
                    xaxis=dict(showgrid=False, visible=False),
                    yaxis=dict(showgrid=False, visible=False),
                    font=dict(color="#e3e8ef")
                )

                st.plotly_chart(fig_strip, use_container_width=True)
               

    st.caption("Data sources: GT KPI Excel ▪ RTM AWS CSV ▪ Kenya GeoJSONs ▪ Competitor Excel")

# ╭───────────────────────────────  PAGE 3  ─────────────────────────╮
# SKU-Level Analysis  (unchanged logic)
# -------------------------------------------------------------------
SKU_GT_PATH  = Path("GT_Monthly_Clustered_2_Standardized.csv")
SKU_RTM_PATH = Path("RTM_MONTH DATA.csv")

@st.cache_data(show_spinner="Loading SKU-level data …")
def load_sku_data(gt_path, rtm_path):
    gt = pd.read_csv(gt_path)
    rtm = pd.read_csv(rtm_path)
    for df in (gt, rtm):
        for col in ("REGION_NAME", "BRAND", "SKU"):
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
    return gt, rtm

def page_sku_level():
    st.markdown("## SKU-Level Analysis")

    gt_df, rtm_df = load_sku_data(SKU_GT_PATH, SKU_RTM_PATH)

    f1, f2, f3, f4, f5 = st.columns([1, 1, 1, 1, 1])
    markets = sorted(set(gt_df["REGION_NAME"]) | set(rtm_df["REGION_NAME"]))
    brands  = sorted(set(gt_df["BRAND"])        | set(rtm_df["BRAND"]))

    brand_sel  = f2.selectbox("Brand", ["All"] + brands, index=0)

    if brand_sel == "All":
        skus = sorted(set(gt_df["SKU"]) | set(rtm_df["SKU"]))
    else:
        skus = sorted(set(gt_df[gt_df["BRAND"] == brand_sel]["SKU"]).union(
                      set(rtm_df[rtm_df["BRAND"] == brand_sel]["SKU"])))

    market_sel  = f1.selectbox("Market", ["All"] + markets, index=0)
    clusters    = sorted(gt_df["Cluster"].dropna().unique())
    cluster_sel = f3.selectbox("Cluster", ["All"] + clusters, index=0)
    sku_sel     = f4.selectbox("SKU Variant", ["All"] + skus, index=0)
    period_map  = {"1 Month": 12}
    period_sel  = f5.selectbox(" ", list(period_map.keys()), index=0)

    def apply_filters(df):
        if market_sel != "All":
            df = df[df["REGION_NAME"] == market_sel]
        if brand_sel != "All":
            df = df[df["BRAND"] == brand_sel]
        if sku_sel != "All":
            df = df[df["SKU"] == sku_sel]
        return df

    gt_filt  = apply_filters(gt_df)
    rtm_filt = apply_filters(rtm_df)
    if cluster_sel != "All":
        gt_filt = gt_filt[gt_filt["Cluster"] == cluster_sel]
    if not rtm_filt.empty:
        latest_month = int(rtm_filt["MONTH"].max())
        keep_months  = [m for m in rtm_filt["MONTH"].unique()
                        if latest_month - m < period_map[period_sel]]
        rtm_filt = rtm_filt[rtm_filt["MONTH"].isin(keep_months)]

    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)

    # Cluster breakdown
    with c1:
        st.markdown("#### SKU Cluster Breakdown")
        if gt_filt.empty:
            st.info("No GT data for chosen filters.")
        else:
            vol = gt_filt.groupby("Cluster")["VOLUME"].sum().sort_values()
            pct = (vol / vol.sum() * 100).round(1)
            df_bars = pct.reset_index().rename(columns={"VOLUME": "Percent"})
            fig = px.bar(df_bars, x="Percent", y="Cluster", orientation="h",
                         text="Percent", color_discrete_sequence=["#2BB06C"])
            fig.update_traces(texttemplate="%{text:.1f}%")
            fig.update_layout(height=260, showlegend=False,
                              paper_bgcolor=PANEL_BG, plot_bgcolor=PANEL_BG,
                              xaxis_title=None, yaxis_title=None,
                              margin=dict(l=0, r=0, t=5, b=5))
            st.plotly_chart(fig, use_container_width=True)

    # Pricing analysis
    with c2:
        st.markdown("#### Pricing Analysis")
        if rtm_filt.empty or "AVERAGE_BASE_PRICE" not in rtm_filt.columns:
            st.info("No RTM pricing data available.")
        else:
            prices = rtm_filt["AVERAGE_BASE_PRICE"].dropna()
            if prices.empty or prices.nunique() < 2:
                st.info("Not enough variation in price data to generate bins.")
            else:
                bins = np.linspace(prices.min(), prices.max(), 6)
                bins = np.unique(bins)
                if len(bins) <= 1:
                    st.info("Price range is constant; cannot create bins.")
                else:
                    labels = [f"{int(bins[i])} – {int(bins[i+1])}"
                              for i in range(len(bins) - 1)]
                    rtm_filt["Price-Range"] = pd.cut(
                        prices, bins=bins, labels=labels, include_lowest=True)
                    vol = rtm_filt.groupby("Price-Range")["VOLUME"].sum()
                    pct = (vol / vol.sum() * 100).round(1)
                    df_px = pct.reset_index().rename(columns={"VOLUME": "Percent"})
                    fig = px.bar(df_px, x="Percent", y="Price-Range",
                                 orientation="h", text="Percent",
                                 color_discrete_sequence=["#F04E4E"])
                    fig.update_traces(texttemplate="%{text:.1f}%")
                    fig.update_layout(height=260, showlegend=False,
                                      paper_bgcolor=PANEL_BG, plot_bgcolor=PANEL_BG,
                                      xaxis_title="Percentage Impact on Sales Volume",
                                      yaxis_title=None,
                                      margin=dict(l=0, r=0, t=5, b=5))
                    st.plotly_chart(fig, use_container_width=True)

    # PED impact
    with c3:
        st.markdown("#### PED Impact")
        ped_df = gt_filt.dropna(subset=["PED", "VOLUME", "Sales Value"])
        if ped_df.empty:
            st.info("No PED data for chosen slice.")
        else:
            fig = px.scatter(
                ped_df, x="PED", y="Sales Value", size="VOLUME", color="Cluster",
                hover_data=["BRAND", "SKU"], size_max=40)
            fig.update_layout(height=300, xaxis_title="PED",
                              yaxis_title="Revenue impact",
                              paper_bgcolor=PANEL_BG, plot_bgcolor=PANEL_BG,
                              margin=dict(l=0, r=0, t=5, b=5))
            st.plotly_chart(fig, use_container_width=True)

    with c4:
        st.markdown("#### Market Share Change")
        st.caption("⛈ Placeholder – add MoM / QoQ share logic here.")

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
        brand = st.selectbox('Brand', gt_data['brand'].unique())
        
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

# ╭───────────────────────────────  NAVIGATION  ─────────────────────╮
PAGE_FUNCS = {
    "Main Dashboard":              page_main_dashboard,
    "Territory Deep Dive":         page_territory_deep_dive,
    "SKU-Level Analysis":          page_sku_level,
    "Kenya County Opportunity":    page_kenya_dashboard,       # now 4 th
    "Territory–Brand Opportunity": page_opportunity_dashboard, # now 5 th
}

choice = st.sidebar.radio("Navigate",
                          ["Main Dashboard",
                           "Territory Deep Dive",
                           "SKU-Level Analysis",
                           "Kenya County Opportunity",
                           "Territory–Brand Opportunity"],     # order matters
                          index=0)

PAGE_FUNCS[choice]()
