"""Single light theme — dark mode has been removed."""

THEME = {
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
    'legend_shadow':'rgba(0,0,0,0.12)',
}


def get_theme() -> dict:
    return THEME
