import json
import pandas as pd
import pytest

from scripts.build_site import build_events, build_stats, EVENT_FIELDS


def _sample_df():
    return pd.DataFrame({
        'event_id':         ['CA001', 'CA002', 'CA003', 'CA004'],
        'event_name':       ['ALPHA', 'BETA', 'GAMMA', 'DELTA'],
        'acres':            [5_000.0, 50_000.0, 200_000.0, 300_000.0],
        'severity':         ['Low', 'Medium', 'High', 'High'],
        'year':             [1990, 2000, 2010, 2020],
        'ig_date':          ['1990-06-01', '2000-07-15', '2010-08-01', '2020-09-01'],
        'latitude':         [37.0, 38.0, 39.0, 40.0],
        'longitude':        [-120.0, -119.0, -118.0, -117.0],
        'max_temp_c':       [30.0, 35.0, 40.0, 42.0],
        'min_humidity_pct': [20.0, 15.0, 10.0, 8.0],
    })


def test_build_events_returns_one_record_per_row():
    events = build_events(_sample_df())
    assert len(events) == 4
    assert events[0]['event_id'] == 'CA001'


def test_build_events_has_exactly_the_expected_fields():
    events = build_events(_sample_df())
    assert set(events[0].keys()) == set(EVENT_FIELDS)


def test_build_events_is_json_serialisable():
    """numpy scalars are not JSON-serialisable; every value must be a Python native."""
    json.dumps(build_events(_sample_df()))


def test_build_events_nulls_survive_as_none():
    df = _sample_df()
    df.loc[0, 'max_temp_c'] = None
    events = build_events(df)
    assert events[0]['max_temp_c'] is None


def test_build_stats_top_level_keys():
    stats = build_stats(_sample_df(), is_sample=False)
    assert set(stats.keys()) == {
        'is_sample', 'event_count', 'story', 'research', 'acres_by_year',
        'eras', 'decade_severity', 'top_fires', 'fire_season', 'evi_recovery',
    }


def test_build_stats_matches_the_analysis_functions():
    from analysis.stats import compute_era_stats, compute_research_stats
    df = _sample_df()
    stats = build_stats(df, is_sample=False)
    assert stats['research'] == compute_research_stats(df)
    assert stats['eras'] == compute_era_stats(df)


def test_build_stats_fire_season_has_twelve_months():
    stats = build_stats(_sample_df(), is_sample=False)
    assert len(stats['fire_season']) == 12


def test_build_stats_is_json_serialisable():
    json.dumps(build_stats(_sample_df(), is_sample=False))


def test_build_stats_flags_sample_data():
    assert build_stats(_sample_df(), is_sample=True)['is_sample'] is True
    assert build_stats(_sample_df(), is_sample=False)['is_sample'] is False


def test_build_events_emits_no_nan_literal():
    """json.dumps writes bare NaN, which JSON.parse rejects. Nulls must be null."""
    df = _sample_df()
    df.loc[0, 'max_temp_c'] = float('nan')
    df.loc[1, 'min_humidity_pct'] = float('nan')
    text = json.dumps(build_events(df), allow_nan=False)   # raises if NaN survives
    assert 'NaN' not in text
    assert json.loads(text)[0]['max_temp_c'] is None


def test_build_stats_evi_is_labelled_illustrative():
    """The EVI curves are hardcoded, not derived; the site must not imply otherwise."""
    evi = build_stats(_sample_df(), is_sample=False)['evi_recovery']
    assert evi['illustrative'] is True
    assert len(evi['months']) == len(evi['low']) == len(evi['high'])
