"""Per-event filtering and formatting. No Streamlit imports."""
import pandas as pd

MAP_SEVERITY_COLORS = {'Low': '#fbbf24', 'Medium': '#f97316', 'High': '#ef4444'}


def severity_color(severity: str) -> str:
    """Hex colour for a severity tier on the map."""
    return MAP_SEVERITY_COLORS.get(severity, '#6b7280')


def format_acres(acres: float) -> str:
    """Human-readable acreage: 1.2M above a million, else comma-grouped."""
    if acres >= 1_000_000:
        return f"{acres / 1_000_000:.1f}M"
    return f"{acres:,.0f}"


def filter_events(df: pd.DataFrame, year_range: tuple, severities: list,
                  min_acres: float) -> pd.DataFrame:
    """Apply year range, severity, and minimum acreage filters."""
    mask = (
        (df['year'] >= year_range[0]) &
        (df['year'] <= year_range[1]) &
        (df['severity'].isin(severities)) &
        (df['acres'] >= min_acres)
    )
    return df[mask].copy()


def compute_map_stats(df: pd.DataFrame) -> dict:
    """Aggregates for the Explorer summary bar."""
    total_acres = df['acres'].sum()
    pct_high = len(df[df['severity'] == 'High']) / len(df) * 100 if len(df) > 0 else 0
    year_min = int(df['year'].min()) if len(df) > 0 else None
    year_max = int(df['year'].max()) if len(df) > 0 else None
    return {
        'event_count': len(df),
        'total_acres_fmt': format_acres(total_acres),
        'pct_high_fmt': f"{pct_high:.0f}%",
        'year_range': f"{year_min}–{year_max}" if year_min is not None else '—',
    }
