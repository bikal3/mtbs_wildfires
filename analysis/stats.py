"""Pure pandas aggregations over the MTBS summary frame. No Streamlit imports."""
import pandas as pd

SEVERITY_ORDER = ['Low', 'Medium', 'High']
SEVERITY_COLORS = {'Low': '#22c55e', 'Medium': '#f97316', 'High': '#ef4444'}

MONTH_NAMES = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
               7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}

ERAS = [('1984–1999', 1984, 1999), ('2000–2009', 2000, 2009), ('2010–2022', 2010, 2022)]


def compute_story_stats(df: pd.DataFrame) -> dict:
    """Headline numbers for the Story hero cards."""
    total_acres = df['acres'].sum()
    if total_acres >= 1_000_000:
        total_acres_fmt = f"{total_acres / 1_000_000:.1f}M"
    else:
        total_acres_fmt = f"{total_acres / 1_000:.0f}K"

    pct_high = (len(df[df['severity'] == 'High']) / len(df) * 100) if len(df) > 0 else 0.0

    return {
        'total_acres_fmt': total_acres_fmt,
        'event_count_fmt': f"{len(df):,}",
        'pct_high_severity_fmt': f"{pct_high:.0f}%",
        'year_range': f"{df['year'].min()}–{df['year'].max()}",
    }


def compute_research_stats(df: pd.DataFrame) -> dict:
    """Headline numbers for the Research page subtitle and findings."""
    total_acres = df['acres'].sum()
    pct_high = round(len(df[df['severity'] == 'High']) / len(df) * 100, 1) if len(df) > 0 else 0.0
    return {
        'total_events': len(df),
        'total_acres_m': float(round(total_acres / 1_000_000, 1)),
        'pct_high': pct_high,
        'year_min': int(df['year'].min()) if len(df) > 0 else 0,
        'year_max': int(df['year'].max()) if len(df) > 0 else 0,
    }


def prepare_severity_chart_data(df: pd.DataFrame) -> pd.DataFrame:
    """Total acres burned per year."""
    return df.groupby('year')['acres'].sum().reset_index()


def prepare_decade_severity(df: pd.DataFrame) -> pd.DataFrame:
    """Count of Low/Medium/High events per era."""
    d = df.copy()
    d['decade'] = pd.cut(d['year'], bins=[1983, 1999, 2009, 2022],
                         labels=[label for label, _, _ in ERAS])
    return (d.groupby(['decade', 'severity'], observed=True)
             .size().reset_index(name='count'))


def compute_era_stats(df: pd.DataFrame) -> list:
    """Per-era summary dicts for the comparison cards."""
    result = []
    for label, y0, y1 in ERAS:
        sub = df[(df['year'] >= y0) & (df['year'] <= y1)]
        if len(sub) == 0:
            result.append({'label': label, 'events': 0, 'acres_m': 0.0,
                           'avg_acres': 0, 'pct_high': 0.0})
            continue
        result.append({
            'label': label,
            'events': len(sub),
            'acres_m': round(sub['acres'].sum() / 1_000_000, 1),
            'avg_acres': int(sub['acres'].mean()),
            'pct_high': round(len(sub[sub['severity'] == 'High']) / len(sub) * 100, 1),
        })
    return result


def prepare_top_fires(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """The n largest fires by acreage, ascending so Plotly draws largest at the top."""
    top = df.nlargest(n, 'acres')[['event_name', 'year', 'acres', 'severity']].copy()
    top['label'] = top['event_name'].str.title() + ' (' + top['year'].astype(str) + ')'
    return top.sort_values('acres')


def prepare_fire_season(df: pd.DataFrame) -> pd.DataFrame:
    """Fire count by ignition month, with all 12 months always present."""
    d = df.copy()
    d['month'] = pd.to_datetime(d['ig_date']).dt.month
    counts = (pd.DataFrame({'month': range(1, 13)})
              .merge(d.groupby('month').size().reset_index(name='count'), on='month', how='left')
              .fillna(0))
    counts['month_name'] = counts['month'].map(MONTH_NAMES)
    counts['count'] = counts['count'].astype(int)
    return counts


def prepare_evi_recovery_data() -> pd.DataFrame:
    """
    Illustrative 3-year EVI recovery curves.

    These are hardcoded reference values, NOT computed from this dataset — the
    per-event EVI work lives in src/evi.ipynb and was never wired through.
    Every chart built from this must be labelled as illustrative.
    """
    months = list(range(0, 37, 3))
    low_severity  = [0.55, 0.42, 0.48, 0.51, 0.54, 0.55, 0.56, 0.57, 0.57, 0.58, 0.58, 0.58, 0.59]
    high_severity = [0.55, 0.10, 0.15, 0.20, 0.25, 0.28, 0.30, 0.32, 0.33, 0.34, 0.35, 0.35, 0.36]
    return pd.DataFrame({'months_after_fire': months,
                         'low_severity': low_severity,
                         'high_severity': high_severity})
