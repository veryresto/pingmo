#!/usr/bin/env python3
"""
Ping Latency Monitor for macOS
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
        try:
            # Use ping command with 1 packet, 2 second timeout
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "2000", self.target],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse ping output for latency
                # Look for pattern like "time=12.345 ms"
                match = re.search(r'time=(\d+\.?\d*) ms', result.stdout)
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
            summary.update({
                "avg_latency_ms": sum(latencies) / len(latencies),
                "min_latency_ms": min(latencies),
                "max_latency_ms": max(latencies),
                "median_latency_ms": sorted(latencies)[len(latencies)//2]
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
                print(f"   Min/Max latency: {summary['min_latency_ms']:.2f}ms / {summary['max_latency_ms']:.2f}ms")
            
        except IOError as e:
            print(f"❌ Error saving results: {e}")

def main():
    """Main function with command line argument parsing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor ping latency on macOS")
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