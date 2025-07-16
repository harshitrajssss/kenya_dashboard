"""
spc_dashboard.py  –  SPC Dashboard with Year/Month filters & sidebar UI
────────────────────────────────────────────────────────────────────────
• Cascading filters shown in one sidebar column
    Year → Month → Date → Recipecode → Paint Status → Shift
• When Year / Month picked, charts use that aggregated subset
• Combined key (Batch_Key) = Date | Recipe | Paint | Shift
• Capability Histogram with 1 %, 3 %, 5 % tail markers
• X bar Chart & R Chart titles, trim and thin-batch warnings
"""

from __future__ import annotations
import numpy as np, pandas as pd, urllib.parse as up
import streamlit as st
from sqlalchemy import create_engine, text
from pathlib import Path
from scipy.stats import norm
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ───────────────────────────────────────────────
# Page / CSS
# ───────────────────────────────────────────────
st.set_page_config("SPC Dashboard", "📊", layout="wide")
if Path("styles.css").exists():
    st.markdown(f"<style>{Path('styles.css').read_text()}</style>", unsafe_allow_html=True)

# ───────────────────────────────────────────────
# DB engine (cached)
# ───────────────────────────────────────────────
@st.cache_resource
def get_engine():
    odbc = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=10.200.202.124;"
        "DATABASE=SMARTMESBTP;"
        "UID=jkuserBTP;"
        "PWD=jkBTP@474;"
        "Encrypt=no;TrustServerCertificate=yes;"
    )
    return create_engine(
        "mssql+pyodbc:///?odbc_connect=" + up.quote_plus(odbc),
        pool_pre_ping=True,
        fast_executemany=True,
    )

ENG = get_engine()
P_TBL, M_TBL = "paintingDatanew", "tbmpcr"

# ───────────────────────────────────────────────
# Base CTE (derived columns)
# ───────────────────────────────────────────────
BASE_CTE = f"""
WITH data AS (
  SELECT p.dtandTime,
         p.Actual_Weight,
         m.recipecode,
         YEAR(p.dtandTime)  AS YYYY,
         MONTH(p.dtandTime) AS MM,
         CASE WHEN CAST(p.dtandTime AS time) BETWEEN '07:00' AND '14:59'
                  THEN 'Shift-A (07-15)'
              WHEN CAST(p.dtandTime AS time) BETWEEN '15:00' AND '22:59'
                  THEN 'Shift-B (15-23)'
              ELSE 'Shift-C (23-07)' END                     AS Shift,
         CASE
           WHEN p.Spray_Status = 1 AND p.Weight_Status = 1 THEN 'Painted'
           WHEN p.Spray_Status = 0 AND p.Weight_Status = 1 THEN 'Not Painted'
           ELSE 'Others'
         END                                                AS Paint_Status
  FROM   {P_TBL} p
  LEFT   JOIN {M_TBL} m ON p.barcode = m.gtbarcode
)
"""

# ───────────────────────────────────────────────
# Helper functions
# ───────────────────────────────────────────────
def build_where(flt: dict[str,str]) -> tuple[str, dict]:
    """Translate filter dict → SQL WHERE + params."""
    w, p = [], {}
    if flt.get("year")   not in (None,"All"):
        w.append("YYYY = :yy");               p["yy"] = int(flt["year"])
    if flt.get("month")  not in (None,"All"):
        w.append("MM = :mm");                 p["mm"] = int(flt["month"])
    if flt.get("date")   not in (None,"All"):
        w.append("CAST(dtandTime AS date)=:d"); p["d"] = flt["date"]
    if flt.get("recipe") not in (None,"All"):
        w.append("recipecode=:r");            p["r"] = flt["recipe"]
    if flt.get("paint")  not in (None,"All"):
        w.append("Paint_Status=:ps");         p["ps"] = flt["paint"]
    if flt.get("shift")  not in (None,"All"):
        w.append("Shift=:s");                 p["s"] = flt["shift"]
    return ("WHERE " + " AND ".join(w) if w else ""), p

@st.cache_data(show_spinner=False)
def distinct(col_sql: str, where_sql: str, params: dict) -> list[str]:
    sql = BASE_CTE + f"SELECT DISTINCT {col_sql} AS v FROM data {where_sql}"
    return sorted(pd.read_sql(text(sql), ENG, params=params)["v"].dropna().tolist())

def cascade_select(label:str, col_sql:str,
                   filters_so_far:dict, key:str, fmt=lambda x:x) -> str:
    where_sql, params = build_where(filters_so_far)
    opts = ["All"] + [fmt(v) for v in distinct(col_sql, where_sql, params)]
    if key not in st.session_state or st.session_state[key] not in opts:
        st.session_state[key] = "All"
    if len(opts) == 1:
        st.sidebar.warning(f"No {label.lower()} with current choices")
    return st.sidebar.selectbox(label,
                                opts,
                                index=opts.index(st.session_state[key]),
                                key=key)

# ───────────────────────────────────────────────
# Sidebar filters (single vertical column)
# ───────────────────────────────────────────────
flt: dict[str,str] = {}

st.sidebar.header("🔎 Filters")

flt["year"]  = cascade_select("Year",  "YYYY",  flt, "sel_year",  str)
flt["month"] = cascade_select("Month", "MM",    flt, "sel_month", lambda m: f"{m:02}" )
flt["date"]  = cascade_select("Date",  "CAST(dtandTime AS date)", flt, "sel_date")
flt["recipe"]= cascade_select("Recipecode","recipecode",          flt, "sel_recipe")
flt["paint"] = cascade_select("Paint Status","Paint_Status",      flt, "sel_paint")
flt["shift"] = cascade_select("Shift", "Shift",                   flt, "sel_shift")

batch_size = st.sidebar.number_input("Batch size", 30, 100_000, 150, 30)
sub_n      = st.sidebar.number_input("Sub-group n", 2, 10, 5, 1)

# ───────────────────────────────────────────────
# Query latest rows (Batch_Key added)
# ───────────────────────────────────────────────
where_sql, params = build_where(flt)
params.update({"lim_hi": int(batch_size),
               "lim_lo": max(20, int(sub_n)*2)})

SQL_BATCH = BASE_CTE + f"""
, numbered AS (
  SELECT *, ROW_NUMBER() OVER (ORDER BY dtandTime DESC) AS rn
  FROM   data {where_sql}
)
SELECT *,
       FORMAT(dtandTime,'yyyy-MM-dd') + ' | '
       + ISNULL(recipecode,'N/A') + ' | '
       + Paint_Status + ' | '
       + Shift AS Batch_Key
FROM   numbered
WHERE  rn <= :lim_hi
   OR  rn <= :lim_lo
ORDER  BY rn;
"""

df = pd.read_sql(text(SQL_BATCH), ENG, params=params)

if df.empty:
    st.error("No production rows match those filters."); st.stop()
if len(df) < batch_size:
    st.info(f"Only {len(df)} rows match – analysis is on this smaller sample.")

# ───────────────────────────────────────────────
# Debug sidebar
# ───────────────────────────────────────────────
with st.sidebar.expander("🛠 Debug"):
    if st.checkbox("Show SQL & row counts"):
        st.code(SQL_BATCH.strip(), language="sql")
        st.write({"rows": len(df),
                  "null weights": df["Actual_Weight"].isna().sum()})

# ───────────────────────────────────────────────
# SPC statistics
# ───────────────────────────────────────────────
W = df["Actual_Weight"].dropna().to_numpy()
if len(W) < sub_n:
    st.error("Sample size must be ≥ sub-group n."); st.stop()

μ, σ = W.mean(), W.std(ddof=0)
LSL, USL = μ - 3*σ, μ + 3*σ

trim = len(W)//sub_n*sub_n
lost = len(W)-trim
if lost:
    st.warning(f"{lost} rows trimmed to form whole sub-groups of {sub_n}.")

groups = W[:trim].reshape(-1, sub_n)
X̄, R = groups.mean(1), np.ptp(groups,1)

A2={2:1.88,3:1.023,4:0.729,5:0.577,6:0.483,7:0.419,8:0.373,9:0.337,10:0.308}[sub_n]
D3={2:0,3:0,4:0,5:0,6:0,7:0.076,8:0.136,9:0.184,10:0.223}[sub_n]
D4={2:3.267,3:2.574,4:2.282,5:2.114,6:2.004,7:1.924,8:1.864,9:1.816,10:1.777}[sub_n]
d2={2:1.128,3:1.693,4:2.059,5:2.326,6:2.534,7:2.704,8:2.847,9:2.970,10:3.078}[sub_n]

Xbar̄, R̄ = X̄.mean(), R.mean()
UCLx, LCLx = Xbar̄ + A2*R̄, Xbar̄ - A2*R̄
UCLr, LCLr = D4*R̄, D3*R̄

σ_short = R̄ / d2
Cp  = (USL-LSL) / (6*σ_short)
Cpk = min(USL-μ, μ-LSL) / (3*σ_short)
Pp  = (USL-LSL) / (6*σ)
Ppk = min(USL-μ, μ-LSL) / (3*σ)

# ───────────────────────────────────────────────
# KPI cards
# ───────────────────────────────────────────────
labels = ["Cp","Cpk","Pp","Ppk","Mean µ","σ overall"]
vals   = [Cp,Cpk,Pp,Ppk,μ,σ]
bgs    = "#e8f5e9 #fff3e0 #e3f2fd #fce4ec #ede7f6 #f3e5f5".split()
for i,(c,l,v) in enumerate(zip(st.columns(6), labels, vals)):
    c.markdown(f"""
        <div style='background:{bgs[i]};
                    padding:18px;border-radius:12px;text-align:center'>
            <h4>{l}</h4><p style='font-size:28px'>{v:.2f}</p>
        </div>""", unsafe_allow_html=True)

# ───────────────────────────────────────────────
# Charts
# ───────────────────────────────────────────────
left, right = st.columns([1.5,1], gap="large")

# Histogram
with left:
    xx = np.linspace(W.min(), W.max(), 200)
    fig_h = go.Figure([
        go.Histogram(x=W, nbinsx=30, histnorm="probability density",
                     marker_color="#4E79A7"),
        go.Scatter(x=xx, y=norm.pdf(xx, μ, σ),
                   line=dict(color="#E15759", width=3))
    ])
    for pct,col in [(0.01,"#d62728"),(0.03,"#ff7f0e"),(0.05,"#2ca02c")]:
        lo = np.percentile(W, pct*100)
        hi = np.percentile(W, 100-pct*100)
        fig_h.add_vline(lo, line=dict(color=col,dash="dot",width=2))
        fig_h.add_vline(hi, line=dict(color=col,dash="dot",width=2))
    fig_h.update_layout(title_text="Capability Histogram",
                        template="plotly_white", height=430,
                        margin=dict(l=40,r=20,t=60,b=40),
                        showlegend=False,
                        xaxis_title="Weight (kg)",
                        yaxis_title="Density")
    st.plotly_chart(fig_h, use_container_width=True)

# X bar & R
with right:
    idx = np.arange(1,len(X̄)+1)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.06,
                        subplot_titles=("X bar Chart","R Chart"))
    fig.add_scatter(x=idx,y=X̄,mode="lines+markers",
                    marker_color="#4E79A7",row=1,col=1)
    for y,colr in [(UCLx,"#E15759"),(LCLx,"#E15759"),(Xbar̄,"green")]:
        fig.add_hline(y,line=dict(color=colr,dash="dash"),row=1,col=1)
    fig.add_scatter(x=idx,y=R,mode="lines+markers",
                    marker_color="#59A14F",row=2,col=1)
    for y,colr in [(UCLr,"#E15759"),(LCLr,"#E15759"),(R̄,"green")]:
        fig.add_hline(y,line=dict(color=colr,dash="dash"),row=2,col=1)
    fig.update_layout(template="plotly_white", height=430,
                      margin=dict(l=40,r=20,t=40,b=40),
                      showlegend=False,
                      xaxis2_title="Sub-group index",
                      yaxis_title="Mean (kg)",
                      yaxis2_title="Range (kg)")
    st.plotly_chart(fig, use_container_width=True)

# ───────────────────────────────────────────────
# Raw table + export
# ───────────────────────────────────────────────
with st.expander("📄 Latest rows"):
    st.dataframe(df, height=340, use_container_width=True)
    st.download_button("Download CSV",
                       df.to_csv(index=False).encode(),
                       "latest_batch.csv",
                       "text/csv")
