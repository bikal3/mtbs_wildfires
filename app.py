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
[data-testid="stHeader"] { border-bottom: 1px solid #e2e8f0; }
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
