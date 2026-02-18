#!/bin/bash
# Server Resource Test for C010 SRM Analysis
#
# Run this on the server (interactive mode) to measure actual resource usage
# before submitting SLURM array jobs.
#
# Usage:
#   ssh haba6030@node2
#   cd /scratch/connectome/haba6030/colorBlind/analysis/validation/SRM
#   bash test_c010_srm_server.sh

set -e

echo "====================================="
echo "C010 SRM Server Resource Test"
echo "====================================="
echo ""

# Activate environment
source ~/.bashrc
conda activate nilearn

echo "Testing V2 with resource monitoring..."
echo "This determines safe SLURM array job limits."
echo ""

# Run with resource monitoring
/usr/bin/time -v python evaluate_srm_c010_between_subject.py --roi V2 > test_server_resource.log 2>&1

echo ""
echo "=== Server Resource Usage ==="
echo ""
echo "Peak Memory:"
grep "Maximum resident set size" test_server_resource.log | awk '{print $6/1024/1024 " GB"}'

echo ""
echo "CPU Usage:"
grep "Percent of CPU" test_server_resource.log

echo ""
echo "Wall Time:"
grep "Elapsed (wall clock) time" test_server_resource.log

echo ""
echo "=== Node Availability Check ==="
ssh node2 free -h 2>/dev/null || echo "node2 free memory: (check manually)"
ssh node4 free -h 2>/dev/null || echo "node4 free memory: (check manually)"

echo ""
echo "=== Current Jobs ==="
squeue -w node2,node4

echo ""
echo "Full log: test_server_resource.log"
echo ""
echo "Based on these results, update --mem and --array settings in sbatch file."
