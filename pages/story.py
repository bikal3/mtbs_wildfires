import os
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from utils.data_loader import load_data, DATA_PATH, SAMPLE_DATA_PATH
from analysis.stats import compute_story_stats


HERO_PATH = os.path.join(os.path.dirname(__file__), '..', 'components', 'story_hero.html')
SECTIONS_PATH = os.path.join(os.path.dirname(__file__), '..', 'components', 'story_sections.html')


def load_template(path: str) -> str:
    """Read an HTML template file and return its contents as a string."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""


def inject_stats(template: str, **kwargs) -> str:
    """Replace {{key}} placeholders in template with provided keyword values."""
    for key, value in kwargs.items():
        template = template.replace(f'{{{{{key}}}}}', str(value))
    return template


def build_trend_chart_html(df: pd.DataFrame) -> str:
    """Build a Plotly bar chart of total acres burned per year, return as HTML string."""
    yearly = df.groupby('year')['acres'].sum().reset_index()
    fig = px.bar(
        yearly,
        x='year',
        y='acres',
        color='acres',
        color_continuous_scale=['#7f1d1d', '#ef4444', '#f97316', '#fbbf24'],
        labels={'year': '', 'acres': 'Acres Burned'},
        title='',
    )
    fig.update_layout(
        paper_bgcolor='#ffffff',
        plot_bgcolor='#f8fafc',
        font_color='#374151',
        coloraxis_showscale=False,
        margin=dict(l=40, r=20, t=10, b=40),
        height=280,
        xaxis=dict(showgrid=False, tickfont=dict(color='#6b7280')),
        yaxis=dict(showgrid=True, gridcolor='#e2e8f0', tickfont=dict(color='#6b7280')),
    )
    return fig.to_html(include_plotlyjs='cdn', full_html=False, config={'displayModeBar': False})


def render_story():
    if not os.path.exists(DATA_PATH) and not os.path.exists(SAMPLE_DATA_PATH):
        st.error("Data file not found. Run `python scripts/preprocess_data.py` first.")
        return

    df = load_data()
    stats = compute_story_stats(df)
    trend_chart_html = build_trend_chart_html(df)

    # Render hero section
    hero_html = load_template(HERO_PATH)
    sections_html = load_template(SECTIONS_PATH)

    if not hero_html or not sections_html:
        st.error("Story template files not found. Check the components/ directory.")
        return

    hero_html = inject_stats(
        hero_html,
        total_acres=stats['total_acres_fmt'],
        event_count=stats['event_count_fmt'],
        pct_high_severity=stats['pct_high_severity_fmt'],
        year_range=stats['year_range'],
        year_range_label=stats['year_range'],
    )
    components.html(hero_html, height=420, scrolling=False)

    # Render narrative sections with embedded trend chart
    sections_html = inject_stats(sections_html, trend_chart=trend_chart_html)
    components.html(sections_html, height=1700, scrolling=True)
