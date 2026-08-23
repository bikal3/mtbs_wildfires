/* Shared chart theme and builders. Requires plotly-basic.min.js to be loaded first. */

const T = {
  paper: '#ffffff', plot: '#f8fafc', grid: '#e2e8f0',
  font: '#374151', title: '#0f172a', card: '#f1f5f9',
};

const SEVERITY_COLORS = { Low: '#22c55e', Medium: '#f97316', High: '#ef4444' };
const MAP_COLORS      = { Low: '#fbbf24', Medium: '#f97316', High: '#ef4444' };

const PLOT_CONFIG = { displayModeBar: false, responsive: true };

/** Shared layout defaults; `over` merges per-chart overrides. */
function layout(over) {
  return Object.assign({
    paper_bgcolor: T.paper,
    plot_bgcolor: T.plot,
    font: { color: T.font },
    title: { font: { color: T.title, size: 14 } },
    margin: { l: 50, r: 20, t: 40, b: 45 },
    xaxis: { showgrid: false },
    yaxis: { gridcolor: T.grid },
    legend: { bgcolor: T.card },
  }, over || {});
}

/**
 * Fetch a JSON asset, rendering an inline error into `errorTargetId` on failure
 * rather than leaving a blank page.
 */
async function loadJSON(path, errorTargetId) {
  try {
    const res = await fetch(path);
    if (!res.ok) throw new Error(res.status + ' ' + res.statusText);
    return await res.json();
  } catch (err) {
    const target = document.getElementById(errorTargetId);
    if (target) {
      target.innerHTML =
        '<div class="error"><h3>Could not load the data</h3>' +
        '<p>Failed to fetch <code>' + path + '</code>: ' + err.message + '. ' +
        'Try a hard refresh; if it persists the deployment is incomplete.</p></div>';
    }
    return null;
  }
}

/** Continuous colour ramp used by the per-year acreage bars. */
const FIRE_SCALE = [[0, '#7f1d1d'], [0.33, '#ef4444'], [0.66, '#f97316'], [1, '#fbbf24']];

function acresByYearChart(el, rows, opts) {
  const o = opts || {};
  Plotly.newPlot(el, [{
    type: 'bar',
    x: rows.map(r => r.year),
    y: rows.map(r => r.acres),
    marker: { color: rows.map(r => r.acres), colorscale: FIRE_SCALE, showscale: false },
    hovertemplate: '%{x}<br>%{y:,.0f} acres<extra></extra>',
  }], layout({
    title: { text: o.title || '', font: { color: T.title, size: 14 } },
    height: o.height || 300,
    xaxis: { showgrid: false, title: o.xtitle || '' },
    yaxis: { gridcolor: T.grid, title: 'Acres Burned' },
  }), PLOT_CONFIG);
}

function eviRecoveryChart(el, evi, height) {
  Plotly.newPlot(el, [
    { type: 'scatter', mode: 'lines', name: 'Low severity',
      x: evi.months, y: evi.low, line: { color: '#22c55e', width: 2 } },
    { type: 'scatter', mode: 'lines', name: 'High severity',
      x: evi.months, y: evi.high, line: { color: '#ef4444', width: 2, dash: 'dash' } },
  ], layout({
    title: { text: 'EVI Recovery Timeline (3 years)', font: { color: T.title, size: 14 } },
    height: height || 300,
    xaxis: { title: 'Months after fire', showgrid: false },
    yaxis: { title: 'EVI index', gridcolor: T.grid, range: [0, 0.7] },
    shapes: [{ type: 'line', x0: 0, x1: 0, yref: 'paper', y0: 0, y1: 1,
               line: { color: '#f97316', width: 1, dash: 'dot' } }],
  }), PLOT_CONFIG);
}

function decadeSeverityChart(el, rows) {
  const decades = [...new Set(rows.map(r => r.decade))];
  const traces = ['Low', 'Medium', 'High'].map(sev => ({
    type: 'bar',
    name: sev,
    x: decades,
    y: decades.map(d => {
      const hit = rows.find(r => r.decade === d && r.severity === sev);
      return hit ? hit.count : 0;
    }),
    marker: { color: SEVERITY_COLORS[sev] },
  }));
  Plotly.newPlot(el, traces, layout({
    title: { text: 'Fire Count by Severity — Three Eras', font: { color: T.title, size: 14 } },
    barmode: 'group',
    height: 300,
    yaxis: { gridcolor: T.grid, title: 'Number of fires' },
  }), PLOT_CONFIG);
}

function tempScatterChart(el, events) {
  const withTemp = events.filter(e => e.max_temp_c !== null && e.acres > 0);
  const maxAcres = Math.max.apply(null, withTemp.map(e => e.acres));
  const traces = ['Low', 'Medium', 'High'].map(sev => {
    const pts = withTemp.filter(e => e.severity === sev);
    return {
      type: 'scatter', mode: 'markers', name: sev,
      x: pts.map(e => e.max_temp_c),
      y: pts.map(e => e.acres),
      text: pts.map(e => e.event_name),
      customdata: pts.map(e => [e.year, e.min_humidity_pct]),
      marker: {
        color: SEVERITY_COLORS[sev],
        opacity: 0.75,
        line: { width: 0.5, color: 'white' },
        size: pts.map(e => e.acres),
        sizemode: 'area',
        sizeref: maxAcres / (40 * 40),
        sizemin: 4,
      },
      hovertemplate:
        '<b>%{text}</b> (%{customdata[0]})<br>' +
        '%{x:.1f} °C · %{customdata[1]}% RH<br>%{y:,.0f} acres<extra></extra>',
    };
  });
  Plotly.newPlot(el, traces, layout({
    title: { text: 'Temperature vs Acres Burned', font: { color: T.title, size: 14 } },
    height: 400,
    xaxis: { title: 'Max Temperature (°C)', showgrid: false },
    yaxis: { title: 'Acres Burned (log scale)', type: 'log', gridcolor: T.grid },
  }), PLOT_CONFIG);
}

/** Strip plot: Plotly basic has no px.strip, so jitter the categorical axis by hand. */
function humidityStripChart(el, events) {
  const order = ['High', 'Medium', 'Low'];
  const traces = order.map((sev, i) => {
    const pts = events.filter(e => e.severity === sev && e.min_humidity_pct !== null);
    return {
      type: 'scatter', mode: 'markers', name: sev,
      x: pts.map(e => e.min_humidity_pct),
      y: pts.map(() => i + (Math.random() - 0.5) * 0.45),
      text: pts.map(e => e.event_name + ' (' + e.year + ')'),
      marker: { color: SEVERITY_COLORS[sev], size: 8, opacity: 0.7 },
      hovertemplate: '<b>%{text}</b><br>%{x}% min RH<extra></extra>',
    };
  });
  Plotly.newPlot(el, traces, layout({
    title: { text: 'Min Humidity Distribution by Severity', font: { color: T.title, size: 14 } },
    height: 280,
    showlegend: false,
    xaxis: { title: 'Min Relative Humidity (%)', showgrid: false },
    yaxis: { gridcolor: T.grid, tickmode: 'array', tickvals: [0, 1, 2], ticktext: order },
  }), PLOT_CONFIG);
}

function topFiresChart(el, rows) {
  Plotly.newPlot(el, [{
    type: 'bar',
    orientation: 'h',
    x: rows.map(r => r.acres),
    y: rows.map(r => r.label),
    marker: { color: rows.map(r => SEVERITY_COLORS[r.severity]) },
    hovertemplate: '%{y}<br>%{x:,.0f} acres<extra></extra>',
  }], layout({
    title: { text: 'Top 10 Largest Fire Events', font: { color: T.title, size: 14 } },
    height: 400,
    margin: { l: 150, r: 20, t: 40, b: 45 },
    xaxis: { title: 'Acres Burned', showgrid: false },
    yaxis: { gridcolor: T.grid, tickfont: { size: 10 } },
  }), PLOT_CONFIG);
}

const SEASON_SCALE = [[0, '#fef9c3'], [0.33, '#fbbf24'], [0.66, '#f97316'], [1, '#dc2626']];

function fireSeasonChart(el, rows) {
  const peak = rows.reduce((a, b) => (b.count > a.count ? b : a), rows[0]);
  Plotly.newPlot(el, [{
    type: 'bar',
    x: rows.map(r => r.month_name),
    y: rows.map(r => r.count),
    marker: { color: rows.map(r => r.count), colorscale: SEASON_SCALE, showscale: false },
    hovertemplate: '%{x}<br>%{y} events<extra></extra>',
  }], layout({
    title: { text: 'Fire Events by Month (peak: ' + peak.month_name + ')',
             font: { color: T.title, size: 14 } },
    height: 400,
    yaxis: { gridcolor: T.grid, title: 'Fire Events' },
  }), PLOT_CONFIG);
}

/** Fill every [data-stat="a.b"] element from a stats object. */
function fillStats(stats) {
  document.querySelectorAll('[data-stat]').forEach(el => {
    const value = el.dataset.stat.split('.').reduce((o, k) => (o == null ? o : o[k]), stats);
    if (value !== undefined && value !== null) el.textContent = value;
  });
}

/** Show the sample-data banner when the build used the 50-event CSV. */
function sampleNotice(stats, targetId) {
  if (!stats.is_sample) return;
  document.getElementById(targetId).insertAdjacentHTML('afterbegin',
    '<div class="note"><strong>Sample dataset</strong> — showing ' + stats.event_count +
    ' representative events, not the full record.</div>');
}
