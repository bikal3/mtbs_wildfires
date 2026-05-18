import os
import pandas as pd
import pytest
from pages.story import load_template, inject_stats, compute_story_stats


def _sample_df():
    return pd.DataFrame({
        'event_id':       ['CA001', 'CA002', 'CA003'],
        'acres':          [5_000.0, 50_000.0, 200_000.0],
        'severity':       ['Low', 'Medium', 'High'],
        'year':           [1990, 2000, 2020],
        'ig_date':        ['1990-06-01', '2000-07-15', '2020-08-01'],
        'latitude':       [37.0, 38.0, 39.0],
        'longitude':      [-120.0, -119.0, -118.0],
        'max_temp_c':     [30.0, 35.0, 40.0],
        'min_humidity_pct': [20.0, 15.0, 10.0],
    })


def test_load_template_returns_string():
    path = os.path.join(os.path.dirname(__file__), '..', 'components', 'story_hero.html')
    html = load_template(path)
    assert isinstance(html, str)
    assert len(html) > 0


def test_inject_stats_replaces_placeholders():
    template = "<div>{{total_acres}}</div><div>{{event_count}}</div>"
    result = inject_stats(template, total_acres="4.2M", event_count="2,847")
    assert "4.2M" in result
    assert "2,847" in result
    assert "{{total_acres}}" not in result


def test_compute_story_stats_keys():
    df = _sample_df()
    stats = compute_story_stats(df)
    assert 'total_acres_fmt' in stats
    assert 'event_count_fmt' in stats
    assert 'pct_high_severity_fmt' in stats
    assert 'year_range' in stats


def test_compute_story_stats_values():
    df = _sample_df()
    stats = compute_story_stats(df)
    assert stats['event_count_fmt'] == '3'
    assert stats['year_range'] == '1990\u20132020'
    # 1 of 3 events is High
    assert stats['pct_high_severity_fmt'] == '33%'


def test_build_trend_chart_html_returns_html_string():
    from pages.story import build_trend_chart_html
    df = _sample_df()
    html = build_trend_chart_html(df)
    assert isinstance(html, str)
    assert '<div' in html
    assert 'plotly' in html.lower()
