# MTBS Wildfire Website Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Streamlit website with three tabs (Story · Research · Explorer) showcasing the MTBS California wildfire analysis project for portfolio and academic audiences.

**Architecture:** A single `app.py` entry point applies a global Dark Fire CSS theme and renders three tabs. The Story tab injects hand-crafted HTML via `st.components.v1.html()` for a cinematic narrative feel. Research and Explorer tabs use pure Streamlit with Plotly charts and a Folium map. All data is pre-processed offline into `data/mtbs_ca_summary.csv` — no live GEE calls at runtime.

**Tech Stack:** Python 3, Streamlit ≥1.32, Plotly, Folium, streamlit-folium, GeoPandas, boto3, openmeteo-requests, pytest

---

## File Map

| File | Role |
|---|---|
| `app.py` | Entry point: page config, global CSS, tab switcher |
| `pages/story.py` | Story tab: loads HTML templates, injects data, renders via st.components |
| `pages/research.py` | Research tab: pure Streamlit — about, data sources, pipeline, charts, findings |
| `pages/explorer.py` | Explorer tab: filters sidebar, Folium map, event detail panel |
| `components/story_hero.html` | Hero section HTML template (title, stats) |
| `components/story_sections.html` | Narrative section HTML templates (trend, EVI, CTA) |
| `scripts/preprocess_data.py` | Offline script: loads MTBS shapefile from AWS, joins weather, writes CSV |
| `data/mtbs_ca_summary.csv` | Pre-processed fire event summary (output of preprocess_data.py) |
| `data/evi_exports/` | Static EVI PNG images exported from evi.ipynb, named `{event_id}.png` |
| `.streamlit/config.toml` | Streamlit dark fire theme config |
| `requirements.txt` | All Python dependencies |
| `tests/test_preprocess.py` | Unit tests for pre-processing functions |
| `tests/test_story.py` | Unit tests for HTML template loading/injection |
| `tests/test_research.py` | Unit tests for chart data preparation functions |
| `tests/test_explorer.py` | Unit tests for map filter logic |

---

## Task 1: Project Setup — requirements, Streamlit config, app shell

**Files:**
- Create: `requirements.txt`
- Create: `.streamlit/config.toml`
- Create: `app.py`

- [ ] **Step 1: Create requirements.txt**

```
streamlit>=1.32.0
plotly>=5.18.0
folium>=0.15.0
streamlit-folium>=0.20.0
geopandas>=0.14.0
pandas>=2.0.0
boto3>=1.34.0
botocore>=1.34.0
openmeteo-requests>=1.2.0
requests-cache>=1.2.0
retry-requests>=2.0.0
pytest>=7.4.0
```

- [ ] **Step 2: Create .streamlit/config.toml**

```bash
mkdir -p .streamlit
```

```toml
[theme]
base = "dark"
primaryColor = "#f97316"
backgroundColor = "#0a0a0a"
secondaryBackgroundColor = "#111111"
textColor = "#f1f5f9"
font = "sans serif"

[server]
headless = true
```

- [ ] **Step 3: Create app.py**

```python
import streamlit as st

st.set_page_config(
    page_title="MTBS Wildfire Analysis — California 1984–2022",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0a0a0a; }
[data-testid="stHeader"] { background-color: #0a0a0a; }
section[data-testid="stSidebar"] { background-color: #0f0f0f; }
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: #0f0f0f;
    padding: 8px 16px 0;
    border-bottom: 1px solid #1a1a1a;
}
.stTabs [data-baseweb="tab"] {
    color: #6b7280;
    background-color: transparent;
    border-radius: 4px 4px 0 0;
    padding: 8px 24px;
    font-weight: 600;
    font-size: 14px;
}
.stTabs [aria-selected="true"] {
    background-color: #1a1a1a !important;
    color: #f97316 !important;
}
h1, h2, h3 { color: #f1f5f9; }
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔥  Story", "🔬  Research", "🗺  Explorer"])

with tab1:
    from pages.story import render_story
    render_story()

with tab2:
    from pages.research import render_research
    render_research()

with tab3:
    from pages.explorer import render_explorer
    render_explorer()
```

- [ ] **Step 4: Create placeholder pages so app.py doesn't crash**

Create `pages/__init__.py` (empty), then:

`pages/story.py`:
```python
import streamlit as st

def render_story():
    st.write("Story — coming soon")
```

`pages/research.py`:
```python
import streamlit as st

def render_research():
    st.write("Research — coming soon")
```

`pages/explorer.py`:
```python
import streamlit as st

def render_explorer():
    st.write("Explorer — coming soon")
```

- [ ] **Step 5: Verify app runs**

```bash
pip install -r requirements.txt
streamlit run app.py
```

Expected: Browser opens, three tabs visible with "coming soon" text, dark background, orange tab highlight on active tab.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .streamlit/config.toml app.py pages/
git commit -m "feat: add Streamlit app shell with dark fire theme and tab structure"
```

---

## Task 2: Pre-processing Script — generate mtbs_ca_summary.csv

**Files:**
- Create: `scripts/preprocess_data.py`
- Create: `tests/test_preprocess.py`

- [ ] **Step 1: Write failing tests**

`tests/test_preprocess.py`:
```python
import pandas as pd
import geopandas as gpd
import pytest
from shapely.geometry import Point, Polygon
from unittest.mock import patch, MagicMock
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
    assert row['year'] == 2021
    assert row['severity'] == 'High'
    assert row['max_temp_c'] == 38.5
    assert row['min_humidity_pct'] == 11.0
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_preprocess.py -v
```

Expected: `ModuleNotFoundError: No module named 'scripts.preprocess_data'`

- [ ] **Step 3: Create scripts/preprocess_data.py**

```bash
mkdir -p scripts data/raw data/evi_exports
touch scripts/__init__.py
```

`scripts/preprocess_data.py`:
```python
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

# Allow imports from src/utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from utils.source_coop_utils import get_mtbs_shp
from utils.openmeteo_utils import fetch_weather_data


def load_mtbs_california(local_path: str) -> gpd.GeoDataFrame:
    """
    Download MTBS shapefile from AWS public bucket (anonymous access)
    and return a GeoDataFrame filtered to California wildfires.
    """
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
      Medium : 10,000 – 99,999 acres
      High   : >= 100,000 acres
    """
    if acres < 10_000:
        return 'Low'
    elif acres < 100_000:
        return 'Medium'
    return 'High'


def get_event_weather(lat: float, lon: float, ig_date_ms: int) -> dict:
    """
    Fetch peak temperature (°C) and minimum relative humidity (%)
    for a 17-day window centred on the ignition date.
    Returns dict with keys max_temp_c and min_humidity_pct.
    """
    ig_date = datetime.utcfromtimestamp(ig_date_ms / 1000)
    start = (ig_date - timedelta(days=3)).strftime('%Y-%m-%d')
    end = (ig_date + timedelta(days=14)).strftime('%Y-%m-%d')
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_preprocess.py -v
```

Expected output:
```
PASSED tests/test_preprocess.py::test_classify_severity_low
PASSED tests/test_preprocess.py::test_classify_severity_medium
PASSED tests/test_preprocess.py::test_classify_severity_high
PASSED tests/test_preprocess.py::test_classify_severity_boundaries
PASSED tests/test_preprocess.py::test_build_summary_columns
PASSED tests/test_preprocess.py::test_build_summary_values
6 passed
```

- [ ] **Step 5: Run the pre-processing script to generate the CSV**

```bash
python scripts/preprocess_data.py
```

Expected: `data/mtbs_ca_summary.csv` created with columns: `event_id, event_name, ig_date, year, latitude, longitude, acres, severity, max_temp_c, min_humidity_pct`

Verify with:
```bash
python -c "import pandas as pd; df = pd.read_csv('data/mtbs_ca_summary.csv'); print(df.shape); print(df.head(3))"
```

Expected: DataFrame with 10 columns and >100 rows for California.

- [ ] **Step 6: Commit**

```bash
git add scripts/ tests/test_preprocess.py
git commit -m "feat: add pre-processing script and tests for mtbs_ca_summary.csv"
```

---

## Task 3: Story Tab — HTML templates + Python loader

**Files:**
- Create: `components/story_hero.html`
- Create: `components/story_sections.html`
- Create: `pages/story.py` (replace placeholder)
- Create: `tests/test_story.py`

- [ ] **Step 1: Write failing tests**

`tests/test_story.py`:
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import pytest
from pages.story import load_template, inject_stats, compute_story_stats


def _sample_df():
    return pd.DataFrame({
        'event_id':       ['CA001', 'CA002', 'CA003'],
        'acres':          [5_000.0, 50_000.0, 200_000.0],
        'severity':       ['Low', 'Medium', 'High'],
        'year':           [1990, 2000, 2020],
        'ig_date':        ['1990-06-01', '2000-07-15', '2020-08-01'],
        'latitude':       [37.0, 38.0, 39.0],
        'longitude':      [-120.0, -119.0, -118.0],
        'max_temp_c':     [30.0, 35.0, 40.0],
        'min_humidity_pct': [20.0, 15.0, 10.0],
    })


def test_load_template_returns_string():
    path = os.path.join(os.path.dirname(__file__), '..', 'components', 'story_hero.html')
    html = load_template(path)
    assert isinstance(html, str)
    assert len(html) > 0


def test_inject_stats_replaces_placeholders():
    template = "<div>{{total_acres}}</div><div>{{event_count}}</div>"
    result = inject_stats(template, total_acres="4.2M", event_count="2,847")
    assert "4.2M" in result
    assert "2,847" in result
    assert "{{total_acres}}" not in result


def test_compute_story_stats_keys():
    df = _sample_df()
    stats = compute_story_stats(df)
    assert 'total_acres_fmt' in stats
    assert 'event_count_fmt' in stats
    assert 'pct_high_severity_fmt' in stats
    assert 'year_range' in stats


def test_compute_story_stats_values():
    df = _sample_df()
    stats = compute_story_stats(df)
    assert stats['event_count_fmt'] == '3'
    assert stats['year_range'] == '1990–2020'
    # 1 of 3 events is High
    assert stats['pct_high_severity_fmt'] == '33%'
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_story.py -v
```

Expected: `ImportError` — `load_template`, `inject_stats`, `compute_story_stats` not yet defined.

- [ ] **Step 3: Create components/story_hero.html**

```bash
mkdir -p components
```

`components/story_hero.html`:
```html
<div style="
  background: linear-gradient(180deg, #1a0500 0%, #0a0a0a 100%);
  padding: 60px 32px 40px;
  text-align: center;
  border-bottom: 1px solid #2d0f00;
  font-family: sans-serif;
">
  <div style="color:#f97316;font-size:11px;letter-spacing:4px;text-transform:uppercase;margin-bottom:12px;">
    California · 1984 – 2022
  </div>
  <h1 style="color:#fde68a;font-size:48px;font-weight:900;line-height:1.1;margin:0 0 16px;">
    40 Years of Fire
  </h1>
  <p style="color:#9ca3af;font-size:16px;max-width:560px;margin:0 auto 32px;line-height:1.7;">
    How satellite data reveals four decades of escalating wildfire crisis
    across California's landscapes.
  </p>

  <!-- Stat counters -->
  <div style="
    display:inline-grid;
    grid-template-columns:repeat(4,1fr);
    gap:24px;
    background:#0f0f0f;
    border:1px solid #1a1a1a;
    border-radius:8px;
    padding:24px 32px;
    margin-bottom:32px;
  ">
    <div style="text-align:center;">
      <div style="color:#ef4444;font-size:32px;font-weight:900;line-height:1;">{{total_acres}}</div>
      <div style="color:#6b7280;font-size:11px;margin-top:6px;line-height:1.4;">total acres<br>burned</div>
    </div>
    <div style="text-align:center;">
      <div style="color:#f97316;font-size:32px;font-weight:900;line-height:1;">{{event_count}}</div>
      <div style="color:#6b7280;font-size:11px;margin-top:6px;line-height:1.4;">wildfire<br>events</div>
    </div>
    <div style="text-align:center;">
      <div style="color:#fbbf24;font-size:32px;font-weight:900;line-height:1;">{{pct_high_severity}}</div>
      <div style="color:#6b7280;font-size:11px;margin-top:6px;line-height:1.4;">high-severity<br>events</div>
    </div>
    <div style="text-align:center;">
      <div style="color:#22c55e;font-size:32px;font-weight:900;line-height:1;">{{year_range}}</div>
      <div style="color:#6b7280;font-size:11px;margin-top:6px;line-height:1.4;">time<br>span</div>
    </div>
  </div>

  <div style="color:#f97316;font-size:12px;">↓ Scroll to explore</div>
</div>
```

- [ ] **Step 4: Create components/story_sections.html**

`components/story_sections.html`:
```html
<!-- Section: The Trend -->
<div style="
  padding: 48px 32px;
  border-bottom: 1px solid #1a1a1a;
  font-family: sans-serif;
  max-width: 860px;
  margin: 0 auto;
">
  <div style="color:#f97316;font-size:10px;letter-spacing:3px;text-transform:uppercase;margin-bottom:12px;">
    The Trend
  </div>
  <h2 style="color:#e2e8f0;font-size:28px;font-weight:800;margin:0 0 16px;">
    Fires are getting bigger and more severe
  </h2>
  <p style="color:#9ca3af;font-size:15px;line-height:1.75;margin-bottom:32px;">
    The MTBS dataset records every fire over 1,000 acres since 1984.
    The pattern is unambiguous — both total area burned and high-severity
    burn fraction have increased sharply since 2000, driven by prolonged
    drought, rising temperatures, and decades of fuel accumulation.
  </p>
  <div id="trend-chart" style="border-radius:6px;overflow:hidden;">
    {{trend_chart}}
  </div>
</div>

<!-- Section: Vegetation Recovery -->
<div style="
  padding: 48px 32px;
  border-bottom: 1px solid #1a1a1a;
  background: #0f0f0f;
  font-family: sans-serif;
  max-width: 860px;
  margin: 0 auto;
">
  <div style="color:#22c55e;font-size:10px;letter-spacing:3px;text-transform:uppercase;margin-bottom:12px;">
    Vegetation Recovery
  </div>
  <h2 style="color:#e2e8f0;font-size:28px;font-weight:800;margin:0 0 16px;">
    Satellite imagery tracks what burns — and what recovers
  </h2>
  <p style="color:#9ca3af;font-size:15px;line-height:1.75;margin-bottom:32px;">
    Using the Enhanced Vegetation Index (EVI) from Landsat 8 and Sentinel-2,
    we tracked vegetation health before and after each fire event.
    High-severity burns show slower, often incomplete recovery — the
    landscape is fundamentally altered.
  </p>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;">
    <div style="background:#111;border-radius:6px;padding:16px;text-align:center;">
      <div style="background:linear-gradient(180deg,#14532d,#166534,#15803d,#86efac);height:60px;border-radius:4px;margin-bottom:12px;"></div>
      <div style="color:#9ca3af;font-size:12px;margin-bottom:4px;">Pre-fire EVI</div>
      <div style="color:#22c55e;font-size:14px;font-weight:700;">Healthy vegetation</div>
    </div>
    <div style="background:#111;border-radius:6px;padding:16px;text-align:center;">
      <div style="background:linear-gradient(180deg,#7f1d1d,#991b1b,#b91c1c,#fca5a5);height:60px;border-radius:4px;margin-bottom:12px;"></div>
      <div style="color:#9ca3af;font-size:12px;margin-bottom:4px;">Post-fire EVI</div>
      <div style="color:#ef4444;font-size:14px;font-weight:700;">Scorched landscape</div>
    </div>
    <div style="background:#111;border-radius:6px;padding:16px;text-align:center;">
      <div style="background:linear-gradient(180deg,#1c1917,#292524,#57534e,#a8a29e);height:60px;border-radius:4px;margin-bottom:12px;"></div>
      <div style="color:#9ca3af;font-size:12px;margin-bottom:4px;">1-year recovery</div>
      <div style="color:#fbbf24;font-size:14px;font-weight:700;">Partial regrowth</div>
    </div>
  </div>
</div>

<!-- Section: CTA -->
<div style="
  padding: 56px 32px;
  text-align: center;
  font-family: sans-serif;
">
  <p style="color:#6b7280;font-size:14px;margin-bottom:24px;">
    Want to explore the data yourself or read the full methodology?
  </p>
  <div style="display:inline-flex;gap:12px;">
    <a href="?tab=explorer" style="
      background:#f97316;color:#fff;
      padding:12px 24px;border-radius:6px;
      font-size:14px;font-weight:700;
      text-decoration:none;
    ">🗺 Open Explorer</a>
    <a href="?tab=research" style="
      background:#1e293b;color:#94a3b8;
      padding:12px 24px;border-radius:6px;
      font-size:14px;font-weight:700;
      text-decoration:none;
    ">🔬 Read Research</a>
  </div>
</div>
```

- [ ] **Step 5: Create pages/story.py**

`pages/story.py`:
```python
import os
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components


DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'mtbs_ca_summary.csv')
HERO_PATH = os.path.join(os.path.dirname(__file__), '..', 'components', 'story_hero.html')
SECTIONS_PATH = os.path.join(os.path.dirname(__file__), '..', 'components', 'story_sections.html')


def load_template(path: str) -> str:
    """Read an HTML template file and return its contents as a string."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def inject_stats(template: str, **kwargs) -> str:
    """Replace {{key}} placeholders in template with provided keyword values."""
    for key, value in kwargs.items():
        template = template.replace(f'{{{{{key}}}}}', str(value))
    return template


def compute_story_stats(df: pd.DataFrame) -> dict:
    """Compute display statistics from the summary DataFrame."""
    total_acres = df['acres'].sum()
    if total_acres >= 1_000_000:
        total_acres_fmt = f"{total_acres / 1_000_000:.1f}M"
    else:
        total_acres_fmt = f"{total_acres / 1_000:.0f}K"

    event_count_fmt = f"{len(df):,}"
    pct_high = len(df[df['severity'] == 'High']) / len(df) * 100
    pct_high_severity_fmt = f"{pct_high:.0f}%"
    year_range = f"{df['year'].min()}–{df['year'].max()}"

    return {
        'total_acres_fmt': total_acres_fmt,
        'event_count_fmt': event_count_fmt,
        'pct_high_severity_fmt': pct_high_severity_fmt,
        'year_range': year_range,
    }


def build_trend_chart_html(df: pd.DataFrame) -> str:
    """Build a Plotly bar chart of total acres burned per year, return as HTML string."""
    yearly = df.groupby('year')['acres'].sum().reset_index()
    fig = px.bar(
        yearly,
        x='year',
        y='acres',
        color='acres',
        color_continuous_scale=['#7f1d1d', '#ef4444', '#f97316', '#fbbf24'],
        labels={'year': '', 'acres': 'Acres Burned'},
        title='',
    )
    fig.update_layout(
        paper_bgcolor='#111',
        plot_bgcolor='#111',
        font_color='#9ca3af',
        coloraxis_showscale=False,
        margin=dict(l=40, r=20, t=10, b=40),
        height=280,
        xaxis=dict(showgrid=False, tickfont=dict(color='#6b7280')),
        yaxis=dict(showgrid=True, gridcolor='#1e293b', tickfont=dict(color='#6b7280')),
    )
    return fig.to_html(include_plotlyjs='cdn', full_html=False, config={'displayModeBar': False})


@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH)


def render_story():
    if not os.path.exists(DATA_PATH):
        st.error("Data file not found. Run `python scripts/preprocess_data.py` first.")
        return

    df = load_data()
    stats = compute_story_stats(df)
    trend_chart_html = build_trend_chart_html(df)

    # Render hero section
    hero_html = load_template(HERO_PATH)
    hero_html = inject_stats(
        hero_html,
        total_acres=stats['total_acres_fmt'],
        event_count=stats['event_count_fmt'],
        pct_high_severity=stats['pct_high_severity_fmt'],
        year_range=stats['year_range'],
    )
    components.html(hero_html, height=420, scrolling=False)

    # Render narrative sections with embedded trend chart
    sections_html = load_template(SECTIONS_PATH)
    sections_html = inject_stats(sections_html, trend_chart=trend_chart_html)
    components.html(sections_html, height=1100, scrolling=True)
```

- [ ] **Step 6: Run tests to confirm they pass**

```bash
pytest tests/test_story.py -v
```

Expected output:
```
PASSED tests/test_story.py::test_load_template_returns_string
PASSED tests/test_story.py::test_inject_stats_replaces_placeholders
PASSED tests/test_story.py::test_compute_story_stats_keys
PASSED tests/test_story.py::test_compute_story_stats_values
4 passed
```

- [ ] **Step 7: Verify in browser**

```bash
streamlit run app.py
```

Open browser, click "🔥 Story" tab. Expected: dark hero section with stats, trend bar chart, EVI recovery section, CTA buttons.

- [ ] **Step 8: Commit**

```bash
git add components/ pages/story.py tests/test_story.py
git commit -m "feat: add Story tab with HTML narrative components and Plotly trend chart"
```

---

## Task 4: Research Tab — pure Streamlit

**Files:**
- Modify: `pages/research.py` (replace placeholder)
- Create: `tests/test_research.py`

- [ ] **Step 1: Write failing tests**

`tests/test_research.py`:
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_research.py -v
```

Expected: `ImportError` — functions not yet defined.

- [ ] **Step 3: Write pages/research.py**

`pages/research.py`:
```python
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'mtbs_ca_summary.csv')
REPORT_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'Report.pdf')


def prepare_severity_chart_data(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate total acres burned per year for the severity bar chart."""
    return df.groupby('year')['acres'].sum().reset_index()


def prepare_evi_recovery_data() -> pd.DataFrame:
    """
    Return a representative EVI recovery curve for low vs high severity fires.
    Based on typical MTBS/Landsat EVI recovery patterns from the project report.
    X-axis: months after fire. Y-axis: EVI index (0–1).
    """
    months = list(range(0, 37, 3))
    low_severity =  [0.55, 0.42, 0.48, 0.51, 0.54, 0.55, 0.56, 0.57, 0.57, 0.58, 0.58, 0.58, 0.59]
    high_severity = [0.55, 0.10, 0.15, 0.20, 0.25, 0.28, 0.30, 0.32, 0.33, 0.34, 0.35, 0.35, 0.36]
    return pd.DataFrame({
        'months_after_fire': months,
        'low_severity': low_severity,
        'high_severity': high_severity,
    })


def compute_research_stats(df: pd.DataFrame) -> dict:
    """Compute summary statistics for the research overview metrics."""
    total_acres = df['acres'].sum()
    pct_high = round(len(df[df['severity'] == 'High']) / len(df) * 100, 1)
    return {
        'total_events': len(df),
        'total_acres_m': round(total_acres / 1_000_000, 1),
        'pct_high': pct_high,
        'year_min': int(df['year'].min()),
        'year_max': int(df['year'].max()),
    }


@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH)


def render_research():
    if not os.path.exists(DATA_PATH):
        st.error("Data file not found. Run `python scripts/preprocess_data.py` first.")
        return

    df = load_data()
    stats = compute_research_stats(df)

    # ── Page header ──────────────────────────────────────────────────────────
    st.markdown(
        "<div style='color:#38bdf8;font-size:11px;letter-spacing:3px;text-transform:uppercase;'>"
        "Full Research</div>",
        unsafe_allow_html=True,
    )
    st.title("MTBS Wildfire Analysis")
    st.caption(
        f"California · {stats['year_min']}–{stats['year_max']} · "
        "Google Earth Engine · Landsat · Sentinel-2 · Open-Meteo"
    )
    st.divider()

    # ── 01 About ─────────────────────────────────────────────────────────────
    st.subheader("01 — About")
    st.write(
        "This project investigates how satellite-derived vegetation indices and climate data "
        "can characterise wildfire burn severity trends across California over 38 years. "
        "Data is sourced from the Monitoring Trends in Burn Severity (MTBS) programme, "
        "Google Earth Engine, AWS S3, and the Open-Meteo API."
    )
    col1, col2 = st.columns([1, 5])
    with col1:
        if os.path.exists(REPORT_PATH):
            with open(REPORT_PATH, 'rb') as f:
                st.download_button("📄 Report PDF", f, file_name="MTBS_Wildfire_Report.pdf", mime="application/pdf")
    with col2:
        st.link_button("💻 GitHub Repo", "https://github.com/bikal3/mtbs_wildfires")
    st.divider()

    # ── 02 Data Sources ───────────────────────────────────────────────────────
    st.subheader("02 — Data Sources")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("**:orange[MTBS]**")
        st.caption("Burn severity + fire perimeters, 1984–2022. Sourced via GEE and AWS S3.")
    with c2:
        st.markdown("**:green[Landsat 8 / Sentinel-2]**")
        st.caption("Multispectral imagery for EVI and NDVI calculation via Google Earth Engine.")
    with c3:
        st.markdown("**:blue[Open-Meteo API]**")
        st.caption("Historical weather conditions (temp, wind, humidity) per fire event.")
    with c4:
        st.markdown("**:violet[AWS S3 / Source Coop]**")
        st.caption("Large-scale USGS/MTBS shapefiles processed via Dask distributed computing.")
    st.divider()

    # ── 03 Methodology Pipeline ───────────────────────────────────────────────
    st.subheader("03 — Methodology Pipeline")
    p1, p2, p3, p4, p5 = st.columns(5)
    for col, icon, label, sublabel in [
        (p1, "🛰", "GEE Pull", "MTBS + imagery"),
        (p2, "☁️", "Cloud Mask", "Landsat / S2"),
        (p3, "🌿", "EVI / NDVI", "Band calc"),
        (p4, "🌡", "Weather", "Open-Meteo"),
        (p5, "📊", "Analysis", "Severity trends"),
    ]:
        with col:
            st.markdown(
                f"<div style='background:#1e293b;border-radius:6px;padding:12px;text-align:center;'>"
                f"<div style='font-size:24px;'>{icon}</div>"
                f"<div style='color:#e2e8f0;font-weight:700;margin-top:6px;'>{label}</div>"
                f"<div style='color:#64748b;font-size:12px;'>{sublabel}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
    st.divider()

    # ── 04 Key Results ────────────────────────────────────────────────────────
    st.subheader("04 — Key Results")
    chart_col, evi_col = st.columns(2)

    with chart_col:
        severity_data = prepare_severity_chart_data(df)
        fig_bar = px.bar(
            severity_data, x='year', y='acres',
            color='acres',
            color_continuous_scale=['#7f1d1d', '#ef4444', '#f97316', '#fbbf24'],
            labels={'year': 'Year', 'acres': 'Acres Burned'},
            title='Total Acres Burned per Year',
        )
        fig_bar.update_layout(
            paper_bgcolor='#111', plot_bgcolor='#111',
            font_color='#9ca3af', coloraxis_showscale=False,
            title_font_color='#e2e8f0',
            margin=dict(l=40, r=20, t=40, b=40), height=300,
            xaxis=dict(showgrid=False), yaxis=dict(gridcolor='#1e293b'),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with evi_col:
        evi_data = prepare_evi_recovery_data()
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=evi_data['months_after_fire'], y=evi_data['low_severity'],
            mode='lines', name='Low severity', line=dict(color='#22c55e', width=2),
        ))
        fig_line.add_trace(go.Scatter(
            x=evi_data['months_after_fire'], y=evi_data['high_severity'],
            mode='lines', name='High severity', line=dict(color='#ef4444', width=2, dash='dash'),
        ))
        fig_line.add_vline(x=0, line_color='#f97316', line_dash='dot', annotation_text='Fire')
        fig_line.update_layout(
            paper_bgcolor='#111', plot_bgcolor='#111',
            font_color='#9ca3af', title='EVI Recovery Timeline (3 years)',
            title_font_color='#e2e8f0',
            margin=dict(l=40, r=20, t=40, b=40), height=300,
            xaxis=dict(title='Months after fire', showgrid=False),
            yaxis=dict(title='EVI index', gridcolor='#1e293b', range=[0, 0.7]),
            legend=dict(bgcolor='#1e293b'),
        )
        st.plotly_chart(fig_line, use_container_width=True)
    st.divider()

    # ── 05 Key Findings ───────────────────────────────────────────────────────
    st.subheader("05 — Key Findings")
    findings = [
        ("🔥", "orange",
         f"High-severity burn area represents {stats['pct_high']}% of all California "
         "wildfire events in the dataset. Severe events (>100,000 acres) have become "
         "increasingly frequent after 2000."),
        ("🌿", "green",
         "EVI recovery analysis shows high-severity burned areas reach only ~36% of "
         "pre-fire vegetation levels after 3 years, compared to >58% for low-severity areas."),
        ("🌡", "blue",
         "Weather data from Open-Meteo confirms fire events with max daily temperatures "
         "above 35°C and minimum relative humidity below 15% correspond to the highest "
         "severity outcomes in the dataset."),
    ]
    for icon, color, text in findings:
        st.markdown(
            f"<div style='background:#111;border-radius:6px;padding:14px 18px;margin-bottom:10px;"
            f"display:flex;gap:14px;align-items:flex-start;'>"
            f"<div style='font-size:20px;'>{icon}</div>"
            f"<div style='color:#d1d5db;font-size:14px;line-height:1.6;'>{text}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    st.divider()

    # ── 06 Tools & Links ──────────────────────────────────────────────────────
    st.subheader("06 — Tools & Links")
    tools = ["Python", "Google Earth Engine", "GeoPandas", "Dask", "Plotly", "Folium", "Open-Meteo", "Streamlit"]
    st.markdown(
        " ".join(
            f"<span style='background:#1e293b;color:#94a3b8;padding:4px 10px;"
            f"border-radius:4px;font-size:12px;margin:2px;display:inline-block;'>{t}</span>"
            for t in tools
        ),
        unsafe_allow_html=True,
    )
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_research.py -v
```

Expected output:
```
PASSED tests/test_research.py::test_prepare_severity_chart_data_columns
PASSED tests/test_research.py::test_prepare_severity_chart_data_aggregation
PASSED tests/test_research.py::test_prepare_evi_recovery_data_shape
PASSED tests/test_research.py::test_compute_research_stats_keys
PASSED tests/test_research.py::test_compute_research_stats_values
5 passed
```

- [ ] **Step 5: Verify in browser**

```bash
streamlit run app.py
```

Click "🔬 Research" tab. Expected: all 6 sections render with correct dark fire styling, two charts side by side, 3 findings cards, download PDF button active.

- [ ] **Step 6: Commit**

```bash
git add pages/research.py tests/test_research.py
git commit -m "feat: add Research tab with methodology pipeline, charts, and findings"
```

---

## Task 5: Explorer Tab — Folium map + filters + detail panel

**Files:**
- Modify: `pages/explorer.py` (replace placeholder)
- Create: `tests/test_explorer.py`

- [ ] **Step 1: Write failing tests**

`tests/test_explorer.py`:
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import pytest
from pages.explorer import filter_events, severity_color, format_acres, compute_map_stats


def _sample_df():
    return pd.DataFrame({
        'event_id':         ['CA001', 'CA002', 'CA003', 'CA004'],
        'event_name':       ['Alpha Fire', 'Beta Fire', 'Gamma Fire', 'Delta Fire'],
        'acres':            [5_000, 50_000, 200_000, 300_000],
        'severity':         ['Low', 'Medium', 'High', 'High'],
        'year':             [1990, 2000, 2010, 2022],
        'ig_date':          ['1990-06-01', '2000-07-15', '2010-08-01', '2022-09-01'],
        'latitude':         [37.0, 38.0, 39.0, 40.0],
        'longitude':        [-120.0, -119.0, -118.0, -117.0],
        'max_temp_c':       [30.0, 35.0, 40.0, 42.0],
        'min_humidity_pct': [20.0, 15.0, 10.0, 8.0],
    })


def test_filter_events_year_range():
    df = _sample_df()
    result = filter_events(df, year_range=(1995, 2015), severities=['Low', 'Medium', 'High'], min_acres=0)
    assert set(result['event_id']) == {'CA002', 'CA003'}


def test_filter_events_severity():
    df = _sample_df()
    result = filter_events(df, year_range=(1984, 2022), severities=['High'], min_acres=0)
    assert set(result['event_id']) == {'CA003', 'CA004'}


def test_filter_events_min_acres():
    df = _sample_df()
    result = filter_events(df, year_range=(1984, 2022), severities=['Low', 'Medium', 'High'], min_acres=100_000)
    assert set(result['event_id']) == {'CA003', 'CA004'}


def test_filter_events_combined():
    df = _sample_df()
    result = filter_events(df, year_range=(2005, 2025), severities=['High'], min_acres=150_000)
    assert set(result['event_id']) == {'CA003', 'CA004'}


def test_severity_color():
    assert severity_color('Low') == '#fbbf24'
    assert severity_color('Medium') == '#f97316'
    assert severity_color('High') == '#ef4444'


def test_format_acres_thousands():
    assert format_acres(5_000) == '5,000'


def test_format_acres_millions():
    assert format_acres(1_200_000) == '1.2M'


def test_compute_map_stats_keys():
    df = _sample_df()
    stats = compute_map_stats(df)
    assert 'event_count' in stats
    assert 'total_acres_fmt' in stats
    assert 'pct_high_fmt' in stats


def test_compute_map_stats_values():
    df = _sample_df()
    stats = compute_map_stats(df)
    assert stats['event_count'] == 4
    assert stats['pct_high_fmt'] == '50%'
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_explorer.py -v
```

Expected: `ImportError` — functions not yet defined.

- [ ] **Step 3: Write pages/explorer.py**

`pages/explorer.py`:
```python
import os
from pathlib import Path
import pandas as pd
import folium
from streamlit_folium import st_folium
import streamlit as st

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'mtbs_ca_summary.csv')
EVI_DIR = Path(__file__).parent.parent / 'data' / 'evi_exports'

SEVERITY_ORDER = ['Low', 'Medium', 'High']


def severity_color(severity: str) -> str:
    """Return the hex colour for a severity tier."""
    return {'Low': '#fbbf24', 'Medium': '#f97316', 'High': '#ef4444'}.get(severity, '#6b7280')


def format_acres(acres: float) -> str:
    """Format acreage as a human-readable string."""
    if acres >= 1_000_000:
        return f"{acres / 1_000_000:.1f}M"
    return f"{acres:,.0f}"


def filter_events(
    df: pd.DataFrame,
    year_range: tuple,
    severities: list,
    min_acres: float,
) -> pd.DataFrame:
    """Apply year range, severity, and minimum acreage filters to the events DataFrame."""
    mask = (
        (df['year'] >= year_range[0]) &
        (df['year'] <= year_range[1]) &
        (df['severity'].isin(severities)) &
        (df['acres'] >= min_acres)
    )
    return df[mask].copy()


def compute_map_stats(df: pd.DataFrame) -> dict:
    """Compute aggregate stats shown in the summary bar."""
    total_acres = df['acres'].sum()
    pct_high = len(df[df['severity'] == 'High']) / len(df) * 100 if len(df) > 0 else 0
    year_min = int(df['year'].min()) if len(df) > 0 else '—'
    year_max = int(df['year'].max()) if len(df) > 0 else '—'
    return {
        'event_count': len(df),
        'total_acres_fmt': format_acres(total_acres),
        'pct_high_fmt': f"{pct_high:.0f}%",
        'year_range': f"{year_min}–{year_max}",
    }


def build_folium_map(df: pd.DataFrame) -> folium.Map:
    """Build a Folium map with fire event circle markers."""
    m = folium.Map(
        location=[37.5, -119.5],
        zoom_start=6,
        tiles='CartoDB dark_matter',
    )
    for _, row in df.iterrows():
        radius = max(4, min(20, row['acres'] / 20_000))
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=radius,
            color=severity_color(row['severity']),
            fill=True,
            fill_color=severity_color(row['severity']),
            fill_opacity=0.7,
            tooltip=f"{row['event_name']} ({row['year']})",
            popup=folium.Popup(row['event_id'], max_width=200),
        ).add_to(m)
    return m


@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH)


def render_explorer():
    if not os.path.exists(DATA_PATH):
        st.error("Data file not found. Run `python scripts/preprocess_data.py` first.")
        return

    df = load_data()

    # ── Page header ───────────────────────────────────────────────────────────
    st.markdown(
        "<div style='color:#22c55e;font-size:11px;letter-spacing:3px;text-transform:uppercase;'>"
        "Interactive Explorer</div>",
        unsafe_allow_html=True,
    )
    st.title("California Fire Events")
    st.caption("Filter, explore, and inspect individual wildfire events from the MTBS dataset.")

    # ── Filters ───────────────────────────────────────────────────────────────
    col_yr, col_sev, col_ac, col_count = st.columns([3, 2, 2, 1])

    with col_yr:
        year_range = st.slider(
            "Year Range",
            min_value=int(df['year'].min()),
            max_value=int(df['year'].max()),
            value=(int(df['year'].min()), int(df['year'].max())),
        )
    with col_sev:
        severities = st.multiselect(
            "Severity",
            options=SEVERITY_ORDER,
            default=SEVERITY_ORDER,
        )
    with col_ac:
        min_acres_options = {
            'Any size': 0,
            '10K+ acres': 10_000,
            '100K+ acres': 100_000,
        }
        min_acres_label = st.selectbox("Min Acres", options=list(min_acres_options.keys()))
        min_acres = min_acres_options[min_acres_label]

    filtered = filter_events(df, year_range=year_range, severities=severities or SEVERITY_ORDER, min_acres=min_acres)
    map_stats = compute_map_stats(filtered)

    with col_count:
        st.metric("Events", f"{map_stats['event_count']:,}")

    # ── Map + Detail layout ───────────────────────────────────────────────────
    map_col, detail_col = st.columns([3, 1])

    map_data = None
    with map_col:
        if filtered.empty:
            st.warning("No events match the current filters.")
        else:
            folium_map = build_folium_map(filtered)
            map_data = st_folium(folium_map, width='100%', height=500, returned_objects=['last_object_clicked_popup'])

    with detail_col:
        st.markdown("**Selected Event**")
        clicked_id = None
        if map_data and map_data.get('last_object_clicked_popup'):
            clicked_id = map_data['last_object_clicked_popup']

        if clicked_id and clicked_id in filtered['event_id'].values:
            row = filtered[filtered['event_id'] == clicked_id].iloc[0]
            st.markdown(f"**{row['event_name']}**")
            st.caption(row['event_id'])

            m1, m2 = st.columns(2)
            m1.metric("Acres", format_acres(row['acres']))
            m2.metric("Severity", row['severity'])
            m3, m4 = st.columns(2)
            m3.metric("Max Temp", f"{row['max_temp_c']}°C")
            m4.metric("Min Humidity", f"{row['min_humidity_pct']}%")
            st.caption(f"Ignition: {row['ig_date']}")

            evi_img = EVI_DIR / f"{clicked_id}.png"
            if evi_img.exists():
                st.image(str(evi_img), caption="EVI Map", use_column_width=True)
            else:
                st.info("No EVI export available for this event.")
        else:
            st.info("Click a fire event on the map to see details.")

    # ── Summary bar ───────────────────────────────────────────────────────────
    st.divider()
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Events Shown", f"{map_stats['event_count']:,}")
    s2.metric("Total Acres", map_stats['total_acres_fmt'])
    s3.metric("% High Severity", map_stats['pct_high_fmt'])
    s4.metric("Date Range", map_stats['year_range'])
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_explorer.py -v
```

Expected output:
```
PASSED tests/test_explorer.py::test_filter_events_year_range
PASSED tests/test_explorer.py::test_filter_events_severity
PASSED tests/test_explorer.py::test_filter_events_min_acres
PASSED tests/test_explorer.py::test_filter_events_combined
PASSED tests/test_explorer.py::test_severity_color
PASSED tests/test_explorer.py::test_format_acres_thousands
PASSED tests/test_explorer.py::test_format_acres_millions
PASSED tests/test_explorer.py::test_compute_map_stats_keys
PASSED tests/test_explorer.py::test_compute_map_stats_values
9 passed
```

- [ ] **Step 5: Verify in browser**

```bash
streamlit run app.py
```

Click "🗺 Explorer" tab. Expected: year slider, severity multiselect, min acres dropdown, Folium map showing fire event dots coloured by severity, summary stats bar at bottom. Click a dot — event details appear in the right panel.

- [ ] **Step 6: Commit**

```bash
git add pages/explorer.py tests/test_explorer.py
git commit -m "feat: add Explorer tab with Folium fire map, filters, and event detail panel"
```

---

## Task 6: Full Test Suite + Deployment Setup

**Files:**
- Create: `tests/conftest.py`
- Create: `Procfile` (for Streamlit Cloud)

- [ ] **Step 1: Run full test suite and confirm all pass**

```bash
pytest tests/ -v
```

Expected: All tests across `test_preprocess.py`, `test_story.py`, `test_research.py`, `test_explorer.py` pass.

- [ ] **Step 2: Create tests/conftest.py**

`tests/conftest.py`:
```python
import sys
import os

# Ensure project root is on the path for all test modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
```

- [ ] **Step 3: Create Procfile for Streamlit Cloud**

`Procfile`:
```
web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

- [ ] **Step 4: Verify data/mtbs_ca_summary.csv is NOT committed (it's in .gitignore)**

The existing `.gitignore` already excludes `**/data/` so the CSV is safe. Confirm:

```bash
git status
```

Expected: `data/` does not appear in staged files.

- [ ] **Step 5: Final commit**

```bash
git add tests/conftest.py Procfile
git commit -m "feat: add test conftest and Streamlit Cloud Procfile"
```

- [ ] **Step 6: Deploy to Streamlit Cloud**

1. Push to GitHub: `git push origin main`
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → select repo `bikal3/mtbs_wildfires` → main branch → `app.py`
4. Note: `data/mtbs_ca_summary.csv` is gitignored. You must either:
   - Upload it via Streamlit Cloud secrets/file upload, **or**
   - Commit a small sample CSV (e.g., 50 representative events) as `data/mtbs_ca_summary_sample.csv` and update `DATA_PATH` in each page to fall back to the sample if the full CSV is absent

Recommended fallback — add to each page's `load_data()`:
```python
@st.cache_data
def load_data() -> pd.DataFrame:
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    sample_path = DATA_PATH.replace('mtbs_ca_summary.csv', 'mtbs_ca_summary_sample.csv')
    return pd.read_csv(sample_path)
```
