# California Wildfire Analysis (1984–2022)

An end-to-end data science project combining satellite imagery, climate records, and 38 years of MTBS fire data to understand how California's wildfire crisis has intensified — and what the land looks like after the flames.

## Live Demo

[View the app on Streamlit Cloud](https://your-app-url.streamlit.app)

> The app is hosted on Streamlit Cloud's free tier. If it shows **"This app has gone to sleep due to inactivity"**, click **"Yes, get it back up!"** and it will be ready in about 30 seconds.

## Overview

This project has two parts:

- **Streamlit web app** — an interactive dashboard with a narrative story, statistical research, and a map explorer
- **Jupyter notebooks** — the original analysis work (EVI retrieval, MTBS data exploration, weather data) located in `src/`

## Running the Web App

### Requirements

```bash
pip install -r requirements.txt
```

### Launch

```bash
streamlit run app.py
```

The app runs on `http://localhost:8501` by default.

### Using sample data

If the full dataset (`data/mtbs_ca_summary.csv`) is not present, the app automatically falls back to a built-in sample of 50 representative California fire events. To generate the full dataset:

```bash
python scripts/preprocess_data.py
```

## App Tabs

| Tab | Description |
| --- | ----------- |
| Story | Narrative overview — trends, vegetation recovery, and key findings |
| Research | Statistical analysis — era comparisons, fire weather, top fires, seasonality |
| Explorer | Interactive map — filter by year, severity, and acreage; click a fire for details |

## Project Structure

```
.
├── app.py                  # Streamlit entry point
├── pages/
│   ├── story.py            # Story tab
│   ├── research.py         # Research tab
│   └── explorer.py         # Explorer tab
├── components/
│   ├── story_hero.html     # Hero section template
│   └── story_sections.html # Narrative sections template
├── utils/
│   ├── data_loader.py      # Data loading and caching
│   └── theme.py            # Chart and map theme constants
├── data/
│   ├── mtbs_ca_summary.csv         # Full dataset (generated)
│   └── mtbs_ca_summary_sample.csv  # Sample dataset (50 events)
├── scripts/
│   └── preprocess_data.py  # Generates the full dataset from raw MTBS files
└── src/                    # Jupyter notebooks and original analysis
    └── README.md           # Notebook setup guide (Docker, utils reference)
```

## Tech Stack

- **Streamlit** — web app framework
- **Plotly** — interactive charts
- **Folium / st-folium** — interactive map
- **Pandas** — data processing
- **MTBS** — Monitoring Trends in Burn Severity dataset (USGS)

## Deployment

To deploy on Streamlit Cloud, connect this repository and set the main file to `app.py`. No additional configuration is needed — the app uses the bundled sample data when the full dataset is not available.

## Notebooks and Docker Setup

See [`src/README.md`](src/README.md) for instructions on running the Jupyter notebooks via Docker, including EVI retrieval, MTBS exploration, and weather data analysis.
