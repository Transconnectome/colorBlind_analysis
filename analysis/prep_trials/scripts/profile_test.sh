#!/bin/bash
################################################################################
# Resource Profiling Script
#
# Usage:
#   /usr/bin/time -v bash profile_test.sh 2>&1 | tee time.log
#
# Purpose: Measure actual resource usage before submitting array jobs
################################################################################

echo "=== Resource Profiling Started ==="
echo "Time: $(date)"
echo ""

# Run the actual script
bash test_method3_single_subject.sh

echo ""
echo "=== Resource Profiling Completed ==="
echo "Time: $(date)"
echo ""
echo "Analysis:"
echo "1. Check 'Maximum resident set size' in time.log"
echo "2. Check 'Percent of CPU' for CPU efficiency"
echo "3. Request memory = (Max RSS × 1.5) for safety"
echo "4. Optimize --cpus-per-task based on actual CPU%"
