"""
Offline pre-processing script.
Run once to generate data/mtbs_ca_summary.csv.

Usage:
    python scripts/preprocess_data.py
"""
import os
import sys
import botocore
import botocore.config
import boto3
import pandas as pd
import geopandas as gpd
from datetime import datetime, timedelta

# src/utils path — added to sys.path so lazy imports inside functions work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


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
    Fetch peak temperature (C) and minimum relative humidity (%)
    for a 17-day window centred on the ignition date.
    Returns dict with keys max_temp_c and min_humidity_pct.
    """
    ig_date = datetime.utcfromtimestamp(ig_date_ms / 1000)
    start = (ig_date - timedelta(days=3)).strftime('%Y-%m-%d')
    end = (ig_date + timedelta(days=14)).strftime('%Y-%m-%d')
    from utils.openmeteo_utils import fetch_weather_data  # noqa: PLC0415
    df = fetch_weather_data(
        latitude=lat,
        longitude=lon,
        start_date=start,
        end_date=end,
        daily_variables=['temperature_2m_max', 'relative_humidity_2m_min'],
    )
    return {
        'max_temp_c': round(float(df['temperature_2m_max'].max()), 1),
        'min_humidity_pct': round(float(df['relative_humidity_2m_min'].min()), 1),
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
        ig_date_str = datetime.utcfromtimestamp(ig_ms / 1000).strftime('%Y-%m-%d')
        weather = get_event_weather(centroid.y, centroid.x, ig_ms)
        records.append({
            'event_id': row['Event_ID'],
            'event_name': row['Incid_Name'],
            'ig_date': ig_date_str,
            'year': datetime.utcfromtimestamp(ig_ms / 1000).year,
            'latitude': round(centroid.y, 6),
            'longitude': round(centroid.x, 6),
            'acres': round(float(row['BurnBndAc']), 1),
            'severity': classify_severity(float(row['BurnBndAc'])),
            'max_temp_c': weather['max_temp_c'],
            'min_humidity_pct': weather['min_humidity_pct'],
        })
    return pd.DataFrame(records)


if __name__ == '__main__':
    local_path = 'data/raw'
    os.makedirs(local_path, exist_ok=True)
    os.makedirs('data', exist_ok=True)

    print('Loading MTBS California fires from AWS S3...')
    ca_fires = load_mtbs_california(local_path)
    print(f'Found {len(ca_fires)} California wildfire events.')

    print('Fetching weather data and building summary...')
    summary = build_summary(ca_fires)

    output_path = 'data/mtbs_ca_summary.csv'
    summary.to_csv(output_path, index=False)
    print(f'Saved {len(summary)} events to {output_path}')
