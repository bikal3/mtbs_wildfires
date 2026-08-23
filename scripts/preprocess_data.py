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


MTBS_BUCKET = 'cboettig'
MTBS_PREFIX = 'fire/USGS-MTBS/'
MTBS_LAYER = 'mtbs_perims_DD'


def download_mtbs_shapefile(local_path: str) -> str:
    """
    Download every sidecar file for the MTBS perimeter layer from the public S3
    bucket (anonymous access) and return the path to the .shp.
    Files already on disk are skipped, so re-runs are cheap.
    """
    s3 = boto3.client(
        's3',
        region_name='us-east-1',
        config=botocore.config.Config(signature_version=botocore.UNSIGNED),
    )
    paginator = s3.get_paginator('list_objects_v2')
    keys = [
        obj['Key']
        for page in paginator.paginate(Bucket=MTBS_BUCKET, Prefix=f'{MTBS_PREFIX}{MTBS_LAYER}')
        for obj in page.get('Contents', [])
    ]
    if not keys:
        raise RuntimeError(
            f'No MTBS files found at s3://{MTBS_BUCKET}/{MTBS_PREFIX}{MTBS_LAYER}. '
            'The mirror may have moved — check https://www.mtbs.gov/direct-download'
        )

    for key in keys:
        target = os.path.join(local_path, key.split('/')[-1])
        if os.path.exists(target):
            print(f'  cached  {os.path.basename(target)}')
            continue
        print(f'  fetch   {os.path.basename(target)}')
        s3.download_file(Bucket=MTBS_BUCKET, Key=key, Filename=target)

    shp = os.path.join(local_path, f'{MTBS_LAYER}.shp')
    if not os.path.exists(shp):
        raise RuntimeError(f'Downloaded MTBS files but {shp} is missing.')
    return shp


def filter_california_wildfires(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Keep only California (Event_ID prefix 'CA') rows of type 'Wildfire'."""
    return gdf[
        (gdf['Event_ID'].str.startswith('CA')) &
        (gdf['Incid_Type'] == 'Wildfire')
    ].copy()


def load_mtbs_california(local_path: str) -> gpd.GeoDataFrame:
    """Download, read, filter to CA wildfires, and normalise CRS to EPSG:4326."""
    shp = download_mtbs_shapefile(local_path)
    print(f'Reading {shp} ...')
    gdf = gpd.read_file(shp)
    print(f'  {len(gdf):,} total MTBS records')
    return filter_california_wildfires(gdf).to_crs('EPSG:4326')


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
    import warnings
    warnings.filterwarnings('ignore', message='Geometry is in a geographic CRS')

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
