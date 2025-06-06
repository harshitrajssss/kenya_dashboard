import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

# ───────── CONFIG ─────────
NAVY_BG = "#0F1C2E"
PANEL_BG = "#192A3E"
FG_TEXT = "#e3e8ef"

st.set_page_config(page_title="SKU-Level Analysis", layout="wide", initial_sidebar_state="collapsed")

st.markdown(f"""
<style>
    body, .stApp {{ background-color: {NAVY_BG}; color: {FG_TEXT}; }}
    h1,h2,h3,h4,h5 {{ color: {FG_TEXT}; margin: 0; }}
    section.main > div {{ padding-top: 0.5rem; }}
    label div[data-baseweb="select"] div {{ background-color: #1e293b !important; color: {FG_TEXT} !important; }}
    .panel {{ background-color: {PANEL_BG}; border-radius: 8px; padding: 1.25rem; margin-bottom: 1.5rem; }}
    .custom-table-container .stDataFrame div[data-testid="stVerticalBlock"] {{ background-color: {PANEL_BG}; }}
    .custom-table-container .stDataFrame thead th {{ background-color: #223349; color: {FG_TEXT}; }}
    .custom-table-container .stDataFrame tbody td {{ background-color: {PANEL_BG}; color: {FG_TEXT}; }}
</style>
""", unsafe_allow_html=True)

# ──────── FILE PATHS ────────
GT_PATH = Path("GT_Monthly_Clustered_2_Standardized.csv")
RTM_PATH = Path("RTM_MONTH DATA.csv")

@st.cache_data
def load_data(gt_path, rtm_path):
    gt = pd.read_csv(gt_path)
    rtm = pd.read_csv(rtm_path)
    for df in (gt, rtm):
        for col in ("REGION_NAME", "BRAND", "SKU"):
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
    return gt, rtm

gt_df, rtm_df = load_data(GT_PATH, RTM_PATH)

# ──────── FILTERS ────────
f1, f2, f3, f4, f5 = st.columns([1, 1, 1, 1, 1])
markets = sorted(set(gt_df["REGION_NAME"]) | set(rtm_df["REGION_NAME"]))
brands = sorted(set(gt_df["BRAND"]) | set(rtm_df["BRAND"]))
skus = sorted(set(gt_df["SKU"]) | set(rtm_df["SKU"]))
clusters = sorted(gt_df["Cluster"].dropna().unique())

market_sel = f1.selectbox("Market", ["All"] + markets, index=0)
brand_sel = f2.selectbox("Brand", ["All"] + brands, index=0)
cluster_sel = f3.selectbox("Cluster", ["All"] + clusters, index=0)
sku_sel = f4.selectbox("SKU Variant", ["All"] + skus, index=0)
period_map = {"1 Month": 1, "3 Months": 3, "6 Months": 6, "1 Year": 12}
period_sel = f5.selectbox(" ", list(period_map.keys()), index=0)

def apply_filters(df):
    if market_sel != "All":
        df = df[df["REGION_NAME"] == market_sel]
    if brand_sel != "All":
        df = df[df["BRAND"] == brand_sel]
    if sku_sel != "All":
        df = df[df["SKU"] == sku_sel]
    return df

gt_filt = apply_filters(gt_df)
rtm_filt = apply_filters(rtm_df)
if cluster_sel != "All":
    gt_filt = gt_filt[gt_filt["Cluster"] == cluster_sel]
if not rtm_filt.empty:
    latest_month = int(rtm_filt["MONTH"].max())
    keep_months = [m for m in rtm_filt["MONTH"].unique() if latest_month - m < period_map[period_sel]]
    rtm_filt = rtm_filt[rtm_filt["MONTH"].isin(keep_months)]

# ──────── DASHBOARD ────────
c1, c2 = st.columns(2)
c3, c4 = st.columns(2)

with c1:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("#### SKU Cluster Breakdown")
    if gt_filt.empty:
        st.info("No GT data for chosen filters.")
    else:
        vol = gt_filt.groupby("Cluster")["VOLUME"].sum().sort_values()
        pct = (vol / vol.sum() * 100).round(1)
        df_bars = pct.reset_index().rename(columns={"VOLUME": "Percent"})
        fig = px.bar(df_bars, x="Percent", y="Cluster", orientation="h", text="Percent", color_discrete_sequence=["#2BB06C"])
        fig.update_traces(texttemplate="%{text:.1f}%")
        fig.update_layout(height=260, showlegend=False, paper_bgcolor=PANEL_BG, plot_bgcolor=PANEL_BG,
                          xaxis_title=None, yaxis_title=None, margin=dict(l=0, r=0, t=5, b=5))
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("#### Pricing Analysis")
    if rtm_filt.empty or "AVERAGE_BASE_PRICE" not in rtm_filt.columns:
        st.info("No RTM pricing data available.")
    else:
        prices = rtm_filt["AVERAGE_BASE_PRICE"].dropna()
        if prices.empty:
            st.info("Selected slice has no price records.")
        else:
            bins = np.linspace(prices.min(), prices.max(), 6)
            labels = [f"${int(bins[i])} – ${int(bins[i+1])}" for i in range(5)]
            rtm_filt["Price-Range"] = pd.cut(prices, bins=bins, labels=labels, include_lowest=True)
            vol = rtm_filt.groupby("Price-Range")["VOLUME"].sum()
            pct = (vol / vol.sum() * 100).round(1)
            df_px = pct.reset_index().rename(columns={"VOLUME": "Percent"})
            fig = px.bar(df_px, x="Percent", y="Price-Range", orientation="h", text="Percent", color_discrete_sequence=["#F04E4E"])
            fig.update_traces(texttemplate="%{text:.1f}%")
            fig.update_layout(height=260, showlegend=False, paper_bgcolor=PANEL_BG, plot_bgcolor=PANEL_BG,
                              xaxis_title="Percentage Impact on Sales Volume", yaxis_title=None,
                              margin=dict(l=0, r=0, t=5, b=5))
            st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c3:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("#### PED Impact")
    ped_df = gt_filt.dropna(subset=["PED", "VOLUME", "Sales Value"])
    if ped_df.empty:
        st.info("No PED data for chosen slice.")
    else:
        fig = px.scatter(ped_df, x="PED", y="Sales Value", size="VOLUME", color="Cluster", hover_data=["BRAND", "SKU"], size_max=40)
        fig.update_layout(height=300, xaxis_title="PED", yaxis_title="Revenue impact ($)",
                          paper_bgcolor=PANEL_BG, plot_bgcolor=PANEL_BG,
                          margin=dict(l=0, r=0, t=5, b=5))
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c4:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("#### Market Share Change")
    st.caption("\u26C9 Placeholder – add MoM / QoQ share logic here.")
    st.markdown("</div>", unsafe_allow_html=True)
