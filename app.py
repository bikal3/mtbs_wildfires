import streamlit as st

st.set_page_config(
    page_title="MTBS Wildfire Analysis — California 1984–2022",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Initialise theme state
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True

from utils.theme import inject_css
inject_css()

# ── Theme toggle (top-right) ──────────────────────────────────────────────────
_, toggle_col = st.columns([0.88, 0.12])
with toggle_col:
    new_dark = st.toggle("Dark mode", value=st.session_state.dark_mode, key="theme_toggle")
    if new_dark != st.session_state.dark_mode:
        st.session_state.dark_mode = new_dark
        st.rerun()

# ── Tabs ──────────────────────────────────────────────────────────────────────
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
