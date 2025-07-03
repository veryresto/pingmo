# Ping Latency Monitor & Visualizer

This project provides a set of tools to continuously monitor ping latency, save the results, and visualize them in a comprehensive and user-friendly way.

## Features

- **Continuous Monitoring:** The `ping_monitor.py` script continuously pings a target host and records the latency.
- **Graceful Shutdown:** Press `Ctrl+C` to stop the monitor and save the collected data.
- **Detailed Statistics:** The script calculates and displays detailed statistics upon completion, including:
    - Average, median, min, and max latency
    - 95th and 99th percentile latency
    - Standard deviation
    - Spike analysis using various methods
    - Video conferencing quality assessment
- **JSON Output:** The results are saved in a timestamped JSON file for easy parsing and analysis.
- **Interactive Visualization:** The `ping_visualizer.html` provides an interactive dashboard to visualize the ping results.
    - Drag and drop your JSON file to load the data.
    - View latency over time, latency distribution, video conferencing quality, and spike analysis charts.

## How to Use

### 1. Monitor Ping Latency

Run the `ping_monitor.py` script from your terminal:

```bash
python3 ping_monitor.py [OPTIONS]
```

**Options:**

- `-t`, `--target`: The target IP address or hostname to ping (default: `1.1.1.1`).
- `-i`, `--interval`: The ping interval in seconds (default: `1.0`).
- `-o`, `--output`: The name of the output file (default: `ping_results_YYYY-MM-DD-HH.MM.json`).

**Example:**

```bash
python3 ping_monitor.py -t 8.8.8.8 -i 0.5
```

This will start monitoring the latency to `8.8.8.8` every `0.5` seconds. Press `Ctrl+C` to stop and save the results.

### 2. Visualize the Results

1.  Open the `ping_visualizer.html` file in your web browser.
2.  Drag and drop the generated JSON file onto the upload area, or click to browse for the file.
3.  The dashboard will automatically load and display the charts and statistics.

## Interpreting the Results

The visualizer provides several charts to help you understand your network's performance:

- **Latency Over Time:** This chart shows the ping latency for each individual ping, allowing you to see when spikes or timeouts occurred.
- **Latency Distribution:** This histogram shows how many pings fall into different latency ranges, giving you an idea of the overall consistency of your connection.
- **Video Conferencing Quality:** This chart breaks down the pings into categories based on their suitability for real-time applications like video calls.
- **Spike Analysis:** This chart shows the number of pings that exceeded certain latency thresholds, helping you to identify significant latency spikes.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
