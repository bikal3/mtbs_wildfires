import os
import pandas as pd
import pytest
from pages.research import (
    prepare_severity_chart_data,
    prepare_evi_recovery_data,
    compute_research_stats,
)


def _sample_df():
    return pd.DataFrame({
        'event_id':         ['CA001', 'CA002', 'CA003', 'CA004'],
        'acres':            [5_000, 50_000, 200_000, 300_000],
        'severity':         ['Low', 'Medium', 'High', 'High'],
        'year':             [1990, 2000, 2010, 2020],
        'ig_date':          ['1990-06-01', '2000-07-15', '2010-08-01', '2020-09-01'],
        'latitude':         [37.0, 38.0, 39.0, 40.0],
        'longitude':        [-120.0, -119.0, -118.0, -117.0],
        'max_temp_c':       [30.0, 35.0, 40.0, 42.0],
        'min_humidity_pct': [20.0, 15.0, 10.0, 8.0],
    })


def test_prepare_severity_chart_data_columns():
    df = _sample_df()
    result = prepare_severity_chart_data(df)
    assert 'year' in result.columns
    assert 'acres' in result.columns


def test_prepare_severity_chart_data_aggregation():
    df = _sample_df()
    result = prepare_severity_chart_data(df)
    # year 2020 should have 300_000 acres
    row_2020 = result[result['year'] == 2020].iloc[0]
    assert row_2020['acres'] == 300_000


def test_prepare_evi_recovery_data_shape():
    result = prepare_evi_recovery_data()
    assert 'months_after_fire' in result.columns
    assert 'low_severity' in result.columns
    assert 'high_severity' in result.columns
    assert len(result) > 0


def test_compute_research_stats_keys():
    df = _sample_df()
    stats = compute_research_stats(df)
    assert 'total_events' in stats
    assert 'total_acres_m' in stats
    assert 'pct_high' in stats
    assert 'year_min' in stats
    assert 'year_max' in stats


def test_compute_research_stats_values():
    df = _sample_df()
    stats = compute_research_stats(df)
    assert stats['total_events'] == 4
    assert stats['year_min'] == 1990
    assert stats['year_max'] == 2020
    assert stats['pct_high'] == 50.0
