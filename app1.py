# app.py — Competitor Analysis (refined visual design)

import streamlit as st
import streamlit.components.v1 as components

# ──────────────────────────────────────────────
# Power BI URLs  (replace with live ones if needed)
NIELSEN_PBI_URL = (
    "https://app.powerbi.com/view?r=eyJrIjoiNGE5NDc5YjMtZWI4Yy00ZmY0LWI1ZjYtZmEwMTJjYTA1MWZkIiwidCI6IjA4YjdjZmViLTg5N2UtNDY5Yi05NDM2LTk3NGU2OTRhOGRmMiJ9"
)
MT_PBI_URL = (
    "https://app.powerbi.com/view?r=eyJrIjoiYTZlNWYxNjctZDRjMS00NTA1LTkzNWItOWZmYWE3ZjY3MDJkIiwidCI6IjA4YjdjZmViLTg5N2UtNDY5Yi05NDM2LTk3NGU2OTRhOGRmMiJ9&pageName=ReportSection"
)
# ──────────────────────────────────────────────


def main() -> None:
    # -------- page set-up --------
    st.set_page_config(
        page_title="Competitor Analysis",
        page_icon="📊",
        layout="wide",
    )
    _inject_css()                      # ⬅️  one-shot style injector

    # -------- header --------
    col_logo, col_title = st.columns([1, 8])
    with col_logo:
        st.image("https://placehold.co/64x64?text=Logo", width=64)
    with col_title:
        st.markdown("<h1 style='margin-bottom:0.3rem'>Competitor Analysis</h1>",
                    unsafe_allow_html=True)
        st.caption("Compare Nielsen syndicated data with Modern-Trade (MT) performance.")

    st.divider()

    # -------- centred content container --------
    with st.container():
        st.markdown("<div class='center-container'>", unsafe_allow_html=True)

        # ① Tabs (styled as buttons)
        tab1, tab2 = st.tabs(["📈 Nielsen", "🏬 Modern Trade"])

        # ② Dashboard in nicely padded card
        with tab1:
            _dashboard_card("Nielsen Dashboard", NIELSEN_PBI_URL)

        with tab2:
            _dashboard_card("Modern-Trade (MT) Dashboard", MT_PBI_URL)

        st.markdown("</div>", unsafe_allow_html=True)

    # -------- footer --------
    st.markdown(
        "<p style='text-align:center; font-size:0.75rem; color:gray;'>"
        "© 2025 Solutech Analytics | Confidential</p>",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────
def _dashboard_card(title: str, url: str) -> None:
    """Wrap a dashboard iframe in a rounded, shadowed card."""
    st.markdown("<div class='dash-card'>", unsafe_allow_html=True)
    st.subheader(title)
    components.iframe(url, height=750, scrolling=True)
    st.markdown("</div>", unsafe_allow_html=True)


def _inject_css() -> None:
    """Global CSS — run once."""
    st.markdown(
        """
        <style>
        /* ---------- general page tweaks ---------- */
        body, .stApp {background:#F4F6FA;}
        #MainMenu, footer {visibility:hidden;}

        /* center everything under .center-container */
        .center-container > div:first-child {max-width:1400px; margin:auto;}

        /* ---------- cards ---------- */
        .dash-card {
            background:#FFFFFF;
            border:1px solid #E2E6EF;
            border-radius:12px;
            padding:1.5rem;
            margin-top:1rem;
            box-shadow:0 8px 24px rgba(0,0,0,0.05);
        }
        iframe {border:none; border-radius:10px;}

        /* ---------- tab bar ---------- */
        div[data-baseweb="tab-list"] {
            gap:0.35rem;
        }
        div[data-baseweb="tab"] {
            padding:0.7rem 1.6rem;
            background:#EEF1F7;
            border:1px solid #D7DBE5;
            border-bottom:none;
            border-radius:10px 10px 0 0;
            font-weight:600;
            transition:background 0.2s ease;
        }
        div[data-baseweb="tab"][aria-selected="true"] {
            background:#FFFFFF;
            color:#1a1a1a;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
