import streamlit as st

st.set_page_config(
    page_title="MTBS Wildfire Analysis — California 1984–2022",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS tweaks (light base from config.toml handles the rest) ──────────
st.markdown("""
<style>
[data-testid="stSidebar"]            { display: none; }
[data-testid="collapsedControl"]     { display: none; }
[data-testid="stHeader"]             { border-bottom: 1px solid #e2e8f0; }
[data-testid="block-container"]      { padding-top: 1rem !important; }
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: #f8fafc;
    padding: 8px 16px 0;
    border-bottom: 1px solid #e2e8f0;
}
.stTabs [data-baseweb="tab"] {
    color: #6b7280;
    background-color: transparent;
    border-radius: 4px 4px 0 0;
    padding: 8px 24px;
    font-weight: 600;
    font-size: 14px;
}
.stTabs [aria-selected="true"] {
    background-color: #ffffff !important;
    color: #f97316 !important;
    border-bottom: 2px solid #f97316;
}
</style>
""", unsafe_allow_html=True)

# ── Site header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding: 12px 8px 16px; border-bottom: 1px solid #e2e8f0; margin-bottom: 4px;">
  <div style="color:#ea580c;font-size:11px;font-weight:700;letter-spacing:3px;
              text-transform:uppercase;margin-bottom:8px;">
    California · 1984 – 2022
  </div>
  <h1 style="color:#0f172a;font-size:36px;font-weight:900;margin:0 0 10px;line-height:1.15;">
    🔥 California Wildfire Analysis
  </h1>
  <p style="color:#4b5563;font-size:15px;max-width:680px;line-height:1.75;margin:0;">
    An end-to-end data science project combining satellite imagery, climate records,
    and 38 years of MTBS fire data to understand how California's wildfire crisis
    has intensified — and what the land looks like after the flames.
  </p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔥  Story", "🔬  Research", "🗺  Explorer"])

with tab1:
    from pages.story import render_story
    render_story()

with tab2:
    from pages.research import render_research
    render_research()

with tab3:
    from pages.explorer import render_explorer
    render_explorer()
