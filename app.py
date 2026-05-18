import streamlit as st

st.set_page_config(
    page_title="MTBS Wildfire Analysis — California 1984–2022",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0a0a0a; }
[data-testid="stHeader"] { background-color: #0a0a0a; }
section[data-testid="stSidebar"] { background-color: #0f0f0f; }
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: #0f0f0f;
    padding: 8px 16px 0;
    border-bottom: 1px solid #1a1a1a;
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
    background-color: #1a1a1a !important;
    color: #f97316 !important;
}
h1, h2, h3 { color: #f1f5f9; }
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
