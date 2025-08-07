#!/usr/bin/env python3
"""
Cross-platform Ping Latency Monitor
Continuously monitors ping latency and saves results to a file.
Press Ctrl+C to stop monitoring and save results.
"""

import subprocess
import time
import json
import signal
import sys
from datetime import datetime
import re

class PingMonitor:
    def __init__(self, target="1.1.1.1", interval=1, output_file=None):
        self.target = target
        self.interval = interval
        self.start_time = datetime.now()
        
        # Generate filename with datetime if not provided
        if output_file is None:
            timestamp = self.start_time.strftime("%Y-%m-%d-%H.%M")
            self.output_file = f"ping_results_{timestamp}.json"
        else:
            self.output_file = output_file
            
        self.results = []
        self.running = True
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        print(f"\n\nStopping monitor... Saving {len(self.results)} results to {self.output_file}")
        self.running = False
        self.save_results()
        sys.exit(0)
    
    def ping_once(self):
        """Execute a single ping and return latency in ms"""
        is_windows = sys.platform.startswith('win')

        # Platform-specific ping command arguments
        count_param = "-n" if is_windows else "-c"
        # -W is timeout in ms on macOS, -w is timeout in ms on Windows.
        # On Linux, -W is timeout in seconds. The script was written for macOS,
        # so we assume the timeout value is in milliseconds.
        timeout_param = "-w" if is_windows else "-W"
        
        command = ["ping", count_param, "1", timeout_param, "2000", self.target]
        
        try:
            kwargs = {'capture_output': True, 'text': True, 'timeout': 5}
            if is_windows:
                # 0x08000000 is subprocess.CREATE_NO_WINDOW.
                # This flag prevents the console window from popping up on Windows.
                kwargs['creationflags'] = 0x08000000

            result = subprocess.run(command, **kwargs)
            
            if result.returncode == 0:
                # Parse ping output for latency
                # macOS/Linux: "time=12.345 ms" | Windows: "time=12ms" or "time<1ms"
                match = re.search(r'time[=<]([0-9\.]+)', result.stdout)
                if match:
                    return float(match.group(1))
            
            return None
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return None
    
    def monitor(self):
        """Main monitoring loop"""
        print(f"Starting ping monitoring to {self.target}")
        print(f"Interval: {self.interval} seconds")
        print(f"Output file: {self.output_file}")
        print("Press Ctrl+C to stop and save results\n")
        
        consecutive_failures = 0
        
        while self.running:
            timestamp = datetime.now().isoformat()
            latency = self.ping_once()
            
            if latency is not None:
                self.results.append({
                    "timestamp": timestamp,
                    "target": self.target,
                    "latency_ms": latency,
                    "status": "success"
                })
                print(f"{timestamp}: {self.target} - {latency:.2f}ms")
                consecutive_failures = 0
            else:
                self.results.append({
                    "timestamp": timestamp,
                    "target": self.target,
                    "latency_ms": None,
                    "status": "timeout"
                })
                consecutive_failures += 1
                print(f"{timestamp}: {self.target} - TIMEOUT")
                
                # Warning if too many consecutive failures
                if consecutive_failures >= 5:
                    print(f"⚠️  Warning: {consecutive_failures} consecutive timeouts")
            
            time.sleep(self.interval)
    
    def save_results(self):
        """Save results to JSON file"""
        if not self.results:
            print("No results to save.")
            return
        
        # Calculate summary statistics
        successful_pings = [r for r in self.results if r["status"] == "success"]
        latencies = [r["latency_ms"] for r in successful_pings]
        
        summary = {
            "monitoring_started": self.start_time.isoformat(),
            "monitoring_ended": datetime.now().isoformat(),
            "total_pings": len(self.results),
            "successful_pings": len(successful_pings),
            "failed_pings": len(self.results) - len(successful_pings),
            "success_rate": len(successful_pings) / len(self.results) * 100 if self.results else 0,
            "target": self.target,
            "interval_seconds": self.interval
        }
        
        if latencies:
            sorted_latencies = sorted(latencies)
            n = len(latencies)
            
            # Basic statistics
            avg_latency = sum(latencies) / n
            median_latency = sorted_latencies[n//2] if n % 2 == 1 else (sorted_latencies[n//2-1] + sorted_latencies[n//2]) / 2
            
            # Percentile calculations
            p95_latency = sorted_latencies[int(0.95 * n)] if n > 0 else 0
            p99_latency = sorted_latencies[int(0.99 * n)] if n > 0 else 0
            
            # Standard deviation
            variance = sum((x - avg_latency) ** 2 for x in latencies) / n
            std_dev = variance ** 0.5
            
            # Spike detection using multiple methods
            spike_stats = self.calculate_spike_statistics(latencies, avg_latency, median_latency, std_dev)
            
            summary.update({
                "avg_latency_ms": avg_latency,
                "median_latency_ms": median_latency,
                "min_latency_ms": min(latencies),
                "max_latency_ms": max(latencies),
                "std_dev_ms": std_dev,
                "p95_latency_ms": p95_latency,
                "p99_latency_ms": p99_latency,
                "spike_analysis": spike_stats
            })
        
        # Save to file
        output_data = {
            "summary": summary,
            "results": self.results
        }
        
        try:
            with open(self.output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"✅ Results saved to {self.output_file}")
            
            # Print summary
            print(f"\n📊 Summary:")
            print(f"   Total pings: {summary['total_pings']}")
            print(f"   Success rate: {summary['success_rate']:.1f}%")
            if latencies:
                print(f"   Average latency: {summary['avg_latency_ms']:.2f}ms")
                print(f"   Median latency: {summary['median_latency_ms']:.2f}ms")
                print(f"   Min/Max latency: {summary['min_latency_ms']:.2f}ms / {summary['max_latency_ms']:.2f}ms")
                print(f"   95th percentile: {summary['p95_latency_ms']:.2f}ms")
                print(f"   99th percentile: {summary['p99_latency_ms']:.2f}ms")
                print(f"   Standard deviation: {summary['std_dev_ms']:.2f}ms")
                
                # Spike summary
                spike_stats = summary['spike_analysis']
                print(f"\n🔥 Spike Analysis:")
                print(f"   Spikes > 100ms: {spike_stats['spikes_above_100ms']['count']} ({spike_stats['spikes_above_100ms']['percentage']:.1f}%)")
                print(f"   Spikes > 200ms: {spike_stats['spikes_above_200ms']['count']} ({spike_stats['spikes_above_200ms']['percentage']:.1f}%)")
                print(f"   Statistical outliers (2σ): {spike_stats['statistical_outliers']['two_std_dev']['count']} ({spike_stats['statistical_outliers']['two_std_dev']['percentage']:.1f}%)")
                
                # Video conferencing quality
                quality = spike_stats['video_conferencing_quality']
                print(f"\n📹 Video Conferencing Quality:")
                print(f"   Excellent (0-20ms): {quality['excellent_0_20ms']['percentage']:.1f}%")
                print(f"   Good (20-50ms): {quality['good_20_50ms']['percentage']:.1f}%")
                print(f"   Acceptable (50-100ms): {quality['acceptable_50_100ms']['percentage']:.1f}%")
                print(f"   Poor (100-200ms): {quality['poor_100_200ms']['percentage']:.1f}%")
                print(f"   Very Poor (>200ms): {quality['very_poor_above_200ms']['percentage']:.1f}%")
            
        except IOError as e:
            print(f"❌ Error saving results: {e}")
    
    def calculate_spike_statistics(self, latencies, avg_latency, median_latency, std_dev):
        """Calculate comprehensive spike statistics"""
        spike_stats = {}
        
        # Method 1: Fixed thresholds (good for video conferencing)
        thresholds = [50, 100, 150, 200, 300, 500]
        for threshold in thresholds:
            spikes = [x for x in latencies if x > threshold]
            spike_stats[f"spikes_above_{threshold}ms"] = {
                "count": len(spikes),
                "percentage": (len(spikes) / len(latencies)) * 100,
                "values": spikes if len(spikes) <= 10 else spikes[-10:]  # Last 10 spikes if too many
            }
        
        # Method 2: Statistical outliers (2 standard deviations)
        outlier_threshold_2sd = avg_latency + (2 * std_dev)
        outliers_2sd = [x for x in latencies if x > outlier_threshold_2sd]
        
        # Method 3: Statistical outliers (3 standard deviations)
        outlier_threshold_3sd = avg_latency + (3 * std_dev)
        outliers_3sd = [x for x in latencies if x > outlier_threshold_3sd]
        
        # Method 4: IQR method (Interquartile Range)
        sorted_latencies = sorted(latencies)
        n = len(latencies)
        q1 = sorted_latencies[n//4]
        q3 = sorted_latencies[3*n//4]
        iqr = q3 - q1
        iqr_threshold = q3 + (1.5 * iqr)
        iqr_outliers = [x for x in latencies if x > iqr_threshold]
        
        # Method 5: Median-based spike detection
        median_threshold = median_latency * 3  # 3x median
        median_spikes = [x for x in latencies if x > median_threshold]
        
        # Add statistical methods to results
        spike_stats.update({
            "statistical_outliers": {
                "two_std_dev": {
                    "threshold_ms": outlier_threshold_2sd,
                    "count": len(outliers_2sd),
                    "percentage": (len(outliers_2sd) / len(latencies)) * 100,
                    "values": outliers_2sd if len(outliers_2sd) <= 10 else outliers_2sd[-10:]
                },
                "three_std_dev": {
                    "threshold_ms": outlier_threshold_3sd,
                    "count": len(outliers_3sd),
                    "percentage": (len(outliers_3sd) / len(latencies)) * 100,
                    "values": outliers_3sd if len(outliers_3sd) <= 10 else outliers_3sd[-10:]
                },
                "iqr_method": {
                    "threshold_ms": iqr_threshold,
                    "count": len(iqr_outliers),
                    "percentage": (len(iqr_outliers) / len(latencies)) * 100,
                    "values": iqr_outliers if len(iqr_outliers) <= 10 else iqr_outliers[-10:]
                },
                "median_3x": {
                    "threshold_ms": median_threshold,
                    "count": len(median_spikes),
                    "percentage": (len(median_spikes) / len(latencies)) * 100,
                    "values": median_spikes if len(median_spikes) <= 10 else median_spikes[-10:]
                }
            }
        })
        
        # Quality assessment for video conferencing
        excellent_count = len([x for x in latencies if x <= 20])
        good_count = len([x for x in latencies if 20 < x <= 50])
        acceptable_count = len([x for x in latencies if 50 < x <= 100])
        poor_count = len([x for x in latencies if 100 < x <= 200])
        very_poor_count = len([x for x in latencies if x > 200])
        
        spike_stats["video_conferencing_quality"] = {
            "excellent_0_20ms": {"count": excellent_count, "percentage": (excellent_count / len(latencies)) * 100},
            "good_20_50ms": {"count": good_count, "percentage": (good_count / len(latencies)) * 100},
            "acceptable_50_100ms": {"count": acceptable_count, "percentage": (acceptable_count / len(latencies)) * 100},
            "poor_100_200ms": {"count": poor_count, "percentage": (poor_count / len(latencies)) * 100},
            "very_poor_above_200ms": {"count": very_poor_count, "percentage": (very_poor_count / len(latencies)) * 100}
        }
        
        return spike_stats

def main():
    """Main function with command line argument parsing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor ping latency.")
    parser.add_argument("--target", "-t", default="1.1.1.1", 
                       help="Target IP address or hostname (default: 1.1.1.1)")
    parser.add_argument("--interval", "-i", type=float, default=1.0,
                       help="Ping interval in seconds (default: 1.0)")
    parser.add_argument("--output", "-o", default=None,
                       help="Output file name (default: ping_results_YYYY-MM-DD-HH.MM.json)")
    
    args = parser.parse_args()
    
    # Create and start monitor
    monitor = PingMonitor(
        target=args.target,
        interval=args.interval,
        output_file=args.output
    )
    
    try:
        monitor.monitor()
    except KeyboardInterrupt:
        # This should be handled by signal handler, but just in case
        monitor.save_results()

if __name__ == "__main__":
    main()