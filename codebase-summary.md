# Pingmo — Codebase Summary

## Project Overview

**Pingmo** is a lightweight, two-part tool for monitoring and visualizing network ping latency. It has no server component — currently it runs entirely via a local Python script + a static HTML file.

```
pingmo/
├── monitor.py             # Python CLI — runs ping, collects data, saves JSON
├── ping_visualizer.html   # Static HTML page — loads JSON and renders charts
└── README.md              # Usage documentation
```

---

## `monitor.py` — Ping Data Collector

### Purpose
A cross-platform Python CLI that continuously pings a target host (default: `1.1.1.1`) at a configurable interval, collects results in memory, and saves a structured JSON file on exit (Ctrl+C).

### Key Class: `PingMonitor`

| Attribute | Default | Description |
|---|---|---|
| `target` | `1.1.1.1` | Host/IP to ping |
| `interval` | `1.0s` | Delay between pings |
| `output_file` | auto-named | `ping_results_YYYY-MM-DD-HH.MM.json` |

### CLI Arguments

```bash
python3 monitor.py [-t TARGET] [-i INTERVAL] [-o OUTPUT_FILE]
```

### Core Methods

| Method | Role |
|---|---|
| `ping_once()` | Calls OS `ping` via `subprocess`, parses latency from stdout with regex |
| `monitor()` | Main loop — calls `ping_once()`, appends to `self.results`, prints live output |
| `save_results()` | Computes summary statistics, writes final JSON |
| `calculate_spike_statistics()` | Multi-method spike analysis (fixed thresholds, 2σ/3σ, IQR, median×3) |
| `signal_handler()` | Catches `SIGINT` (Ctrl+C), calls `save_results()`, exits cleanly |

### Platform Handling
- Detects Windows vs macOS/Linux via `sys.platform`
- Adjusts `ping` flags accordingly (`-n`/`-c` for count, `-w`/`-W` for timeout)
- Uses regex `time[=<]([0-9\.]+)` to parse latency from both platform output formats

### Output: JSON Schema

```jsonc
{
  "summary": {
    "monitoring_started": "ISO8601",
    "monitoring_ended": "ISO8601",
    "total_pings": 120,
    "successful_pings": 118,
    "failed_pings": 2,
    "success_rate": 98.3,
    "target": "1.1.1.1",
    "interval_seconds": 1.0,
    "avg_latency_ms": 14.2,
    "median_latency_ms": 13.5,
    "min_latency_ms": 8.1,
    "max_latency_ms": 210.0,
    "std_dev_ms": 18.4,
    "p95_latency_ms": 32.0,
    "p99_latency_ms": 178.0,
    "spike_analysis": {
      "spikes_above_50ms":  { "count": 3, "percentage": 2.5, "values": [...] },
      "spikes_above_100ms": { ... },
      "spikes_above_150ms": { ... },
      "spikes_above_200ms": { ... },
      "spikes_above_300ms": { ... },
      "spikes_above_500ms": { ... },
      "statistical_outliers": {
        "two_std_dev":   { "threshold_ms": ..., "count": ..., "percentage": ..., "values": [...] },
        "three_std_dev": { ... },
        "iqr_method":    { ... },
        "median_3x":     { ... }
      },
      "video_conferencing_quality": {
        "excellent_0_20ms":      { "count": ..., "percentage": ... },
        "good_20_50ms":          { ... },
        "acceptable_50_100ms":   { ... },
        "poor_100_200ms":        { ... },
        "very_poor_above_200ms": { ... }
      }
    }
  },
  "results": [
    { "timestamp": "ISO8601", "target": "1.1.1.1", "latency_ms": 12.3, "status": "success" },
    { "timestamp": "ISO8601", "target": "1.1.1.1", "latency_ms": null,  "status": "timeout" }
  ]
}
```

---

## `ping_visualizer.html` — Visualization Dashboard

### Purpose
A self-contained, single-file HTML page that accepts a JSON file (from `monitor.py`) and renders an interactive analytics dashboard using **Chart.js 3.9.1** (loaded via CDN).

### UI Structure

| Section | Content |
|---|---|
| **Upload area** | Drag-and-drop or file picker — accepts `.json` only |
| **Stats grid** | Stat cards: start/end time, duration, total pings, success rate, avg/median/p95 latency, spikes >100ms, excellent %, poor % |
| **Latency Over Time** | Line chart — all ping data points, colored per quality tier |
| **Latency Distribution** | Bar chart (histogram) — bins: 0–10, 10–20, …, 500–1000ms |
| **Video Conferencing Quality** | Doughnut chart — Excellent / Good / Acceptable / Poor / Very Poor breakdown |
| **Spike Analysis** | Bar chart — spike counts at thresholds 50/100/150/200/300/500ms |

### Quality Color Coding (consistent across all charts and stats)

| Tier | Range | Color |
|---|---|---|
| Excellent | 0–20ms | `#28a745` (green) |
| Good | 20–50ms | `#17a2b8` (teal) |
| Acceptable | 50–100ms | `#ffc107` (yellow) |
| Poor | 100–200ms | `#fd7e14` (orange) |
| Very Poor | >200ms | `#dc3545` (red) |

### JS Architecture
- No frameworks — plain vanilla JS
- Chart instances stored in `charts` object (`charts.timeline`, `.distribution`, `.quality`, `.spike`) and destroyed before re-render if a new file is loaded
- `handleFile(file)` → `FileReader` → `JSON.parse` → `visualizeData(data)`
- `visualizeData()` validates `data.summary` and `data.results` exist, then calls individual chart builder functions

### Styling
- CSS-only, no external stylesheet
- Design: glassmorphism card style, purple gradient background (`#667eea` → `#764ba2`), hover animations, responsive grid

---

## Current Data Flow

```
User runs monitor.py (terminal)
    └─> OS ping command (subprocess)
        └─> Parses latency
            └─> Appends to results[]
                └─> On Ctrl+C: computes stats → saves .json file

User opens ping_visualizer.html in browser
    └─> Uploads .json file via drag-drop or picker
        └─> JS reads & parses JSON
            └─> Renders 4 Chart.js charts + stat cards
```

---

## Planned Migration: Web App

The goal is to convert this into a **fully browser-based web app** — no Python install or local file required. Key changes needed:

### What changes

| Current | Web App Target |
|---|---|
| `monitor.py` runs OS `ping` via subprocess | Browser runs **latency measurement** (via `fetch` timing or a relay backend) |
| Results saved as `.json` file | Results held in-memory, streamed live in the browser |
| User uploads JSON to visualizer | Visualizer updates in **real-time** as pings complete |
| Two separate files, manual workflow | Single URL, unified UX |

### Key technical consideration
Browsers cannot send raw ICMP packets (ping). To monitor connectivity directly from the user's perspective (client-side), the app must use web-compatible alternatives:
1. **HTTP Latency via `fetch()` or `HEAD` requests**: Measuring the Round Trip Time (RTT) of a small request to the target server. 
2. **Resource Timing API (`performance.now()`)**: Using high-resolution timestamps to measure the duration of network requests to an endpoint for precise metrics.
3. **Asset Load Timing (Image/Script)**: Timing how long a small asset takes to load from the target server. This is a common method for measuring latency to third-party endpoints (like CDNs) where CORS might be restricted.

### What stays the same
- The JSON data schema (`summary` + `results[]`) can be reused as the in-memory data model
- All Chart.js visualization logic from `ping_visualizer.html` can be ported directly
- Quality tier thresholds and spike analysis logic remain identical
- The stats computation from `save_results()` / `calculate_spike_statistics()` can be translated to JS or kept on a backend
