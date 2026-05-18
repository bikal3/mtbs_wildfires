import os
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components


DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'mtbs_ca_summary.csv')
HERO_PATH = os.path.join(os.path.dirname(__file__), '..', 'components', 'story_hero.html')
SECTIONS_PATH = os.path.join(os.path.dirname(__file__), '..', 'components', 'story_sections.html')


def load_template(path: str) -> str:
    """Read an HTML template file and return its contents as a string."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def inject_stats(template: str, **kwargs) -> str:
    """Replace {{key}} placeholders in template with provided keyword values."""
    for key, value in kwargs.items():
        template = template.replace(f'{{{{{key}}}}}', str(value))
    return template


def compute_story_stats(df: pd.DataFrame) -> dict:
    """Compute display statistics from the summary DataFrame."""
    total_acres = df['acres'].sum()
    if total_acres >= 1_000_000:
        total_acres_fmt = f"{total_acres / 1_000_000:.1f}M"
    else:
        total_acres_fmt = f"{total_acres / 1_000:.0f}K"

    event_count_fmt = f"{len(df):,}"
    pct_high = (len(df[df['severity'] == 'High']) / len(df) * 100) if len(df) > 0 else 0.0
    pct_high_severity_fmt = f"{pct_high:.0f}%"
    year_range = f"{df['year'].min()}\u2013{df['year'].max()}"

    return {
        'total_acres_fmt': total_acres_fmt,
        'event_count_fmt': event_count_fmt,
        'pct_high_severity_fmt': pct_high_severity_fmt,
        'year_range': year_range,
    }


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
        paper_bgcolor='#111',
        plot_bgcolor='#111',
        font_color='#9ca3af',
        coloraxis_showscale=False,
        margin=dict(l=40, r=20, t=10, b=40),
        height=280,
        xaxis=dict(showgrid=False, tickfont=dict(color='#6b7280')),
        yaxis=dict(showgrid=True, gridcolor='#1e293b', tickfont=dict(color='#6b7280')),
    )
    return fig.to_html(include_plotlyjs='cdn', full_html=False, config={'displayModeBar': False})


@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH)


def render_story():
    if not os.path.exists(DATA_PATH):
        st.error("Data file not found. Run `python scripts/preprocess_data.py` first.")
        return

    df = load_data()
    stats = compute_story_stats(df)
    trend_chart_html = build_trend_chart_html(df)

    # Render hero section
    hero_html = load_template(HERO_PATH)
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
    sections_html = load_template(SECTIONS_PATH)
    sections_html = inject_stats(sections_html, trend_chart=trend_chart_html)
    components.html(sections_html, height=1100, scrolling=True)
