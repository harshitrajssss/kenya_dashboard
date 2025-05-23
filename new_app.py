import re
import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# 1️⃣  PAGE CONFIG & GLOBAL STYLES
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Territory–Brand Opportunity Dashboard",
    layout="wide",
    page_icon="📊",
)

# ---- Colour Palette ----
NAVY_BG = "#0F1C2E"  # used for app & map background
PANEL_BG = "#192A3E"
ACCENT    = "#9FC5FF"

# ---- Global CSS (dark theme) ----
st.markdown(
    f"""
    <style>
    #MainMenu{{visibility:hidden;}} footer{{visibility:hidden;}}
    html, body{{background:{NAVY_BG};color:#E3E8EF;font-family:'Segoe UI',sans-serif;}}
    h1,h2,h3,h4,h5,h6{{color:#FFFFFF;}}

    /* Metric cards */
    .metric-card{{border:1px solid #334F6B;border-radius:12px;background:{PANEL_BG};
                 padding:1.25rem 1rem;height:220px;overflow-y:auto;}}
    .metric-card h5{{margin:0 0 .5rem 0;font-size:1rem;color:{ACCENT};}}
    .metric-card p{{margin:0;font-size:.95rem;line-height:1.35rem;}}

    /* DataFrame tweaks */
    .stDataFrame{{background:{PANEL_BG};}}
    .stDataFrame tbody td{{white-space:pre-wrap !important;line-height:1.35rem;}}
    .stDataFrame table{{width:100% !important;}}

    /* Plotly/Mapbox background */
    .stPlotlyChart > div {{background:{NAVY_BG} !important;}}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 2️⃣  STATIC MARKDOWN REPORT CONTENT (default)
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
# 3️⃣  HELPERS
# -----------------------------------------------------------------------------
@st.cache_data
def load_gt_data(path: str = "GT_DATA_122_merged_filled.xlsx") -> pd.DataFrame:
    return pd.read_excel(path)

def extract_data(markdown_text: str, territory: str):
    sku_clusters = re.findall(r"SKU Cluster\s*[:|]\s*([A-Za-z0-9 ]+)", markdown_text)
    white_space_scores = re.findall(r"White Space Score\s*[:|]?\s*([0-9.]+)", markdown_text)
    client_shares = re.findall(r"Client Share\s*[:|]?\s*([0-9.]+%)", markdown_text)

    exec_match = re.search(r"## Executive Summary\s+(.*)", markdown_text, re.DOTALL)
    executive_summary_first_line = ""
    if exec_match:
        executive_summary_first_line = re.split(r"(?<=[.!?])\s+", exec_match.group(1).strip())[0]

    high_match = re.search(r"### Top high potential Regions\s*(.*?)(?=\n##|\n---)", markdown_text, re.DOTALL)
    high_potential_regions = []
    if high_match:
        high_potential_regions = [r.strip() for r in re.split(r",|;", high_match.group(1)) if r.strip()]

    insights = re.findall(r"### Insights\s*(.*?)(?=\n###|\n---)", markdown_text, re.DOTALL)

    table = {
        "Territory": territory,
        "Client Shares": list(set(client_shares)),
        "White Space Scores": list(set(white_space_scores)),
        "Summary": [i.strip() for i in insights],
    }
    meta = {
        "sku_clusters": list(set(sku_clusters)),
        "executive_summary": executive_summary_first_line,
        "high_potential_regions": high_potential_regions,
    }
    return table, meta

def average_white_space(df: pd.DataFrame, territory: str, brand: str) -> float:
    subset = df[(df["Markets"] == territory) & (df["brand"] == brand)]
    return round(subset["White Space Score"].mean(), 2)

# -----------------------------------------------------------------------------
# 4️⃣  DATA & FILTERS
# -----------------------------------------------------------------------------
GT_DATA = load_gt_data()

# brand list & default selection
brand_options = list(GT_DATA["brand"].unique())
try:
    default_brand_index = brand_options.index("USHINDI BAR")
except ValueError:
    default_brand_index = 0  # fallback

with st.sidebar:
    st.header("🔎 Filters")
    territory = st.selectbox("Territory", GT_DATA["Markets"].unique())
    brand = st.selectbox("Brand", brand_options, index=default_brand_index)

avg_ws = average_white_space(GT_DATA, territory, brand)

table_data, meta = extract_data(TEXT, territory)

# Join summary list into single multiline string for nicer display
if isinstance(table_data["Summary"], list):
    table_data["Summary"] = ["\n\n".join(table_data["Summary"])]

# -----------------------------------------------------------------------------
# 5️⃣  LAYOUT
# -----------------------------------------------------------------------------
st.title(f"📍 {brand} — {territory} Opportunity Report")

# ---- Metric Cards ----
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        f"""<div class='metric-card'><h5>High‑Potential Regions</h5>
        <p>{', '.join(meta['high_potential_regions']) or 'N/A'}</p></div>""",
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f"""<div class='metric-card'><h5>Avg White‑Space Score</h5>
        <p>{avg_ws if not pd.isna(avg_ws) else 'N/A'}</p></div>""",
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f"""<div class='metric-card'><h5>Executive Summary</h5>
        <p>{meta['executive_summary'] or '—'}</p></div>""",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ---- Detailed Metrics Table ----

df = pd.DataFrame(table_data)
st.subheader("📊 Detailed Metrics Table")
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    height=400,
    column_config={"Summary": st.column_config.TextColumn(width="large")},
)

# ---- Export ----
with st.expander("⬇️ Export Report"):
    st.download_button(
        label="Download Markdown Report",
        data=TEXT,
        mime="text/markdown",
        file_name=f"{territory}_{brand}_report.md",
    )
