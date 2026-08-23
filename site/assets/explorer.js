/* Explorer: Leaflet map + filters + detail panel. Requires charts.js and leaflet.js. */

const SEVERITY_ORDER = ['Low', 'Medium', 'High'];

/** Mirrors analysis.events.format_acres. */
function formatAcres(acres) {
  if (acres >= 1e6) return (acres / 1e6).toFixed(1) + 'M';
  return Math.round(acres).toLocaleString('en-US');
}

/** Mirrors analysis.events.filter_events. */
function filterEvents(events, yearFrom, yearTo, severities, minAcres) {
  return events.filter(e =>
    e.year >= yearFrom && e.year <= yearTo &&
    severities.includes(e.severity) &&
    e.acres >= minAcres);
}

/** Mirrors analysis.events.compute_map_stats. */
function computeMapStats(rows) {
  if (rows.length === 0) {
    return { event_count: 0, total_acres_fmt: '0', pct_high_fmt: '0%', year_range: '—' };
  }
  const totalAcres = rows.reduce((sum, e) => sum + e.acres, 0);
  const highCount = rows.filter(e => e.severity === 'High').length;
  const years = rows.map(e => e.year);
  return {
    event_count: rows.length,
    total_acres_fmt: formatAcres(totalAcres),
    pct_high_fmt: Math.round(highCount / rows.length * 100) + '%',
    year_range: Math.min.apply(null, years) + '–' + Math.max.apply(null, years),
  };
}

/** Marker radius, matching the Folium rule: acres/20000, clamped to 4..20. */
function markerRadius(acres) {
  return Math.max(4, Math.min(20, acres / 20000));
}

(async function () {
  const [stats, events] = await Promise.all([
    loadJSON('/assets/stats.json', 'main'),
    loadJSON('/assets/events.json', 'main'),
  ]);
  if (!stats || !events) return;

  fillStats(stats);
  sampleNotice(stats, 'main');

  // ── Map ─────────────────────────────────────────────────────────────────
  // Canvas renderer: 1,000+ SVG circle markers make panning stutter badly.
  const map = L.map('map', { renderer: L.canvas(), preferCanvas: true })
    .setView([37.5, -119.5], 6);

  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    maxZoom: 19,
  }).addTo(map);

  const legend = L.control({ position: 'topright' });
  legend.onAdd = function () {
    const div = L.DomUtil.create('div', 'legend');
    div.innerHTML =
      '<b>Severity</b><br>' +
      '<span style="color:#fbbf24;">&#9679;</span> Low<br>' +
      '<span style="color:#f97316;">&#9679;</span> Medium<br>' +
      '<span style="color:#ef4444;">&#9679;</span> High';
    return div;
  };
  legend.addTo(map);

  const markerLayer = L.layerGroup().addTo(map);
  let highlight = null;

  // ── Detail panel ────────────────────────────────────────────────────────
  function showDetail(e) {
    document.getElementById('detail-body').innerHTML =
      '<h3>' + e.event_name + '</h3>' +
      '<div class="event-id">' + e.event_id + '</div>' +
      '<div class="grid grid-2" style="margin-bottom:12px;">' +
        '<div class="metric"><div class="label">Acres</div><div class="value">' + formatAcres(e.acres) + '</div></div>' +
        '<div class="metric"><div class="label">Severity</div><div class="value">' + e.severity + '</div></div>' +
        '<div class="metric"><div class="label">Max temp</div><div class="value">' +
          (e.max_temp_c === null ? '—' : e.max_temp_c + '°C') + '</div></div>' +
        '<div class="metric"><div class="label">Min humidity</div><div class="value">' +
          (e.min_humidity_pct === null ? '—' : e.min_humidity_pct + '%') + '</div></div>' +
      '</div>' +
      '<p class="caption" style="margin:0 0 10px;">Ignition: ' + e.ig_date + '</p>' +
      '<div id="detail-evi" class="chart"></div>' +
      '<p class="disclaimer" style="font-size:11px;margin:4px 0 0;">' +
        'EVI curve is an illustrative reference, not measured for this event.</p>';
    eviRecoveryChart(document.getElementById('detail-evi'), stats.evi_recovery, 180);
  }

  function clearDetail() {
    document.getElementById('detail-body').innerHTML =
      '<p class="empty">Click a fire event on the map to see its details.</p>';
  }

  // ── Render ──────────────────────────────────────────────────────────────
  function render() {
    const yearFrom = Number(document.getElementById('year-from').value);
    const yearTo = Number(document.getElementById('year-to').value);
    const sev = document.getElementById('severity').value;
    const minAcres = Number(document.getElementById('min-acres').value);
    const severities = sev === 'All' ? SEVERITY_ORDER : [sev];

    document.getElementById('year-label').textContent = yearFrom + ' – ' + yearTo;

    const rows = filterEvents(events, yearFrom, yearTo, severities, minAcres);

    markerLayer.clearLayers();
    if (highlight) { map.removeLayer(highlight); highlight = null; }
    clearDetail();

    rows.forEach(e => {
      L.circleMarker([e.latitude, e.longitude], {
        radius: markerRadius(e.acres),
        color: MAP_COLORS[e.severity] || '#6b7280',
        fillColor: MAP_COLORS[e.severity] || '#6b7280',
        fillOpacity: 0.7,
        weight: 1,
      })
        .bindTooltip(e.event_name + ' (' + e.year + ')')
        .on('click', function () {
          if (highlight) map.removeLayer(highlight);
          highlight = L.circleMarker([e.latitude, e.longitude], {
            radius: markerRadius(e.acres) + 8,
            color: '#0f172a', weight: 2, fill: false, opacity: 0.8,
          }).addTo(map);
          showDetail(e);
        })
        .addTo(markerLayer);
    });

    const s = computeMapStats(rows);
    document.getElementById('filter-count').textContent = s.event_count.toLocaleString('en-US');
    document.getElementById('stat-count').textContent = s.event_count.toLocaleString('en-US');
    document.getElementById('stat-acres').textContent = s.total_acres_fmt;
    document.getElementById('stat-high').textContent = s.pct_high_fmt;
    document.getElementById('stat-years').textContent = s.year_range;
    document.getElementById('map-empty').style.display = rows.length ? 'none' : 'block';
  }

  // Keep the two year handles from crossing over.
  const yearFromEl = document.getElementById('year-from');
  const yearToEl = document.getElementById('year-to');
  yearFromEl.addEventListener('input', () => {
    if (Number(yearFromEl.value) > Number(yearToEl.value)) yearToEl.value = yearFromEl.value;
    render();
  });
  yearToEl.addEventListener('input', () => {
    if (Number(yearToEl.value) < Number(yearFromEl.value)) yearFromEl.value = yearToEl.value;
    render();
  });
  document.getElementById('severity').addEventListener('change', render);
  document.getElementById('min-acres').addEventListener('change', render);

  render();
})();
