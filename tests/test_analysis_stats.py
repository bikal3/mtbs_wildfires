import os
import pandas as pd
import pytest
from analysis.stats import (
    prepare_severity_chart_data,
    prepare_evi_recovery_data,
    compute_research_stats,
)


def _sample_df():
    return pd.DataFrame({
        'event_id':         ['CA001', 'CA002', 'CA003', 'CA004'],
        'event_name':       ['Alpha Fire', 'Beta Fire', 'Gamma Fire', 'Delta Fire'],
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


from analysis.stats import (
    compute_era_stats,
    prepare_decade_severity,
    prepare_fire_season,
    prepare_top_fires,
)


def test_compute_era_stats_covers_three_eras():
    df = _sample_df()
    eras = compute_era_stats(df)
    assert [e['label'] for e in eras] == ['1984–1999', '2000–2009', '2010–2022']


def test_compute_era_stats_values():
    df = _sample_df()   # 1990 Low 5k, 2000 Medium 50k, 2010 High 200k, 2020 High 300k
    eras = {e['label']: e for e in compute_era_stats(df)}
    assert eras['1984–1999']['events'] == 1
    assert eras['1984–1999']['pct_high'] == 0.0
    assert eras['2010–2022']['events'] == 2
    assert eras['2010–2022']['pct_high'] == 100.0
    assert eras['2010–2022']['avg_acres'] == 250_000


def test_compute_era_stats_handles_empty_era():
    df = _sample_df()[lambda d: d['year'] == 1990]
    eras = {e['label']: e for e in compute_era_stats(df)}
    assert eras['2000–2009']['events'] == 0
    assert eras['2000–2009']['acres_m'] == 0.0


def test_prepare_decade_severity_counts():
    df = _sample_df()
    result = prepare_decade_severity(df)
    assert set(result.columns) == {'decade', 'severity', 'count'}
    assert result['count'].sum() == 4


def test_prepare_top_fires_orders_ascending_for_plotly():
    df = _sample_df()
    top = prepare_top_fires(df, n=3)
    assert list(top['acres']) == sorted(top['acres'])
    assert len(top) == 3


def test_prepare_top_fires_labels_are_title_cased_with_year():
    df = _sample_df().assign(event_name=['ALPHA FIRE', 'BETA FIRE', 'GAMMA FIRE', 'DELTA FIRE'])
    top = prepare_top_fires(df, n=1)
    assert top.iloc[0]['label'] == 'Delta Fire (2020)'


def test_prepare_fire_season_always_has_twelve_months():
    df = _sample_df()
    season = prepare_fire_season(df)
    assert len(season) == 12
    assert list(season['month_name'])[:3] == ['Jan', 'Feb', 'Mar']
    assert season['count'].sum() == 4
