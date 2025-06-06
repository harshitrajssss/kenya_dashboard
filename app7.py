import re
import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# 1️⃣ PAGE CONFIG & GLOBAL STYLES
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Territory–Brand Opportunity Dashboard",
    layout="wide",
    page_icon="📊",
)

NAVY_BG = "#0F1C2E"
PANEL_BG = "#192A3E"
ACCENT   = "#9FC5FF"

st.markdown(
    f"""
    <style>
    #MainMenu, footer {{visibility: hidden;}}
    html, body, [data-testid="stApp"] {{
        background-color: {NAVY_BG};
        color: #E3E8EF;
        font-family: 'Segoe UI', sans-serif;
    }}
    section[data-testid="stSidebar"] > div {{
        background-color: {NAVY_BG};
    }}
    .metric-card {{
        border: 1px solid #334F6B;
        border-radius: 12px;
        background: {PANEL_BG};
        padding: 1.25rem 1rem;
        height: 220px;
        overflow-y: auto;
    }}
    .metric-card h5 {{
        margin: 0 0 .5rem 0;
        font-size: 1rem;
        color: {ACCENT};
    }}
    .metric-card p {{
        margin: 0;
        font-size: .95rem;
        line-height: 1.35rem;
    }}
    .stDataFrame, .stTable {{
        background: {PANEL_BG};
    }}
    .stTable tbody td {{
        white-space: pre-wrap !important;
        line-height: 1.35rem;
    }}
    .stPlotlyChart > div {{
        background: {NAVY_BG} !important;
    }}
    h1,h2,h3,h4,h5,h6 {{
        color: #FFFFFF;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 2️⃣ STATIC MARKDOWN CONTENT
# -----------------------------------------------------------------------------
TEXT = """# USHINDI Laundry Bar
## Territory-Wise Brand Strategy
### Executive Analysis & Actionable Recommendations
---
## Executive Summary
USHINDI Laundry Bar faces significant challenges and opportunities in the Nairobi territory. The brand is struggling with low market share (6.5%) despite a high white space score (64.7), indicating substantial untapped potential. Key metrics comparison:

| Metric | Value | Interpretation |
|--------|-------|----------------|
| SKU Cluster | Yellow B | Struggling, requires targeted interventions |
| White Space Score | 64.7 | High opportunity, but poor execution |
| Client Share | 6.5% | Very low, immediate action needed |
| Competitor Strength | 24.6% | Moderate competition |
| ERP/Nielsen Ratio | 2.61 | Oversupply, conversion issues |
| Z-Score | 0.74 | Slight positive momentum |
| TA Fit | 64.1% | Good audience alignment |

The brand needs to address conversion issues, improve retail presence, and leverage RTM data to target high-potential micro-markets.

---
### Top high potential Regions
region 1, region 2 ,region 3
## NAIROBI
---
**SKU Cluster**: Yellow B (Struggling)  
**White Space Score**: 64.69 (High untapped potential)  
**Client Share**: 6.49% → Critically low market penetration  
**Competitor Strength**: Medium (24.56%)  
**ERP/Nielsen Ratio**: 2.61 → Significant oversupply, poor sell-through  
**Z-Score**: 0.74 → Slight positive momentum  
**TA Fit**: 64.12%  

### Insights
USHINDI Laundry Bar is severely underperforming in Nairobi despite a high white space score and good target audience fit. The ERP/Nielsen ratio of 2.61 indicates a significant oversupply issue, suggesting problems with retail execution and consumer offtake. RTM data shows pockets of strength in specific locations that aren't translating to overall market share.
"""

# -----------------------------------------------------------------------------
# 3️⃣ HELPER FUNCTIONS
# -----------------------------------------------------------------------------
@st.cache_data
def load_gt_data(path="GT_DATA_122_merged_filled.xlsx"):
    return pd.read_excel(path)

def parse_markdown(md: str):
    # Extract Executive Summary snippet before "Key metrics comparison"
    exec_match = re.search(r"## Executive Summary\s*(.*?)\n", md, re.DOTALL)
    exec_block = exec_match.group(1).strip() if exec_match else ""
    exec_snippet = re.split(r"(?i)key metrics comparison", exec_block)[0].strip()

    if not exec_snippet:
        exec_snippet = re.split(r"(?<=[.!?])\s+", exec_block)[0].strip()

    # Other fields
    insights = re.findall(r"### Insights\s*(.*?)(?=\n###|\n---)", md, re.DOTALL)
    white_space_scores = re.findall(r"White Space Score\s*[:|]?\s*([0-9.]+)", md)
    client_shares = re.findall(r"Client Share\s*[:|]?\s*([0-9.]+%)", md)

    high_match = re.search(r"### Top high potential Regions\s*(.*?)(?=\n##|\n---)", md, re.DOTALL)
    high_regions = [r.strip() for r in re.split(r",|;", high_match.group(1))] if high_match else []

    return {
        "executive_summary": exec_snippet,
        "insights": "\n\n".join(insights) if insights else exec_snippet,
        "white_space_scores": list(set(white_space_scores)),
        "client_shares": list(set(client_shares)),
        "high_regions": high_regions,
    }

def average_white_space(df: pd.DataFrame, territory: str, brand: str) -> float:
    subset = df[(df["Markets"] == territory) & (df["brand"] == brand)]
    return round(subset["White Space Score"].mean(), 2)

# -----------------------------------------------------------------------------
# 4️⃣ FILTERS
# -----------------------------------------------------------------------------
GT_DATA = load_gt_data()

with st.sidebar:
    st.header("🔎 Filters")

    territory_opts = list(GT_DATA["Markets"].unique())
    default_territory_idx = territory_opts.index("NAIROBI") if "NAIROBI" in territory_opts else 0
    territory = st.selectbox("Territory", territory_opts, index=default_territory_idx)

    brand_opts = list(GT_DATA["brand"].unique())
    default_brand_idx = brand_opts.index("USHINDI BAR") if "USHINDI BAR" in brand_opts else 0
    brand = st.selectbox("Brand", brand_opts, index=default_brand_idx)

meta = parse_markdown(TEXT)
avg_ws = average_white_space(GT_DATA, territory, brand)

# -----------------------------------------------------------------------------
# 5️⃣ LAYOUT
# -----------------------------------------------------------------------------
st.title(f"📍 {brand} — {territory} Opportunity Report")

# ---- KPI CARDS ----
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        f"<div class='metric-card'><h5>High-Potential Regions</h5>"
        f"<p>{', '.join(meta['high_regions']) or 'N/A'}</p></div>",
        unsafe_allow_html=True
    )
with c2:
    st.markdown(
        f"<div class='metric-card'><h5>Avg White-Space Score</h5>"
        f"<p>{avg_ws if not pd.isna(avg_ws) else 'N/A'}</p></div>",
        unsafe_allow_html=True
    )
with c3:
    st.markdown(
        f"<div class='metric-card'><h5>Executive Summary</h5>"
        f"<p>{meta['executive_summary']}</p></div>",
        unsafe_allow_html=True
    )

st.markdown("---")

# ---- DETAILED TABLE ----
st.subheader("📊 Detailed Metrics Table")
table_df = pd.DataFrame({
    "Territory": [territory],
    "Client Shares": [", ".join(meta["client_shares"]) or "—"],
    "White Space Scores": [", ".join(meta["white_space_scores"]) or "—"],
    "Summary": [meta["executive_summary"]],
})
st.table(table_df)

# ---- EXPORT ----
with st.expander("⬇️ Export Report"):
    st.download_button(
        "Download Markdown Report",
        data=TEXT,
        mime="text/markdown",
        file_name=f"{territory}_{brand}_report.md",
    )