#!/bin/bash
# Local Resource Test for C010 SRM Analysis
#
# This script profiles resource usage (memory, CPU) with a single ROI test
# to determine safe SLURM settings before full execution.
#
# Usage:
#   cd /path/to/SRM/
#   bash test_c010_srm_resources.sh

set -e

echo "=================================="
echo "C010 SRM Resource Profiling Test"
echo "=================================="
echo ""
echo "Testing V2 (representative ROI) with resource monitoring..."
echo "This will measure peak memory and CPU usage to set SLURM limits."
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Activate srm environment
echo "Activating conda environment: srm"
source ~/.bashrc
conda activate srm
echo "Environment: $CONDA_DEFAULT_ENV"
echo ""

# Run with resource monitoring
/usr/bin/time -v python evaluate_srm_c010_between_subject.py --roi V2 > test_resource.log 2>&1

echo ""
echo "=== Resource Usage Summary ==="
echo ""
echo "Peak Memory:"
grep "Maximum resident set size" test_resource.log | awk '{print $6/1024 " MB"}'

echo ""
echo "CPU Usage:"
grep "Percent of CPU" test_resource.log

echo ""
echo "Wall Time:"
grep "Elapsed (wall clock) time" test_resource.log

echo ""
echo "=== SLURM Recommendations ==="
echo ""

# Parse peak memory (KB to MB)
PEAK_MEM_KB=$(grep "Maximum resident set size" test_resource.log | awk '{print $6}')
PEAK_MEM_MB=$((PEAK_MEM_KB / 1024))
SAFE_MEM_MB=$((PEAK_MEM_MB * 2))  # 2x safety margin

echo "Measured peak memory: ${PEAK_MEM_MB} MB"
echo ""

if [ $PEAK_MEM_MB -lt 8192 ]; then
    echo "Recommendation: --mem=16G (conservative)"
    echo "Concurrency: --array=1-4%2 (max 2 concurrent, 32GB total)"
elif [ $PEAK_MEM_MB -lt 16384 ]; then
    echo "Recommendation: --mem=32G (moderate)"
    echo "Concurrency: --array=1-4%2 (max 2 concurrent, 64GB total)"
else
    echo "Recommendation: --mem=48G (high memory)"
    echo "Concurrency: --array=1-4%2 (max 2 concurrent, 96GB total)"
fi

echo ""
echo "CPU Recommendation: --cpus-per-task=2 (SRM is memory-bound)"
echo ""
echo "Update sbatch/run_c010_between_subject.sbatch with these settings."
echo ""
echo "Full log saved to: test_resource.log"
