import os
from pathlib import Path
import pandas as pd
import folium
from streamlit_folium import st_folium
import streamlit as st
import plotly.graph_objects as go
from utils.data_loader import load_data, DATA_PATH, SAMPLE_DATA_PATH, is_sample_data
from utils.theme import get_theme
from analysis.events import compute_map_stats, filter_events, format_acres, severity_color
from analysis.stats import SEVERITY_ORDER, prepare_evi_recovery_data

EVI_DIR = Path(__file__).parent.parent / 'data' / 'evi_exports'

def build_folium_map(df: pd.DataFrame, selected_id: str = None) -> folium.Map:
    """Build a Folium map with fire event circle markers."""
    t = get_theme()
    m = folium.Map(
        location=[37.5, -119.5],
        zoom_start=6,
        tiles=t['folium_tiles'],
    )
    legend_html = f"""
<div style="position:fixed;top:10px;right:10px;z-index:1000;background:{t['legend_bg']};
     border-radius:6px;padding:10px 14px;color:{t['legend_text']};font-size:12px;
     box-shadow:0 2px 8px {t['legend_shadow']};">
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

    # ── Sample data notice ────────────────────────────────────────────────────
    if is_sample_data():
        st.info(
            f"**Sample dataset** — showing {len(df)} representative events for preview. "
            "The full California MTBS dataset (1984–2022) contains **1,000+ fire events** "
            "spanning 38 years. Run `python scripts/preprocess_data.py` to load the complete data.",
            icon="ℹ️",
        )

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
    # Use a filter-derived key so the map widget resets (and clears stale clicks)
    # whenever the user changes any filter, but stays stable between reruns with
    # the same filters — preserving the click data returned by st_folium.
    map_key = f"fire_map_{year_range[0]}_{year_range[1]}_{selected_severity}_{min_acres}"

    if st.session_state.get('_last_map_key') != map_key:
        st.session_state.pop('explorer_clicked_id', None)
        st.session_state['_last_map_key'] = map_key

    clicked_id = st.session_state.get('explorer_clicked_id')

    map_col, detail_col = st.columns([3, 1])

    with map_col:
        if filtered.empty:
            st.warning("No events match the current filters.")
        else:
            folium_map = build_folium_map(filtered, selected_id=clicked_id)
            map_data = st_folium(
                folium_map,
                width='100%',
                height=500,
                returned_objects=['last_object_clicked_popup'],
                key=map_key,
            )
            if map_data and map_data.get('last_object_clicked_popup'):
                raw = str(map_data['last_object_clicked_popup']).strip()
                if raw in filtered['event_id'].values:
                    st.session_state['explorer_clicked_id'] = raw
                    clicked_id = raw

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
            t = get_theme()
            evi_df = prepare_evi_recovery_data()
            fig_evi = go.Figure()
            fig_evi.add_trace(go.Scatter(x=evi_df['months_after_fire'], y=evi_df['low_severity'], mode='lines', name='Low', line=dict(color='#22c55e', width=1.5)))
            fig_evi.add_trace(go.Scatter(x=evi_df['months_after_fire'], y=evi_df['high_severity'], mode='lines', name='High', line=dict(color='#ef4444', width=1.5, dash='dash')))
            fig_evi.update_layout(
                paper_bgcolor=t['chart_paper'], plot_bgcolor=t['chart_plot'],
                font_color=t['chart_font'],
                title=dict(text='EVI Recovery (3yr) — reference', font=dict(color=t['chart_title'], size=12)),
                margin=dict(l=30, r=10, t=30, b=30), height=180,
                xaxis=dict(title='Months', showgrid=False, tickfont=dict(size=9)),
                yaxis=dict(title='EVI', gridcolor=t['chart_grid'], range=[0, 0.7], tickfont=dict(size=9)),
                legend=dict(bgcolor=t['card_bg'], font=dict(size=9)),
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
