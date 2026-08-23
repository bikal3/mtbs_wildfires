# California Wildfire Analysis (1984–2022)

An end-to-end data science project combining satellite imagery, climate records, and 38 years of MTBS fire data to understand how California's wildfire crisis has intensified — and what the land looks like after the flames.

## Live Site

**[mtbs-wildfires.bikal3.com.np](https://mtbs-wildfires.bikal3.com.np)**

A static site — no server, no cold start, nothing to wake up.

| Page | Contents |
| --- | --- |
| [Story](https://mtbs-wildfires.bikal3.com.np/) | Narrative overview — trends, vegetation recovery, key findings |
| [Research](https://mtbs-wildfires.bikal3.com.np/research) | Statistical analysis — era comparisons, fire weather, largest events, seasonality |
| [Explorer](https://mtbs-wildfires.bikal3.com.np/explorer) | Interactive map — filter by year, severity, and acreage; click a fire for details |

## Overview

Two parts:

- **Static site** (`site/`) — vanilla HTML/CSS/JS with vendored Plotly and Leaflet, built from JSON that two offline Python scripts generate
- **Jupyter notebooks** (`src/`) — the original analysis work: EVI retrieval, MTBS exploration, weather data

The dataset covers **1,683 California wildfire events, 1984–2022**, totalling 23.9M acres.

## Data Pipeline

Both steps run locally, and their output is committed, so deploying needs no build.

```bash
# 1. Download MTBS perimeters and fetch per-event weather (slow: ~15-45 min)
pip install -r requirements-preprocess.txt
python scripts/preprocess_data.py        # -> data/mtbs_ca_summary.csv

# 2. Turn the CSV into the site's JSON
pip install -r requirements-build.txt
python scripts/build_site.py             # -> site/assets/{events,stats}.json
python scripts/build_site.py --sample    # build against the 50-event sample instead
```

### Sources

**Fire perimeters** come from the official USGS MTBS composite release
(`mtbs_perimeter_data.zip`, ~390 MB). Only the attribute table is read — MTBS
supplies `burnbndlat`/`burnbndlon` directly, so the 616 MB geometry is never
touched and no geospatial stack is needed beyond `pyogrio`.

**Weather** comes from the Open-Meteo **archive** API
(`archive-api.open-meteo.com`, ERA5, 1940–present). Note that the
*historical-forecast* endpoint only serves 2016 onward and cannot cover this
dataset — using it silently yields null weather for every pre-2016 fire.

`preprocess_data.py` tracks per-event failures and aborts if more than 5% fail,
so a systemic problem stops the run instead of producing a CSV full of nulls.

Downloaded archives land in `data/raw/` (~1 GB, gitignored). Re-runs skip both
the download and the cached weather requests.

### Scope

`MAX_YEAR = 2022` in `scripts/preprocess_data.py` caps the dataset. The MTBS
release now extends to 2025; raising the cap also means widening the era bins in
`analysis/stats.py` and updating the "38 years" copy in `site/`.

## Running Locally

```bash
python -m http.server 8000 --directory site
```

Then open <http://localhost:8000>. Use `/research.html` and `/explorer.html`
locally — the extensionless URLs are a Cloudflare Pages feature.

## Tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

The pure pandas logic lives in `analysis/` precisely so it stays testable
independently of how it is rendered.

## Project Structure

```
.
├── site/                   # The deployed static site (committed build output)
│   ├── index.html          #   Story
│   ├── research.html       #   Research
│   ├── explorer.html       #   Explorer
│   ├── _headers            #   Cloudflare Pages cache rules
│   └── assets/             #   CSS, JS, vendored libs, generated JSON
├── analysis/               # Pure pandas logic, shared by the build and the tests
│   ├── stats.py            #   Chart aggregates
│   └── events.py           #   Per-event filtering and formatting
├── scripts/
│   ├── preprocess_data.py  # MTBS + weather -> data/mtbs_ca_summary.csv
│   └── build_site.py       # CSV -> site/assets/*.json
├── data/
│   ├── mtbs_ca_summary.csv         # Full dataset, 1,683 events (committed)
│   └── mtbs_ca_summary_sample.csv  # 50-event sample
├── tests/
└── src/                    # Jupyter notebooks and original analysis
    └── README.md           # Notebook setup guide (Docker, utils reference)
```

## Deployment

Cloudflare Pages, project `mtbs-wildfires`, via **direct upload** — the project
is not connected to Git, so pushing to GitHub does **not** deploy. To publish:

```bash
npx wrangler pages deploy site --project-name=mtbs-wildfires --branch=main
```

Re-run `build_site.py` first if the data changed. A Pages custom domain needs
two things that are configured separately: a DNS record pointing at
`mtbs-wildfires.pages.dev`, **and** the hostname registered under the project's
Custom domains. Either one alone returns an error.

## Tech Stack

- **Plotly.js** — interactive charts (basic bundle, vendored)
- **Leaflet** — interactive map, canvas renderer (vendored)
- **pandas / pyogrio** — data processing
- **Cloudflare Pages** — hosting
- **MTBS** — Monitoring Trends in Burn Severity (USGS)
- **Open-Meteo** — historical weather archive

## A Note on the EVI Figures

The 3-year EVI recovery curves shown on the Story, Research, and Explorer pages
are **illustrative reference values, not computed from this dataset**. The
per-event EVI work lives in `src/evi.ipynb` and was never wired into the
pipeline. Every chart built from them is labelled accordingly.

## Notebooks and Docker Setup

See [`src/README.md`](src/README.md) for running the Jupyter notebooks via
Docker, including EVI retrieval, MTBS exploration, and weather data analysis.
