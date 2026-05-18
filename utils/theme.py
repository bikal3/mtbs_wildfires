import streamlit as st

DARK = {
    'bg':           '#0a0a0a',
    'bg2':          '#0f0f0f',
    'bg3':          '#1e293b',
    'tab_active':   '#1a1a1a',
    'border':       '#1a1a1a',
    'text':         '#f1f5f9',
    'text2':        '#9ca3af',
    'text3':        '#64748b',
    'chart_paper':  '#111111',
    'chart_plot':   '#111111',
    'chart_grid':   '#1e293b',
    'chart_font':   '#9ca3af',
    'chart_title':  '#e2e8f0',
    'card_bg':      '#1e293b',
    'card_text':    '#e2e8f0',
    'card_sub':     '#64748b',
    'finding_bg':   '#111111',
    'finding_text': '#d1d5db',
    'badge_bg':     '#1e293b',
    'badge_text':   '#94a3b8',
    'folium_tiles': 'CartoDB dark_matter',
    'legend_bg':    '#1e293b',
    'legend_text':  '#e2e8f0',
    'legend_shadow':'rgba(0,0,0,0.5)',
}

LIGHT = {
    'bg':           '#ffffff',
    'bg2':          '#f8fafc',
    'bg3':          '#e2e8f0',
    'tab_active':   '#ffffff',
    'border':       '#e2e8f0',
    'text':         '#0f172a',
    'text2':        '#374151',
    'text3':        '#6b7280',
    'chart_paper':  '#ffffff',
    'chart_plot':   '#f8fafc',
    'chart_grid':   '#e2e8f0',
    'chart_font':   '#374151',
    'chart_title':  '#0f172a',
    'card_bg':      '#f1f5f9',
    'card_text':    '#0f172a',
    'card_sub':     '#6b7280',
    'finding_bg':   '#f8fafc',
    'finding_text': '#374151',
    'badge_bg':     '#e2e8f0',
    'badge_text':   '#374151',
    'folium_tiles': 'CartoDB positron',
    'legend_bg':    '#ffffff',
    'legend_text':  '#0f172a',
    'legend_shadow':'rgba(0,0,0,0.15)',
}

DARK_CSS = """
<style>
[data-testid="stAppViewContainer"] { background-color: #0a0a0a; }
[data-testid="stHeader"]            { background-color: #0a0a0a; }
section[data-testid="stSidebar"]    { background-color: #0f0f0f; }
.stTabs [data-baseweb="tab-list"] {
    gap: 8px; background-color: #0f0f0f;
    padding: 8px 16px 0; border-bottom: 1px solid #1a1a1a;
}
.stTabs [data-baseweb="tab"] {
    color: #6b7280; background-color: transparent;
    border-radius: 4px 4px 0 0; padding: 8px 24px;
    font-weight: 600; font-size: 14px;
}
.stTabs [aria-selected="true"] { background-color: #1a1a1a !important; color: #f97316 !important; }
h1, h2, h3 { color: #f1f5f9; }
</style>
"""

LIGHT_CSS = """
<style>
[data-testid="stAppViewContainer"] { background-color: #ffffff; }
[data-testid="stHeader"]            { background-color: #ffffff; }
section[data-testid="stSidebar"]    { background-color: #f8fafc; }
.stTabs [data-baseweb="tab-list"] {
    gap: 8px; background-color: #f1f5f9;
    padding: 8px 16px 0; border-bottom: 1px solid #e2e8f0;
}
.stTabs [data-baseweb="tab"] {
    color: #6b7280; background-color: transparent;
    border-radius: 4px 4px 0 0; padding: 8px 24px;
    font-weight: 600; font-size: 14px;
}
.stTabs [aria-selected="true"] { background-color: #ffffff !important; color: #f97316 !important; }
h1, h2, h3 { color: #0f172a; }
p, li, label { color: #374151; }
[data-testid="stMetricLabel"]  > div { color: #6b7280 !important; }
[data-testid="stMetricValue"]  > div { color: #0f172a !important; }
[data-testid="stCaptionContainer"] p { color: #6b7280 !important; }
[data-testid="stMarkdownContainer"] p { color: #374151 !important; }
[data-testid="stMarkdownContainer"] li { color: #374151 !important; }
[data-testid="stVerticalBlock"]     { color: #374151; }
.stAlert { background-color: #f1f5f9 !important; color: #374151 !important; }
[data-testid="stHorizontalBlock"] > div { background-color: transparent; }
[data-baseweb="select"] > div { background-color: #f1f5f9 !important; color: #0f172a !important; }
[data-baseweb="input"]  > div { background-color: #f1f5f9 !important; color: #0f172a !important; }
.stSlider [data-baseweb="slider"] { background-color: transparent; }
</style>
"""


def get_theme() -> dict:
    """Return the active theme dict based on session state."""
    return DARK if st.session_state.get('dark_mode', True) else LIGHT


def inject_css():
    """Inject the active theme CSS into the page."""
    st.markdown(DARK_CSS if st.session_state.get('dark_mode', True) else LIGHT_CSS,
                unsafe_allow_html=True)
