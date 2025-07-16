# ────────────────────────────────────────────────────────────────
# PAGE 6 · Competitor Analysis  ➜  add to PAGE_FUNCS:
# PAGE_FUNCS["Competitor Analysis"] = page_competitor_analysis
# ────────────────────────────────────────────────────────────────
import streamlit as st
from streamlit.components.v1 import html   # needed for Power-BI iframe

# inherit palette from the main file (fallbacks keep it self-contained)
NAVY_BG  = globals().get("NAVY_BG",  "#0F1C2E")
PANEL_BG = globals().get("PANEL_BG", "#e3e8ef")
FG_TEXT  = globals().get("FG_TEXT",  "#e3e8ef")

# paste your real Publish-to-Web URLs here
NIELSEN_PBI_URL = "https://app.powerbi.com/view?r=eyJrIjoiNGE5NDc5YjMtZWI4Yy00ZmY0LWI1ZjYtZmEwMTJjYTA1MWZkIiwidCI6IjA4YjdjZmViLTg5N2UtNDY5Yi05NDM2LTk3NGU2OTRhOGRmMiJ9"
                  
MT_PBI_URL      = "https://app.powerbi.com/view?r=eyJrIjoiYTZlNWYxNjctZDRjMS00NTA1LTkzNWItOWZmYWE3ZjY3MDJkIiwidCI6IjA4YjdjZmViLTg5N2UtNDY5Yi05NDM2LTk3NGU2OTRhOGRmMiJ9&pageName=ReportSection"

def page_competitor_analysis() -> None:
    """Toggle between Nielsen & MT competitor dashboards (Power BI embeds)."""
    # ── one-time CSS injection for consistent look & feel
    if "_compet_css" not in st.session_state:
        st.markdown(
            f"""
            <style>
            body,[data-testid=stApp]{{background:{NAVY_BG};color:{FG_TEXT};
            font-family:'Segoe UI',sans-serif}}
            .kpiCard{{border:1px solid #222;border-radius:10px;padding:1rem;
                     background:{PANEL_BG};text-align:center;color:#000}}
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.session_state._compet_css = True   # noqa: SLF001

    # ── header
    st.title("Competitor Analysis – Power BI Dashboards")
    st.caption("Use the toggle to switch between Nielsen and Modern-Trade views.")

    # ── TOGGLE switch  (True ⇒ Nielsen · False ⇒ MT)
    show_nielsen = st.toggle("Show Nielsen (off → MT)", value=True)

    dataset = "Nielsen" if show_nielsen else "MT"
    url     = NIELSEN_PBI_URL if show_nielsen else MT_PBI_URL

    # ── KPI strip (optional placeholders – edit as needed)
    k1, k2, k3 = st.columns(3)
    for col, lbl, val in zip(
        (k1, k2, k3),
        ("Report", "Last Refresh", "Viewer"),
        (dataset, "2025-07-01 02:00", st.session_state.get("user", "Guest")),
    ):
        col.markdown(f"<div class='kpiCard'><h5>{lbl}</h5><p>{val}</p></div>",
                     unsafe_allow_html=True)

    st.markdown("---")

    # ── embedded Power BI report
    # ----- inside page_competitor_analysis() -----
# embed the chosen Power BI report
html(
    f"""
    <iframe  title="Power BI – {dataset}"
             width="100%" height="820"
             src="{url}&embedded=true"
             frameborder="0" allowfullscreen></iframe>
    """,
    height=820,
    scrolling=False,
)

# optional help panel
with st.expander("⚙️  If the report doesn’t load"):
    st.write(
        "1. Verify your network allows Power BI traffic.\n"
        "2. Ensure the *Publish-to-Web* link is still active.\n"
        "3. Sign into the correct Power BI tenant if required."
    )
