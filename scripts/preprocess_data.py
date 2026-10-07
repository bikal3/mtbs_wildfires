"""
Offline pre-processing script.
Run once to generate data/mtbs_ca_summary.csv.

Usage:
    python scripts/preprocess_data.py
"""
import os
import glob
import zipfile
import urllib.request
from datetime import timedelta

import numpy as np
import pandas as pd
import pyogrio
import openmeteo_requests
import requests_cache
from retry_requests import retry

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SUMMARY_COLUMNS = [
    'event_id', 'event_name', 'ig_date', 'year',
    'latitude', 'longitude', 'acres', 'severity',
    'max_temp_c', 'min_humidity_pct',
]

# The MTBS composite release now runs to 2025, but this project is framed as
# 1984-2022 throughout (hero copy, "38 years", and the era bins in
# analysis/stats.py, which stop at 2022). Raise this only alongside those.
MAX_YEAR = 2022

# ── Open-Meteo ────────────────────────────────────────────────────────────────
ARCHIVE_URL = 'https://archive-api.open-meteo.com/v1/archive'

# Historical weather never changes, so the cache never expires, so re-runs are free.
_cache_session = requests_cache.CachedSession(
    os.path.join(PROJECT_ROOT, '.cache', 'openmeteo'), expire_after=-1)
_retry_session = retry(_cache_session, retries=5, backoff_factor=0.4)
_openmeteo = openmeteo_requests.Client(session=_retry_session)

# ── MTBS source ───────────────────────────────────────────────────────────────
# Official USGS MTBS composite perimeter data (1984-present).
# The old Source Coop mirror (s3://cboettig/fire/USGS-MTBS/) was reorganised into
# parquet/pmtiles and no longer carries the mtbs_perims_DD shapefile.
MTBS_URL = ('https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/MTBS_Fire/data/'
            'composite_data/burned_area_extent_shapefile/mtbs_perimeter_data.zip')
MTBS_ZIP = 'mtbs_perimeter_data.zip'

# MTBS supplies the burn-boundary centre directly, so the 616 MB geometry never
# needs reading, only the 43 MB attribute table.
MTBS_COLUMNS = ['event_id', 'incid_name', 'incid_type',
                'burnbndac', 'ig_date', 'burnbndlat', 'burnbndlon']


def _find_perimeter_shapefile(local_path: str) -> str:
    """Locate the extracted perimeter .shp, preferring a name containing 'perim'."""
    found = glob.glob(os.path.join(local_path, '**', '*.shp'), recursive=True)
    if not found:
        return ''
    preferred = [f for f in found if 'perim' in os.path.basename(f).lower()]
    return (preferred or found)[0]


def download_mtbs_shapefile(local_path: str) -> str:
    """
    Download and extract the MTBS composite perimeter shapefile (~390 MB zip).
    Both the download and the extraction are skipped if already present, so
    re-runs are cheap.
    """
    existing = _find_perimeter_shapefile(local_path)
    if existing:
        print(f'  cached   {os.path.basename(existing)}')
        return existing

    zip_path = os.path.join(local_path, MTBS_ZIP)
    if not os.path.exists(zip_path):
        print(f'  fetching {MTBS_URL}')
        with urllib.request.urlopen(MTBS_URL, timeout=180) as resp:
            total = int(resp.headers.get('Content-Length', 0))
            done = 0
            with open(zip_path, 'wb') as out:
                while True:
                    chunk = resp.read(1 << 20)
                    if not chunk:
                        break
                    out.write(chunk)
                    done += len(chunk)
                    print(f'  {done / 1e6:6.0f} / {total / 1e6:.0f} MB', end='\r', flush=True)
        print('')
    else:
        print(f'  cached   {MTBS_ZIP}')

    print(f'  extracting {MTBS_ZIP}')
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(local_path)

    shp = _find_perimeter_shapefile(local_path)
    if not shp:
        raise RuntimeError(
            f'Extracted {zip_path} but found no .shp inside. '
            'Check https://www.mtbs.gov/direct-download for a layout change.'
        )
    return shp


def filter_california_wildfires(df: pd.DataFrame, max_year: int = MAX_YEAR) -> pd.DataFrame:
    """
    Keep California ('CA' event_id prefix) rows of type 'Wildfire' up to max_year,
    with an `ig_dt` datetime column added, ordered oldest first.
    """
    out = df[
        (df['event_id'].str.startswith('CA')) &
        (df['incid_type'] == 'Wildfire')
    ].copy()
    out['ig_dt'] = pd.to_datetime(out['ig_date'])
    out = out[out['ig_dt'].dt.year <= max_year]
    return out.sort_values('ig_dt').reset_index(drop=True)


def load_mtbs_california(local_path: str) -> pd.DataFrame:
    """Download, read the attribute table only, and filter to CA wildfires."""
    shp = download_mtbs_shapefile(local_path)
    print(f'Reading {os.path.basename(shp)} (attributes only) ...')
    df = pyogrio.read_dataframe(shp, read_geometry=False, columns=MTBS_COLUMNS)
    print(f'  {len(df):,} total MTBS records')
    return filter_california_wildfires(df)


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


def get_event_weather(lat: float, lon: float, ig_date) -> dict:
    """
    Peak temperature (C) and minimum relative humidity (%) over a window running
    from 3 days before to 14 days after ignition (18 days inclusive).

    Raises on failure. Callers decide what an individual failure means; see
    build_summary, which aborts only if the failure *rate* is systemic.
    """
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


def build_summary(ca_fires: pd.DataFrame, max_failure_pct: float = 5.0) -> pd.DataFrame:
    """
    Build the summary DataFrame from the filtered California MTBS frame.
    One weather API call per row, slow on the full dataset.

    Individual failures are recorded as null and reported. If more than
    max_failure_pct of events fail, the run aborts: that means something is
    systemically wrong (wrong endpoint, rate limit, network down) rather than
    a handful of flaky requests.
    """
    records, failures = [], []
    total = len(ca_fires)

    for i, row in enumerate(ca_fires.itertuples(index=False), start=1):
        lat, lon = float(row.burnbndlat), float(row.burnbndlon)
        acres = float(row.burnbndac)

        try:
            weather = get_event_weather(lat, lon, row.ig_dt)
        except Exception as exc:
            failures.append((row.event_id, str(exc)))
            weather = {'max_temp_c': None, 'min_humidity_pct': None}

        records.append({
            'event_id': row.event_id,
            'event_name': row.incid_name,
            'ig_date': row.ig_dt.strftime('%Y-%m-%d'),
            'year': row.ig_dt.year,
            'latitude': round(lat, 6),
            'longitude': round(lon, 6),
            'acres': round(acres, 1),
            'severity': classify_severity(acres),
            'max_temp_c': weather['max_temp_c'],
            'min_humidity_pct': weather['min_humidity_pct'],
        })

        if i % 50 == 0 or i == total:
            print(f'  {i}/{total} events · {len(failures)} weather failures')

    if failures:
        pct = len(failures) / total * 100
        print('')
        print(f'{len(failures)} of {total} weather fetches failed ({pct:.1f}%)')
        for event_id, msg in failures[:5]:
            print(f'  {event_id}: {msg}')
        if pct > max_failure_pct:
            raise RuntimeError(
                f'Weather failure rate {pct:.1f}% exceeds {max_failure_pct}%, aborting. '
                'This indicates a systemic problem, not transient errors.'
            )

    return pd.DataFrame(records, columns=SUMMARY_COLUMNS)


if __name__ == '__main__':
    local_path = os.path.join(PROJECT_ROOT, 'data', 'raw')
    os.makedirs(local_path, exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT, 'data'), exist_ok=True)

    print('Loading MTBS California fires...')
    ca_fires = load_mtbs_california(local_path)
    print(f'Found {len(ca_fires):,} California wildfire events (through {MAX_YEAR}).')

    print('Fetching weather data and building summary...')
    summary = build_summary(ca_fires)

    output_path = os.path.join(PROJECT_ROOT, 'data', 'mtbs_ca_summary.csv')
    summary.to_csv(output_path, index=False)
    print(f'Saved {len(summary):,} events to {output_path}')
