#!/usr/bin/env python3
"""
Memory Profiler for colorBlind Analysis Pipeline

Monitors and reports memory usage for different phases to optimize SLURM settings.
"""

import psutil
import time
import argparse
import json
import subprocess
from pathlib import Path
from datetime import datetime
import sys


class MemoryProfiler:
    """Monitor memory usage during script execution"""

    def __init__(self, output_file=None, interval=5):
        """
        Args:
            output_file: Path to save profiling results (JSON)
            interval: Sampling interval in seconds
        """
        self.output_file = output_file
        self.interval = interval
        self.samples = []
        self.process = psutil.Process()
        self.start_time = time.time()

    def get_memory_info(self):
        """Get current memory information"""
        mem = psutil.virtual_memory()
        process_mem = self.process.memory_info()

        return {
            'timestamp': time.time() - self.start_time,
            'datetime': datetime.now().isoformat(),
            # System memory
            'system_total_gb': mem.total / (1024**3),
            'system_available_gb': mem.available / (1024**3),
            'system_used_gb': mem.used / (1024**3),
            'system_percent': mem.percent,
            # Process memory
            'process_rss_gb': process_mem.rss / (1024**3),  # Resident Set Size
            'process_vms_gb': process_mem.vms / (1024**3),  # Virtual Memory Size
            # Children processes
            'children_count': len(self.process.children(recursive=True)),
        }

    def sample(self):
        """Take a memory sample"""
        info = self.get_memory_info()
        self.samples.append(info)
        return info

    def print_current(self):
        """Print current memory usage"""
        info = self.sample()
        print(f"\n[{info['datetime']}]")
        print(f"  System: {info['system_used_gb']:.2f}GB / {info['system_total_gb']:.2f}GB "
              f"({info['system_percent']:.1f}%)")
        print(f"  Process RSS: {info['process_rss_gb']:.2f}GB")
        print(f"  Process VMS: {info['process_vms_gb']:.2f}GB")
        print(f"  Children: {info['children_count']}")

    def get_peak_memory(self):
        """Get peak memory usage"""
        if not self.samples:
            return None

        peak_rss = max(s['process_rss_gb'] for s in self.samples)
        peak_system = max(s['system_used_gb'] for s in self.samples)

        return {
            'peak_process_rss_gb': peak_rss,
            'peak_system_used_gb': peak_system,
            'num_samples': len(self.samples),
        }

    def save_report(self):
        """Save profiling report"""
        if not self.output_file:
            return

        peak = self.get_peak_memory()

        report = {
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'duration_seconds': time.time() - self.start_time,
            'sampling_interval': self.interval,
            'peak_memory': peak,
            'samples': self.samples,
            'recommendations': self.get_recommendations(peak),
        }

        output_path = Path(self.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n✓ Memory profile saved to: {output_path}")

    def get_recommendations(self, peak):
        """Generate SLURM memory recommendations"""
        if not peak:
            return {}

        peak_rss = peak['peak_process_rss_gb']

        # Add 20% buffer for safety
        recommended_mem = peak_rss * 1.2

        # Round up to nearest 5GB
        recommended_mem = ((int(recommended_mem) // 5) + 1) * 5

        return {
            'measured_peak_gb': peak_rss,
            'recommended_mem_gb': recommended_mem,
            'buffer_percent': 20,
            'slurm_setting': f'#SBATCH --mem={recommended_mem}G',
        }

    def print_summary(self):
        """Print summary statistics"""
        if not self.samples:
            print("No samples collected")
            return

        peak = self.get_peak_memory()
        recs = self.get_recommendations(peak)

        print("\n" + "="*70)
        print("MEMORY PROFILING SUMMARY")
        print("="*70)
        print(f"Duration: {time.time() - self.start_time:.1f}s")
        print(f"Samples: {peak['num_samples']}")
        print(f"\nPeak Memory Usage:")
        print(f"  Process RSS: {peak['peak_process_rss_gb']:.2f}GB")
        print(f"  System Total: {peak['peak_system_used_gb']:.2f}GB")
        print(f"\nRecommendations:")
        print(f"  Measured Peak: {recs['measured_peak_gb']:.2f}GB")
        print(f"  Recommended (with {recs['buffer_percent']}% buffer): {recs['recommended_mem_gb']}GB")
        print(f"  SLURM Setting: {recs['slurm_setting']}")
        print("="*70)


def profile_command(cmd, output_file, interval=5):
    """
    Profile a command execution

    Args:
        cmd: Command to execute (list)
        output_file: Path to save profile
        interval: Sampling interval
    """
    import subprocess
    import threading

    profiler = MemoryProfiler(output_file, interval)

    print(f"Starting memory profiling...")
    print(f"Command: {' '.join(cmd)}")
    print(f"Sampling interval: {interval}s")
    print(f"Output: {output_file}")

    # Start the command
    proc = subprocess.Popen(cmd)

    # Monitor in a separate thread
    def monitor():
        while proc.poll() is None:
            profiler.print_current()
            time.sleep(interval)
        # Final sample
        profiler.print_current()

    monitor_thread = threading.Thread(target=monitor)
    monitor_thread.start()

    # Wait for completion
    proc.wait()
    monitor_thread.join()

    # Save and print summary
    profiler.save_report()
    profiler.print_summary()

    return proc.returncode


def main():
    parser = argparse.ArgumentParser(
        description='Memory profiler for colorBlind analysis pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Profile a single subject ROI pipeline
  python memory_profiler.py profile "python roi_pipeline_selected_1202used.py 01" --output profiles/roi_sub01.json

  # Profile baseline decoding
  python memory_profiler.py profile "python fir_reconstruction_BH2009_system_clean.py --subject 01 --roi V1" --output profiles/baseline_sub01_V1.json

  # Monitor an existing SLURM job
  python memory_profiler.py monitor --job-id 12345 --interval 10
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Profile command
    profile_parser = subparsers.add_parser('profile', help='Profile a command execution')
    profile_parser.add_argument('cmd', help='Command to execute (in quotes)')
    profile_parser.add_argument('--output', '-o', required=True, help='Output JSON file')
    profile_parser.add_argument('--interval', '-i', type=int, default=5, help='Sampling interval (seconds)')

    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor an existing job')
    monitor_parser.add_argument('--job-id', required=True, help='SLURM job ID')
    monitor_parser.add_argument('--interval', '-i', type=int, default=10, help='Sampling interval (seconds)')
    monitor_parser.add_argument('--output', '-o', help='Output file (optional)')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze existing profile')
    analyze_parser.add_argument('profile_file', help='Profile JSON file to analyze')

    args = parser.parse_args()

    if args.command == 'profile':
        # Split command string
        import shlex
        cmd_list = shlex.split(args.cmd)
        return profile_command(cmd_list, args.output, args.interval)

    elif args.command == 'monitor':
        print(f"Monitoring SLURM job {args.job_id}...")
        print("Use: sstat -j {job_id} --format=JobID,MaxRSS,MaxVMSize,AveCPU")
        print("Or: watch -n 10 'sstat -j {job_id} --format=JobID,MaxRSS,MaxVMSize,AveCPU'")
        return 0

    elif args.command == 'analyze':
        with open(args.profile_file) as f:
            report = json.load(f)

        peak = report['peak_memory']
        recs = report['recommendations']

        print("\n" + "="*70)
        print(f"ANALYSIS: {args.profile_file}")
        print("="*70)
        print(f"Duration: {report['duration_seconds']:.1f}s")
        print(f"Samples: {peak['num_samples']}")
        print(f"\nPeak Memory:")
        print(f"  Process RSS: {peak['peak_process_rss_gb']:.2f}GB")
        print(f"  System Used: {peak['peak_system_used_gb']:.2f}GB")
        print(f"\nRecommendations:")
        print(f"  {recs['slurm_setting']}")
        print("="*70)
        return 0

    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
