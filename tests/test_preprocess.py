import pandas as pd
import geopandas as gpd
import pytest
from shapely.geometry import Point, Polygon
from unittest.mock import patch
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.preprocess_data import classify_severity, build_summary


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


def _make_ca_fires():
    """Minimal GeoDataFrame mimicking MTBS shapefile columns."""
    poly = Polygon([(-120, 38), (-119, 38), (-119, 39), (-120, 39)])
    return gpd.GeoDataFrame(
        {
            'Event_ID': ['CA3983912034520210702'],
            'Incid_Name': ['TEST FIRE'],
            'Ig_Date': [1625184000000],   # 2021-07-02 in ms
            'BurnBndAc': [963000.0],
            'Incid_Type': ['Wildfire'],
        },
        geometry=[poly],
        crs='EPSG:4326',
    )


def test_build_summary_columns():
    fires = _make_ca_fires()
    mock_weather = {'max_temp_c': 38.5, 'min_humidity_pct': 11.0}
    with patch('scripts.preprocess_data.get_event_weather', return_value=mock_weather):
        df = build_summary(fires)

    expected_cols = {
        'event_id', 'event_name', 'ig_date', 'year',
        'latitude', 'longitude', 'acres', 'severity',
        'max_temp_c', 'min_humidity_pct',
    }
    assert expected_cols.issubset(set(df.columns))


def test_build_summary_values():
    fires = _make_ca_fires()
    mock_weather = {'max_temp_c': 38.5, 'min_humidity_pct': 11.0}
    with patch('scripts.preprocess_data.get_event_weather', return_value=mock_weather):
        df = build_summary(fires)

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
