import os
from pathlib import Path
import pandas as pd
import folium
from streamlit_folium import st_folium
import streamlit as st
import plotly.graph_objects as go
from utils.data_loader import load_data, DATA_PATH, SAMPLE_DATA_PATH

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
    year_min = int(df['year'].min()) if len(df) > 0 else None
    year_max = int(df['year'].max()) if len(df) > 0 else None
    year_range_fmt = f"{year_min}\u2013{year_max}" if year_min is not None else '—'
    return {
        'event_count': len(df),
        'total_acres_fmt': format_acres(total_acres),
        'pct_high_fmt': f"{pct_high:.0f}%",
        'year_range': year_range_fmt,
    }


def _evi_recovery_data() -> pd.DataFrame:
    months = list(range(0, 37, 3))
    low_severity  = [0.55, 0.42, 0.48, 0.51, 0.54, 0.55, 0.56, 0.57, 0.57, 0.58, 0.58, 0.58, 0.59]
    high_severity = [0.55, 0.10, 0.15, 0.20, 0.25, 0.28, 0.30, 0.32, 0.33, 0.34, 0.35, 0.35, 0.36]
    return pd.DataFrame({'months': months, 'low': low_severity, 'high': high_severity})


def build_folium_map(df: pd.DataFrame, selected_id: str = None) -> folium.Map:
    """Build a Folium map with fire event circle markers."""
    m = folium.Map(
        location=[37.5, -119.5],
        zoom_start=6,
        tiles='CartoDB dark_matter',
    )
    legend_html = """
<div style="position:fixed;top:10px;right:10px;z-index:1000;background:#1e293b;
     border-radius:6px;padding:10px 14px;color:#e2e8f0;font-size:12px;
     box-shadow:0 2px 8px rgba(0,0,0,0.5);">
  <b>Severity</b><br>
  <span style="color:#fbbf24;">●</span> Low<br>
  <span style="color:#f97316;">●</span> Medium<br>
  <span style="color:#ef4444;">●</span> High
</div>
"""
    m.get_root().html.add_child(folium.Element(legend_html))
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
        if selected_id and row['event_id'] == selected_id:
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=radius + 8,
                color='#ffffff',
                weight=2,
                fill=False,
                opacity=0.8,
            ).add_to(m)
    return m


def render_explorer():
    if not os.path.exists(DATA_PATH) and not os.path.exists(SAMPLE_DATA_PATH):
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
            min_value=1984,
            max_value=2022,
            value=(1984, 2022),
        )
    with col_sev:
        selected_severity = st.selectbox(
            "Severity",
            options=['All', 'Low', 'Medium', 'High'],
        )
        severities = SEVERITY_ORDER if selected_severity == 'All' else [selected_severity]
    with col_ac:
        min_acres_options = {
            'Any size': 0,
            '10K+ acres': 10_000,
            '100K+ acres': 100_000,
        }
        min_acres_label = st.selectbox("Min Acres", options=list(min_acres_options.keys()))
        min_acres = min_acres_options[min_acres_label]

    filtered = filter_events(df, year_range=year_range, severities=severities, min_acres=min_acres)
    map_stats = compute_map_stats(filtered)

    with col_count:
        st.metric("Events", f"{map_stats['event_count']:,}")

    # ── Map + Detail layout ───────────────────────────────────────────────────
    map_data = None
    map_col, detail_col = st.columns([3, 1])

    # Extract clicked_id from previous render (from session state or prior map_data)
    # Note: map_data is None on first render, so clicked_id will be None too
    clicked_id = st.session_state.get('explorer_clicked_id')

    with map_col:
        if filtered.empty:
            st.warning("No events match the current filters.")
        else:
            folium_map = build_folium_map(filtered, selected_id=clicked_id)
            map_data = st_folium(folium_map, width='100%', height=500, returned_objects=['last_object_clicked_popup'])
            if map_data and map_data.get('last_object_clicked_popup'):
                st.session_state['explorer_clicked_id'] = map_data['last_object_clicked_popup']
                clicked_id = st.session_state['explorer_clicked_id']

    with detail_col:
        st.markdown("**Selected Event**")

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

            # Mini EVI recovery chart
            evi_df = _evi_recovery_data()
            fig_evi = go.Figure()
            fig_evi.add_trace(go.Scatter(x=evi_df['months'], y=evi_df['low'], mode='lines', name='Low', line=dict(color='#22c55e', width=1.5)))
            fig_evi.add_trace(go.Scatter(x=evi_df['months'], y=evi_df['high'], mode='lines', name='High', line=dict(color='#ef4444', width=1.5, dash='dash')))
            fig_evi.update_layout(
                paper_bgcolor='#111', plot_bgcolor='#111',
                font_color='#9ca3af',
                title=dict(text='EVI Recovery (3yr) — reference', font=dict(color='#e2e8f0', size=12)),
                margin=dict(l=30, r=10, t=30, b=30), height=180,
                xaxis=dict(title='Months', showgrid=False, tickfont=dict(size=9)),
                yaxis=dict(title='EVI', gridcolor='#1e293b', range=[0, 0.7], tickfont=dict(size=9)),
                legend=dict(bgcolor='#1e293b', font=dict(size=9)),
                showlegend=True,
            )
            st.plotly_chart(fig_evi, use_container_width=True)

            evi_img = EVI_DIR / f"{clicked_id}.png"
            if evi_img.exists():
                with st.expander("View full EVI map"):
                    st.image(str(evi_img), use_container_width=True)
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
