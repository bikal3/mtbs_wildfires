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
/* ── 1. Override Streamlit's injected CSS variables ─────────────────────── */
:root {
    --text-color:                  #0f172a !important;
    --background-color:            #ffffff !important;
    --secondary-background-color:  #f1f5f9 !important;
    --primary-color:               #f97316 !important;
}

/* ── 2. App shell backgrounds ───────────────────────────────────────────── */
.stApp,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="stMain"],
[data-testid="block-container"]          { background-color: #ffffff !important; }
[data-testid="stHeader"]                 { background-color: #ffffff !important; border-bottom: 1px solid #e2e8f0; }
section[data-testid="stSidebar"]         { background-color: #f8fafc !important; }

/* ── 3. Global text colour (catches everything config.toml made white) ───── */
.stApp, .stApp *                         { color: #374151; }
h1, h2, h3, h4, h5, h6                  { color: #0f172a !important; }
a                                        { color: #f97316 !important; }

/* ── 4. Streamlit text primitives ───────────────────────────────────────── */
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] *    { color: #374151 !important; }
[data-testid="stText"],
[data-testid="stText"] *                 { color: #374151 !important; }
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] *     { color: #6b7280 !important; }
[data-testid="stHeadingWithActionElements"],
[data-testid="stHeadingWithActionElements"] * { color: #0f172a !important; }
[data-testid="stSubheader"],
[data-testid="stSubheader"] *            { color: #0f172a !important; }

/* ── 5. Metrics ─────────────────────────────────────────────────────────── */
[data-testid="metric-container"]         { background: transparent !important; }
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] *          { color: #6b7280 !important; }
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] *          { color: #0f172a !important; }
[data-testid="stMetricDelta"],
[data-testid="stMetricDelta"] *          { color: #6b7280 !important; }

/* ── 6. Tabs ────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: #f1f5f9 !important;
    padding: 8px 16px 0;
    border-bottom: 1px solid #e2e8f0;
}
.stTabs [data-baseweb="tab"]             { color: #6b7280 !important; background-color: transparent !important; border-radius: 4px 4px 0 0; padding: 8px 24px; font-weight: 600; font-size: 14px; }
.stTabs [data-baseweb="tab"] *           { color: inherit !important; }
.stTabs [aria-selected="true"]           { background-color: #ffffff !important; color: #f97316 !important; }

/* ── 7. Form controls ───────────────────────────────────────────────────── */
[data-baseweb="select"] > div,
[data-baseweb="select"] [data-baseweb="input"] { background-color: #f1f5f9 !important; color: #0f172a !important; border-color: #e2e8f0 !important; }
[data-baseweb="select"] span,
[data-baseweb="select"] div              { color: #0f172a !important; }
[data-baseweb="popover"],
[data-baseweb="popover"] *               { background-color: #ffffff !important; color: #0f172a !important; }
[role="listbox"],
[role="listbox"] *                       { background-color: #ffffff !important; color: #0f172a !important; }
[role="option"]                          { color: #0f172a !important; }
[role="option"]:hover                    { background-color: #f1f5f9 !important; }
[data-baseweb="input"] > div             { background-color: #f1f5f9 !important; color: #0f172a !important; }
[data-testid="stSlider"] label,
[data-testid="stSlider"] *               { color: #374151 !important; }
[data-testid="stToggle"] span            { color: #374151 !important; }

/* ── 8. Alerts / info boxes ─────────────────────────────────────────────── */
[data-testid="stAlert"]                  { background-color: #eff6ff !important; border-color: #bfdbfe !important; }
[data-testid="stAlert"] *                { color: #1d4ed8 !important; }
[data-testid="stAlert"][data-baseweb="notification"][kind="warning"],
[data-testid="stAlert"][data-baseweb="notification"][kind="warning"] * { color: #92400e !important; }

/* ── 9. Expander ────────────────────────────────────────────────────────── */
[data-testid="stExpander"]               { border-color: #e2e8f0 !important; background-color: #f8fafc !important; }
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary *,
[data-testid="stExpander"] p             { color: #374151 !important; }

/* ── 10. Divider ────────────────────────────────────────────────────────── */
hr                                       { border-color: #e2e8f0 !important; }

/* ── 11. Buttons ────────────────────────────────────────────────────────── */
[data-testid="stDownloadButton"] button  { background-color: #f1f5f9 !important; color: #374151 !important; border-color: #e2e8f0 !important; }
[data-testid="stLinkButton"] a           { background-color: #f1f5f9 !important; color: #374151 !important; border-color: #e2e8f0 !important; }
button[kind="secondary"]                 { background-color: #f1f5f9 !important; color: #374151 !important; border-color: #e2e8f0 !important; }
</style>
"""


def get_theme() -> dict:
    """Return the active theme dict based on session state."""
    return DARK if st.session_state.get('dark_mode', True) else LIGHT


def inject_css():
    """Inject the active theme CSS into the page."""
    st.markdown(DARK_CSS if st.session_state.get('dark_mode', True) else LIGHT_CSS,
                unsafe_allow_html=True)
