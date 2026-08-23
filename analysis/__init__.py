"""Streamlit-free analysis layer shared by the site build and (temporarily) the app."""
from analysis.events import (
    compute_map_stats,
    filter_events,
    format_acres,
    severity_color,
)
from analysis.stats import (
    SEVERITY_COLORS,
    SEVERITY_ORDER,
    compute_era_stats,
    compute_research_stats,
    compute_story_stats,
    prepare_decade_severity,
    prepare_evi_recovery_data,
    prepare_fire_season,
    prepare_severity_chart_data,
    prepare_top_fires,
)

__all__ = [
    'SEVERITY_COLORS', 'SEVERITY_ORDER',
    'compute_era_stats', 'compute_map_stats', 'compute_research_stats',
    'compute_story_stats', 'filter_events', 'format_acres',
    'prepare_decade_severity', 'prepare_evi_recovery_data', 'prepare_fire_season',
    'prepare_severity_chart_data', 'prepare_top_fires', 'severity_color',
]
