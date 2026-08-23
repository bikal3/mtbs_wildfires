"""
Build the static site's data files.

Reads data/mtbs_ca_summary.csv and writes:
    site/assets/events.json   full event array (map, scatter, strip charts)
    site/assets/stats.json    precomputed aggregates (everything else)

Usage:
    python scripts/build_site.py            # requires the full dataset
    python scripts/build_site.py --sample   # build against the 50-event sample
"""
import argparse
import json
import os
import sys

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from analysis.stats import (  # noqa: E402
    compute_era_stats,
    compute_research_stats,
    compute_story_stats,
    prepare_decade_severity,
    prepare_evi_recovery_data,
    prepare_fire_season,
    prepare_severity_chart_data,
    prepare_top_fires,
)

FULL_CSV = os.path.join(PROJECT_ROOT, 'data', 'mtbs_ca_summary.csv')
SAMPLE_CSV = os.path.join(PROJECT_ROOT, 'data', 'mtbs_ca_summary_sample.csv')
OUT_DIR = os.path.join(PROJECT_ROOT, 'site', 'assets')

EVENT_FIELDS = [
    'event_id', 'event_name', 'ig_date', 'year',
    'latitude', 'longitude', 'acres', 'severity',
    'max_temp_c', 'min_humidity_pct',
]


def load_csv(use_sample: bool) -> pd.DataFrame:
    """
    Load the summary CSV. Fails loudly rather than falling back to the sample —
    silently shipping 50 events is the exact failure this migration exists to fix.
    """
    path = SAMPLE_CSV if use_sample else FULL_CSV
    if not os.path.exists(path):
        hint = '' if use_sample else ' Run: python scripts/preprocess_data.py'
        raise SystemExit(f'ERROR: {path} not found.{hint}')
    df = pd.read_csv(path)
    missing = set(EVENT_FIELDS) - set(df.columns)
    if missing:
        raise SystemExit(f'ERROR: {path} is missing columns: {sorted(missing)}')
    if df.empty:
        raise SystemExit(f'ERROR: {path} contains no rows.')
    return df


def _clean(value):
    """
    NaN -> None, numpy scalar -> Python native.

    The NaN half is load-bearing and must not be "simplified" away: json.dumps
    emits a bare `NaN` literal, which the browser's JSON.parse rejects outright.
    preprocess_data tolerates isolated weather failures, so null max_temp_c /
    min_humidity_pct values do reach here, and one of them would break every
    page on the site.
    """
    if pd.isna(value):
        return None
    if hasattr(value, 'item'):
        return value.item()
    return value


def build_events(df: pd.DataFrame) -> list:
    """The full event array. Needed in-browser by the map, scatter, and strip charts."""
    return [
        {field: _clean(row[field]) for field in EVENT_FIELDS}
        for _, row in df.iterrows()
    ]


def _records(df: pd.DataFrame) -> list:
    """DataFrame to a JSON-safe list of dicts."""
    return [{k: _clean(v) for k, v in rec.items()} for rec in df.to_dict('records')]


def build_stats(df: pd.DataFrame, is_sample: bool) -> dict:
    """Every aggregate the site needs, precomputed so the browser does no maths."""
    evi = prepare_evi_recovery_data()
    return {
        'is_sample': is_sample,
        'event_count': len(df),
        'story': compute_story_stats(df),
        'research': compute_research_stats(df),
        'acres_by_year': _records(prepare_severity_chart_data(df)),
        'eras': compute_era_stats(df),
        'decade_severity': _records(prepare_decade_severity(df).astype({'decade': str})),
        'top_fires': _records(prepare_top_fires(df)),
        'fire_season': _records(prepare_fire_season(df)),
        'evi_recovery': {
            # Hardcoded reference curves, not derived from this dataset.
            'illustrative': True,
            'months': [int(m) for m in evi['months_after_fire']],
            'low': [float(v) for v in evi['low_severity']],
            'high': [float(v) for v in evi['high_severity']],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', action='store_true',
                        help='build against the 50-event sample CSV')
    args = parser.parse_args()

    df = load_csv(args.sample)
    os.makedirs(OUT_DIR, exist_ok=True)

    for name, payload in [
        ('events.json', build_events(df)),
        ('stats.json', build_stats(df, is_sample=args.sample)),
    ]:
        path = os.path.join(OUT_DIR, name)
        with open(path, 'w', encoding='utf-8') as f:
            # allow_nan=False: fail here rather than shipping a `NaN` literal
            # that JSON.parse rejects at runtime.
            json.dump(payload, f, separators=(',', ':'), allow_nan=False)
        print(f'  wrote {path}  ({os.path.getsize(path) / 1024:.0f} KB)')

    print(f'Built site data from {len(df):,} events'
          + (' [SAMPLE]' if args.sample else ''))


if __name__ == '__main__':
    main()
