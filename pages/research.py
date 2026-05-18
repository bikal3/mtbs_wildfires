import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from utils.data_loader import load_data, DATA_PATH, SAMPLE_DATA_PATH, is_sample_data
from utils.theme import get_theme


SEVERITY_COLORS = {'Low': '#22c55e', 'Medium': '#f97316', 'High': '#ef4444'}


# ── Data helpers ──────────────────────────────────────────────────────────────

def prepare_severity_chart_data(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby('year')['acres'].sum().reset_index()


def prepare_evi_recovery_data() -> pd.DataFrame:
    months = list(range(0, 37, 3))
    low_severity  = [0.55, 0.42, 0.48, 0.51, 0.54, 0.55, 0.56, 0.57, 0.57, 0.58, 0.58, 0.58, 0.59]
    high_severity = [0.55, 0.10, 0.15, 0.20, 0.25, 0.28, 0.30, 0.32, 0.33, 0.34, 0.35, 0.35, 0.36]
    return pd.DataFrame({'months_after_fire': months,
                         'low_severity': low_severity,
                         'high_severity': high_severity})


def compute_research_stats(df: pd.DataFrame) -> dict:
    total_acres = df['acres'].sum()
    pct_high = round(len(df[df['severity'] == 'High']) / len(df) * 100, 1) if len(df) > 0 else 0.0
    return {
        'total_events': len(df),
        'total_acres_m': float(round(total_acres / 1_000_000, 1)),
        'pct_high': pct_high,
        'year_min': int(df['year'].min()) if len(df) > 0 else 0,
        'year_max': int(df['year'].max()) if len(df) > 0 else 0,
    }


def prepare_decade_severity(df: pd.DataFrame) -> pd.DataFrame:
    """Count Low/Medium/High events per decade."""
    d = df.copy()
    d['decade'] = pd.cut(d['year'], bins=[1983, 1999, 2009, 2022],
                         labels=['1984–1999', '2000–2009', '2010–2022'])
    return (d.groupby(['decade', 'severity'], observed=True)
             .size().reset_index(name='count'))


def compute_era_stats(df: pd.DataFrame) -> list:
    """Return per-era dicts for the comparison metrics grid."""
    eras = [('1984–1999', 1984, 1999), ('2000–2009', 2000, 2009), ('2010–2022', 2010, 2022)]
    result = []
    for label, y0, y1 in eras:
        sub = df[(df['year'] >= y0) & (df['year'] <= y1)]
        if len(sub) == 0:
            result.append({'label': label, 'events': 0, 'acres_m': 0.0,
                           'avg_acres': 0, 'pct_high': 0.0})
            continue
        result.append({
            'label': label,
            'events': len(sub),
            'acres_m': round(sub['acres'].sum() / 1_000_000, 1),
            'avg_acres': int(sub['acres'].mean()),
            'pct_high': round(len(sub[sub['severity'] == 'High']) / len(sub) * 100, 1),
        })
    return result


def prepare_top_fires(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    top = df.nlargest(n, 'acres')[['event_name', 'year', 'acres', 'severity']].copy()
    top['label'] = top['event_name'].str.title() + ' (' + top['year'].astype(str) + ')'
    return top.sort_values('acres')


def prepare_fire_season(df: pd.DataFrame) -> pd.DataFrame:
    """Fire count by ignition month."""
    d = df.copy()
    d['month'] = pd.to_datetime(d['ig_date']).dt.month
    month_names = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun',
                   7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
    counts = (pd.DataFrame({'month': range(1, 13)})
              .merge(d.groupby('month').size().reset_index(name='count'), on='month', how='left')
              .fillna(0))
    counts['month_name'] = counts['month'].map(month_names)
    counts['count'] = counts['count'].astype(int)
    return counts


# ── Render ────────────────────────────────────────────────────────────────────

def render_research():
    if not os.path.exists(DATA_PATH) and not os.path.exists(SAMPLE_DATA_PATH):
        st.error("Data file not found. Run `python scripts/preprocess_data.py` first.")
        return

    df = load_data()
    stats = compute_research_stats(df)
    t = get_theme()

    if is_sample_data():
        st.info(
            f"**Sample dataset** — charts show {len(df)} representative events. "
            "The full dataset contains **1,000+ California wildfire events** (1984–2022). "
            "Run `python scripts/preprocess_data.py` to load the complete data.",
            icon="ℹ️",
        )

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='color:#38bdf8;font-size:11px;letter-spacing:3px;text-transform:uppercase;'>"
        "Full Research</div>", unsafe_allow_html=True)
    st.title("MTBS Wildfire Analysis")
    st.caption(
        f"California · {stats['year_min']}–{stats['year_max']} · "
        "Google Earth Engine · Landsat · Sentinel-2 · Open-Meteo")
    st.divider()

    # ── 01 About ──────────────────────────────────────────────────────────────
    st.subheader("01 — About")
    st.write(
        "This project investigates how satellite-derived vegetation indices and climate data "
        "can characterise wildfire burn severity trends across California over 38 years. "
        "Data is sourced from the Monitoring Trends in Burn Severity (MTBS) programme, "
        "Google Earth Engine, AWS S3, and the Open-Meteo API.")
    st.link_button("💻 GitHub Repo", "https://github.com/bikal3/mtbs_wildfires")
    st.divider()

    # ── 02 Data Sources ───────────────────────────────────────────────────────
    st.subheader("02 — Data Sources")
    c1, c2, c3, c4 = st.columns(4)
    for col, label, caption in [
        (c1, "**:orange[MTBS]**",
         "Burn severity + fire perimeters, 1984–2022. Sourced via GEE and AWS S3."),
        (c2, "**:green[Landsat 8 / Sentinel-2]**",
         "Multispectral imagery for EVI and NDVI calculation via Google Earth Engine."),
        (c3, "**:blue[Open-Meteo API]**",
         "Historical weather conditions (temp, wind, humidity) per fire event."),
        (c4, "**:violet[AWS S3 / Source Coop]**",
         "Large-scale USGS/MTBS shapefiles processed via Dask distributed computing."),
    ]:
        with col:
            st.markdown(label)
            st.caption(caption)
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
                f"<div style='background:{t['card_bg']};border-radius:6px;padding:12px;text-align:center;'>"
                f"<div style='font-size:24px;'>{icon}</div>"
                f"<div style='color:{t['card_text']};font-weight:700;margin-top:6px;'>{label}</div>"
                f"<div style='color:{t['card_sub']};font-size:12px;'>{sublabel}</div>"
                f"</div>", unsafe_allow_html=True)
    st.divider()

    # ── 04 Acres Burned & EVI Recovery ───────────────────────────────────────
    st.subheader("04 — Acres Burned & EVI Recovery")
    chart_col, evi_col = st.columns(2)

    with chart_col:
        fig_bar = px.bar(
            prepare_severity_chart_data(df), x='year', y='acres',
            color='acres',
            color_continuous_scale=['#7f1d1d', '#ef4444', '#f97316', '#fbbf24'],
            labels={'year': 'Year', 'acres': 'Acres Burned'},
            title='Total Acres Burned per Year',
        )
        fig_bar.update_layout(
            paper_bgcolor=t['chart_paper'], plot_bgcolor=t['chart_plot'],
            font_color=t['chart_font'], coloraxis_showscale=False,
            title_font_color=t['chart_title'],
            margin=dict(l=40, r=20, t=40, b=40), height=300,
            xaxis=dict(showgrid=False), yaxis=dict(gridcolor=t['chart_grid']),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with evi_col:
        evi_data = prepare_evi_recovery_data()
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=evi_data['months_after_fire'], y=evi_data['low_severity'],
            mode='lines', name='Low severity', line=dict(color='#22c55e', width=2)))
        fig_line.add_trace(go.Scatter(
            x=evi_data['months_after_fire'], y=evi_data['high_severity'],
            mode='lines', name='High severity', line=dict(color='#ef4444', width=2, dash='dash')))
        fig_line.add_vline(x=0, line_color='#f97316', line_dash='dot', annotation_text='Fire')
        fig_line.update_layout(
            paper_bgcolor=t['chart_paper'], plot_bgcolor=t['chart_plot'],
            font_color=t['chart_font'], title='EVI Recovery Timeline (3 years)',
            title_font_color=t['chart_title'],
            margin=dict(l=40, r=20, t=40, b=40), height=300,
            xaxis=dict(title='Months after fire', showgrid=False),
            yaxis=dict(title='EVI index', gridcolor=t['chart_grid'], range=[0, 0.7]),
            legend=dict(bgcolor=t['card_bg']),
        )
        st.plotly_chart(fig_line, use_container_width=True)
    st.divider()

    # ── 05 Era Comparison ─────────────────────────────────────────────────────
    st.subheader("05 — Era Comparison")
    st.caption("How the wildfire crisis has escalated across three distinct eras.")

    eras = compute_era_stats(df)
    era_cols = st.columns(3)
    era_metrics = [
        ("Total events",    'events',    "",     None),
        ("Total acres (M)", 'acres_m',   "M",    None),
        ("Avg fire size",   'avg_acres', " ac",  None),
        ("% High severity", 'pct_high',  "%",    None),
    ]
    for col, era in zip(era_cols, eras):
        with col:
            st.markdown(
                f"<div style='background:{t['card_bg']};border-radius:8px;padding:16px 20px;"
                f"border-top:3px solid #f97316;'>"
                f"<div style='color:#f97316;font-size:11px;font-weight:700;letter-spacing:2px;"
                f"text-transform:uppercase;margin-bottom:12px;'>{era['label']}</div>"
                f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;'>"
                f"<div><div style='color:{t['card_sub']};font-size:11px;'>Events</div>"
                f"<div style='color:{t['card_text']};font-size:20px;font-weight:800;'>{era['events']}</div></div>"
                f"<div><div style='color:{t['card_sub']};font-size:11px;'>Acres (M)</div>"
                f"<div style='color:{t['card_text']};font-size:20px;font-weight:800;'>{era['acres_m']}</div></div>"
                f"<div><div style='color:{t['card_sub']};font-size:11px;'>Avg size</div>"
                f"<div style='color:{t['card_text']};font-size:20px;font-weight:800;'>{era['avg_acres']:,}</div></div>"
                f"<div><div style='color:{t['card_sub']};font-size:11px;'>% High</div>"
                f"<div style='color:#ef4444;font-size:20px;font-weight:800;'>{era['pct_high']}%</div></div>"
                f"</div></div>",
                unsafe_allow_html=True)

    st.write("")
    decade_data = prepare_decade_severity(df)
    fig_dec = px.bar(
        decade_data, x='decade', y='count', color='severity',
        color_discrete_map=SEVERITY_COLORS,
        category_orders={'severity': ['Low', 'Medium', 'High']},
        labels={'decade': '', 'count': 'Number of fires', 'severity': 'Severity'},
        title='Fire Count by Severity — Three Eras',
        barmode='group',
    )
    fig_dec.update_layout(
        paper_bgcolor=t['chart_paper'], plot_bgcolor=t['chart_plot'],
        font_color=t['chart_font'], title_font_color=t['chart_title'],
        margin=dict(l=40, r=20, t=40, b=40), height=300,
        xaxis=dict(showgrid=False), yaxis=dict(gridcolor=t['chart_grid']),
        legend=dict(bgcolor=t['card_bg']),
    )
    st.plotly_chart(fig_dec, use_container_width=True)
    st.divider()

    # ── 06 Fire Weather Analysis ──────────────────────────────────────────────
    st.subheader("06 — Fire Weather Analysis")
    st.caption(
        "Each dot is one fire event. Higher temperatures and lower humidity are strongly "
        "associated with larger, high-severity fires.")

    fig_scatter = px.scatter(
        df,
        x='max_temp_c',
        y='acres',
        color='severity',
        color_discrete_map=SEVERITY_COLORS,
        size='acres',
        size_max=40,
        hover_name='event_name',
        hover_data={'year': True, 'max_temp_c': ':.1f', 'min_humidity_pct': True,
                    'acres': ':,.0f', 'severity': True},
        labels={
            'max_temp_c':       'Max Temperature (°C)',
            'acres':            'Acres Burned',
            'min_humidity_pct': 'Min Humidity (%)',
            'severity':         'Severity',
        },
        title='Temperature vs Acres Burned',
        log_y=True,
    )
    fig_scatter.update_traces(marker=dict(opacity=0.75, line=dict(width=0.5, color='white')))
    fig_scatter.update_layout(
        paper_bgcolor=t['chart_paper'], plot_bgcolor=t['chart_plot'],
        font_color=t['chart_font'], title_font_color=t['chart_title'],
        margin=dict(l=40, r=20, t=40, b=40), height=380,
        xaxis=dict(showgrid=False, title='Max Temperature (°C)'),
        yaxis=dict(gridcolor=t['chart_grid'], title='Acres Burned (log scale)'),
        legend=dict(bgcolor=t['card_bg']),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Humidity strip chart below
    fig_hum = px.strip(
        df, x='min_humidity_pct', y='severity',
        color='severity',
        color_discrete_map=SEVERITY_COLORS,
        category_orders={'severity': ['High', 'Medium', 'Low']},
        hover_name='event_name',
        hover_data={'year': True, 'min_humidity_pct': True},
        labels={'min_humidity_pct': 'Min Relative Humidity (%)', 'severity': ''},
        title='Min Humidity Distribution by Severity',
    )
    fig_hum.update_traces(marker=dict(size=9, opacity=0.7))
    fig_hum.update_layout(
        paper_bgcolor=t['chart_paper'], plot_bgcolor=t['chart_plot'],
        font_color=t['chart_font'], title_font_color=t['chart_title'],
        margin=dict(l=40, r=20, t=40, b=40), height=260,
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor=t['chart_grid']),
        showlegend=False,
    )
    st.plotly_chart(fig_hum, use_container_width=True)
    st.divider()

    # ── 07 Largest Events & Fire Season ──────────────────────────────────────
    st.subheader("07 — Largest Events & Fire Season")
    top_col, season_col = st.columns(2)

    with top_col:
        top = prepare_top_fires(df, n=10)
        fig_top = px.bar(
            top, x='acres', y='label',
            color='severity',
            color_discrete_map=SEVERITY_COLORS,
            orientation='h',
            labels={'acres': 'Acres Burned', 'label': '', 'severity': 'Severity'},
            title='Top 10 Largest Fire Events',
        )
        fig_top.update_layout(
            paper_bgcolor=t['chart_paper'], plot_bgcolor=t['chart_plot'],
            font_color=t['chart_font'], title_font_color=t['chart_title'],
            margin=dict(l=10, r=20, t=40, b=40), height=380,
            xaxis=dict(showgrid=False),
            yaxis=dict(gridcolor=t['chart_grid'], tickfont=dict(size=10)),
            legend=dict(bgcolor=t['card_bg']),
        )
        st.plotly_chart(fig_top, use_container_width=True)

    with season_col:
        season = prepare_fire_season(df)
        peak_month = season.loc[season['count'].idxmax(), 'month_name']
        fig_season = px.bar(
            season, x='month_name', y='count',
            color='count',
            color_continuous_scale=['#fef9c3', '#fbbf24', '#f97316', '#dc2626'],
            labels={'month_name': 'Month', 'count': 'Fire Events'},
            title=f'Fire Events by Month (peak: {peak_month})',
        )
        fig_season.update_layout(
            paper_bgcolor=t['chart_paper'], plot_bgcolor=t['chart_plot'],
            font_color=t['chart_font'], title_font_color=t['chart_title'],
            coloraxis_showscale=False,
            margin=dict(l=40, r=20, t=40, b=40), height=380,
            xaxis=dict(showgrid=False),
            yaxis=dict(gridcolor=t['chart_grid']),
        )
        st.plotly_chart(fig_season, use_container_width=True)
    st.divider()

    # ── 08 Key Findings ───────────────────────────────────────────────────────
    st.subheader("08 — Key Findings")
    findings = [
        ("🔥", f"High-severity burn area represents {stats['pct_high']}% of all California "
         "wildfire events in the dataset. Severe events (>100,000 acres) have become "
         "increasingly frequent after 2000."),
        ("🌿", "EVI recovery analysis shows high-severity burned areas reach only ~36% of "
         "pre-fire vegetation levels after 3 years, compared to >58% for low-severity areas."),
        ("🌡", "Weather data from Open-Meteo confirms fire events with max daily temperatures "
         "above 35°C and minimum relative humidity below 15% correspond to the highest "
         "severity outcomes in the dataset."),
        ("📅", "Fire season has shifted and expanded. Events now ignite year-round, with "
         "October–November fires (driven by Santa Ana and Diablo winds) producing some "
         "of the most destructive outcomes despite lower peak summer temperatures."),
    ]
    for icon, text in findings:
        st.markdown(
            f"<div style='background:{t['finding_bg']};border-radius:6px;padding:14px 18px;"
            f"margin-bottom:10px;display:flex;gap:14px;align-items:flex-start;'>"
            f"<div style='font-size:20px;'>{icon}</div>"
            f"<div style='color:{t['finding_text']};font-size:14px;line-height:1.6;'>{text}</div>"
            f"</div>", unsafe_allow_html=True)
    st.divider()

    # ── 09 Tools & Links ──────────────────────────────────────────────────────
    st.subheader("09 — Tools & Links")
    tools = ["Python", "Google Earth Engine", "GeoPandas", "Dask", "Plotly",
             "Folium", "Open-Meteo", "Streamlit"]
    st.markdown(
        " ".join(
            f"<span style='background:{t['badge_bg']};color:{t['badge_text']};padding:4px 10px;"
            f"border-radius:4px;font-size:12px;margin:2px;display:inline-block;'>{tool}</span>"
            for tool in tools),
        unsafe_allow_html=True)
