"""
Offline pre-processing script.
Run once to generate data/mtbs_ca_summary.csv.

Usage:
    python scripts/preprocess_data.py
"""
import os
import botocore
import botocore.config
import boto3
import numpy as np
import pandas as pd
import geopandas as gpd
import openmeteo_requests
import requests_cache
from retry_requests import retry
from datetime import datetime, timedelta, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SUMMARY_COLUMNS = [
    'event_id', 'event_name', 'ig_date', 'year',
    'latitude', 'longitude', 'acres', 'severity',
    'max_temp_c', 'min_humidity_pct',
]

ARCHIVE_URL = 'https://archive-api.open-meteo.com/v1/archive'

# Historical weather never changes, so the cache never expires — re-runs are free.
_cache_session = requests_cache.CachedSession(
    os.path.join(PROJECT_ROOT, '.cache', 'openmeteo'), expire_after=-1)
_retry_session = retry(_cache_session, retries=5, backoff_factor=0.4)
_openmeteo = openmeteo_requests.Client(session=_retry_session)


def load_mtbs_california(local_path: str) -> gpd.GeoDataFrame:
    """
    Download MTBS shapefile from AWS public bucket (anonymous access)
    and return a GeoDataFrame filtered to California wildfires.
    """
    # Lazy imports: dask_geopandas and leafmap are only needed at runtime
    from utils.source_coop_utils import get_mtbs_shp  # noqa: PLC0415

    s3_client = boto3.client(
        's3',
        region_name='us-east-1',
        config=botocore.config.Config(signature_version=botocore.UNSIGNED),
    )
    ddf = get_mtbs_shp('mtbs_perims_DD', s3_client, local_path)
    gdf = ddf.compute()
    ca_fires = gdf[
        (gdf['Event_ID'].str.startswith('CA')) &
        (gdf['Incid_Type'] == 'Wildfire')
    ].copy()
    ca_fires = ca_fires.to_crs('EPSG:4326')
    return ca_fires


def classify_severity(acres: float) -> str:
    """
    Classify fire event severity by burn area.
      Low    : < 10,000 acres
      Medium : 10,000 - 99,999 acres
      High   : >= 100,000 acres
    """
    if acres < 10_000:
        return 'Low'
    elif acres < 100_000:
        return 'Medium'
    return 'High'


def get_event_weather(lat: float, lon: float, ig_date_ms: int) -> dict:
    """
    Peak temperature (C) and minimum relative humidity (%) over a window running
    from 3 days before to 14 days after ignition (18 days inclusive).

    Raises on failure. Callers decide what an individual failure means — see
    build_summary, which aborts only if the failure *rate* is systemic.
    """
    ig_date = datetime.fromtimestamp(ig_date_ms / 1000, tz=timezone.utc).replace(tzinfo=None)
    start = (ig_date - timedelta(days=3)).strftime('%Y-%m-%d')
    end = (ig_date + timedelta(days=14)).strftime('%Y-%m-%d')

    responses = _openmeteo.weather_api(ARCHIVE_URL, params={
        'latitude': lat,
        'longitude': lon,
        'start_date': start,
        'end_date': end,
        'daily': ['temperature_2m_max', 'relative_humidity_2m_min'],
        'timezone': 'GMT',
    })
    daily = responses[0].Daily()
    temps = daily.Variables(0).ValuesAsNumpy()
    humidity = daily.Variables(1).ValuesAsNumpy()

    if np.all(np.isnan(temps)) or np.all(np.isnan(humidity)):
        raise ValueError(f'archive API returned no usable data for ({lat}, {lon}) {start}..{end}')

    return {
        'max_temp_c': round(float(np.nanmax(temps)), 1),
        'min_humidity_pct': round(float(np.nanmin(humidity)), 1),
    }


def build_summary(ca_fires: gpd.GeoDataFrame) -> pd.DataFrame:
    """
    Build the summary DataFrame from a California MTBS GeoDataFrame.
    Calls get_event_weather for each row — expected to be slow on full dataset.
    """
    records = []
    for _, row in ca_fires.iterrows():
        centroid = row.geometry.centroid
        ig_ms = int(row['Ig_Date'])
        ig_dt = datetime.fromtimestamp(ig_ms / 1000, tz=timezone.utc).replace(tzinfo=None)
        ig_date_str = ig_dt.strftime('%Y-%m-%d')
        year = ig_dt.year
        weather = get_event_weather(centroid.y, centroid.x, ig_ms)
        records.append({
            'event_id': row['Event_ID'],
            'event_name': row['Incid_Name'],
            'ig_date': ig_date_str,
            'year': year,
            'latitude': round(centroid.y, 6),
            'longitude': round(centroid.x, 6),
            'acres': round(float(row['BurnBndAc']), 1),
            'severity': classify_severity(float(row['BurnBndAc'])),
            'max_temp_c': weather['max_temp_c'],
            'min_humidity_pct': weather['min_humidity_pct'],
        })
    return pd.DataFrame(records, columns=SUMMARY_COLUMNS)


if __name__ == '__main__':
    local_path = os.path.join(PROJECT_ROOT, 'data', 'raw')
    os.makedirs(local_path, exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT, 'data'), exist_ok=True)

    print('Loading MTBS California fires from AWS S3...')
    ca_fires = load_mtbs_california(local_path)
    print(f'Found {len(ca_fires)} California wildfire events.')

    print('Fetching weather data and building summary...')
    summary = build_summary(ca_fires)

    output_path = os.path.join(PROJECT_ROOT, 'data', 'mtbs_ca_summary.csv')
    summary.to_csv(output_path, index=False)
    print(f'Saved {len(summary)} events to {output_path}')
