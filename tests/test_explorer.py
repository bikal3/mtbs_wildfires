import os
import pandas as pd
import pytest
from pages.explorer import filter_events, severity_color, format_acres, compute_map_stats


def _sample_df():
    return pd.DataFrame({
        'event_id':         ['CA001', 'CA002', 'CA003', 'CA004'],
        'event_name':       ['Alpha Fire', 'Beta Fire', 'Gamma Fire', 'Delta Fire'],
        'acres':            [5_000, 50_000, 200_000, 300_000],
        'severity':         ['Low', 'Medium', 'High', 'High'],
        'year':             [1990, 2000, 2010, 2022],
        'ig_date':          ['1990-06-01', '2000-07-15', '2010-08-01', '2022-09-01'],
        'latitude':         [37.0, 38.0, 39.0, 40.0],
        'longitude':        [-120.0, -119.0, -118.0, -117.0],
        'max_temp_c':       [30.0, 35.0, 40.0, 42.0],
        'min_humidity_pct': [20.0, 15.0, 10.0, 8.0],
    })


def test_filter_events_year_range():
    df = _sample_df()
    result = filter_events(df, year_range=(1995, 2015), severities=['Low', 'Medium', 'High'], min_acres=0)
    assert set(result['event_id']) == {'CA002', 'CA003'}


def test_filter_events_severity():
    df = _sample_df()
    result = filter_events(df, year_range=(1984, 2022), severities=['High'], min_acres=0)
    assert set(result['event_id']) == {'CA003', 'CA004'}


def test_filter_events_min_acres():
    df = _sample_df()
    result = filter_events(df, year_range=(1984, 2022), severities=['Low', 'Medium', 'High'], min_acres=100_000)
    assert set(result['event_id']) == {'CA003', 'CA004'}


def test_filter_events_combined():
    df = _sample_df()
    result = filter_events(df, year_range=(2005, 2025), severities=['High'], min_acres=150_000)
    assert set(result['event_id']) == {'CA003', 'CA004'}


def test_severity_color():
    assert severity_color('Low') == '#fbbf24'
    assert severity_color('Medium') == '#f97316'
    assert severity_color('High') == '#ef4444'


def test_format_acres_thousands():
    assert format_acres(5_000) == '5,000'


def test_format_acres_millions():
    assert format_acres(1_200_000) == '1.2M'


def test_compute_map_stats_keys():
    df = _sample_df()
    stats = compute_map_stats(df)
    assert 'event_count' in stats
    assert 'total_acres_fmt' in stats
    assert 'pct_high_fmt' in stats
    assert 'year_range' in stats


def test_compute_map_stats_values():
    df = _sample_df()
    stats = compute_map_stats(df)
    assert stats['event_count'] == 4
    assert stats['pct_high_fmt'] == '50%'
    assert stats['year_range'] == f"1990\u20132022"


def test_compute_map_stats_empty_df():
    empty = pd.DataFrame(columns=['year', 'acres', 'severity'])
    stats = compute_map_stats(empty)
    assert stats['event_count'] == 0
    assert stats['year_range'] == '—'
