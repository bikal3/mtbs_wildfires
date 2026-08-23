import pandas as pd
import pytest
from unittest.mock import patch

from scripts.preprocess_data import (
    MAX_YEAR,
    build_summary,
    classify_severity,
    filter_california_wildfires,
)


def test_classify_severity_low():
    assert classify_severity(5_000) == 'Low'


def test_classify_severity_medium():
    assert classify_severity(50_000) == 'Medium'


def test_classify_severity_high():
    assert classify_severity(150_000) == 'High'


def test_classify_severity_boundaries():
    assert classify_severity(9_999) == 'Low'
    assert classify_severity(10_000) == 'Medium'
    assert classify_severity(99_999) == 'Medium'
    assert classify_severity(100_000) == 'High'


# ── MTBS attribute table ──────────────────────────────────────────────────────
# The official USGS release uses lowercase column names, an ISO date string
# (not epoch ms), and supplies the burn-boundary centre directly.

def _raw_mtbs() -> pd.DataFrame:
    return pd.DataFrame({
        'event_id':   ['CA3983912034520210702', 'OR4000012000020200101',
                       'CA3500011800019950601', 'CA3600011900020240801'],
        'incid_name': ['TEST FIRE', 'OREGON FIRE', 'OLD FIRE', 'TOO NEW FIRE'],
        'incid_type': ['Wildfire', 'Wildfire', 'Prescribed Fire', 'Wildfire'],
        'burnbndac':  [963000, 5000, 20000, 1000],
        'ig_date':    ['2021-07-02', '2020-01-01', '1995-06-01', '2024-08-01'],
        'burnbndlat': ['38.5', '44.0', '35.0', '36.0'],
        'burnbndlon': ['-119.5', '-121.0', '-118.0', '-119.0'],
    })


def test_filter_keeps_only_california_wildfires():
    result = filter_california_wildfires(_raw_mtbs())
    assert list(result['event_id']) == ['CA3983912034520210702']


def test_filter_excludes_events_after_max_year():
    """Data now runs to 2025, but the project is scoped to MAX_YEAR."""
    assert MAX_YEAR == 2022
    result = filter_california_wildfires(_raw_mtbs())
    assert 'CA3600011900020240801' not in set(result['event_id'])


def test_filter_adds_parsed_datetime_and_sorts_oldest_first():
    raw = _raw_mtbs()
    raw.loc[len(raw)] = ['CA1111111111119900101', 'EARLY FIRE', 'Wildfire',
                         7000, '1990-01-01', '37.0', '-120.0']
    result = filter_california_wildfires(raw)
    assert 'ig_dt' in result.columns
    assert list(result['ig_dt'].dt.year) == [1990, 2021]


def _make_ca_fires() -> pd.DataFrame:
    return filter_california_wildfires(_raw_mtbs())


def test_build_summary_columns():
    mock_weather = {'max_temp_c': 38.5, 'min_humidity_pct': 11.0}
    with patch('scripts.preprocess_data.get_event_weather', return_value=mock_weather):
        df = build_summary(_make_ca_fires())

    expected_cols = {
        'event_id', 'event_name', 'ig_date', 'year',
        'latitude', 'longitude', 'acres', 'severity',
        'max_temp_c', 'min_humidity_pct',
    }
    assert expected_cols.issubset(set(df.columns))


def test_build_summary_values():
    mock_weather = {'max_temp_c': 38.5, 'min_humidity_pct': 11.0}
    with patch('scripts.preprocess_data.get_event_weather', return_value=mock_weather):
        df = build_summary(_make_ca_fires())

    row = df.iloc[0]
    assert row['event_id'] == 'CA3983912034520210702'
    assert row['event_name'] == 'TEST FIRE'
    assert row['ig_date'] == '2021-07-02'
    assert row['year'] == 2021
    assert abs(row['latitude'] - 38.5) < 0.01
    assert abs(row['longitude'] - (-119.5)) < 0.01
    assert row['acres'] == 963000.0
    assert row['severity'] == 'High'
    assert row['max_temp_c'] == 38.5
    assert row['min_humidity_pct'] == 11.0


def test_build_summary_aborts_when_failure_rate_is_systemic():
    fires = _make_ca_fires()
    with patch('scripts.preprocess_data.get_event_weather', side_effect=RuntimeError('api down')):
        with pytest.raises(RuntimeError, match='exceeds'):
            build_summary(fires)


def test_build_summary_tolerates_isolated_failures():
    fires = _make_ca_fires()
    with patch('scripts.preprocess_data.get_event_weather', side_effect=RuntimeError('blip')):
        df = build_summary(fires, max_failure_pct=100.0)
    assert df.iloc[0]['max_temp_c'] is None
    assert df.iloc[0]['event_id'] == 'CA3983912034520210702'


# ── Weather API ───────────────────────────────────────────────────────────────

def test_archive_url_is_the_archive_endpoint():
    """The historical-forecast endpoint only serves 2016+; this dataset starts in 1984."""
    from scripts.preprocess_data import ARCHIVE_URL
    assert ARCHIVE_URL == 'https://archive-api.open-meteo.com/v1/archive'
    assert 'historical-forecast' not in ARCHIVE_URL


def test_get_event_weather_raises_instead_of_returning_none():
    """A failed fetch must raise, not silently produce a null row."""
    from datetime import datetime
    from scripts import preprocess_data

    def boom(*args, **kwargs):
        raise RuntimeError('api down')

    original = preprocess_data._openmeteo.weather_api
    preprocess_data._openmeteo.weather_api = boom
    try:
        with pytest.raises(RuntimeError):
            preprocess_data.get_event_weather(34.2, -117.72, datetime(2021, 7, 2))
    finally:
        preprocess_data._openmeteo.weather_api = original


def test_preprocess_needs_no_dask_leafmap_or_boto3():
    """The heavy geo/AWS stack was dropped: attributes only, plain HTTPS download."""
    import scripts.preprocess_data as pp
    source = open(pp.__file__).read()
    for banned in ('dask', 'leafmap', 'boto3', 'botocore', 'geopandas'):
        assert banned not in source, f'{banned} should no longer be imported'
    assert hasattr(pp, 'download_mtbs_shapefile')
