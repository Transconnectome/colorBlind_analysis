#!/bin/bash
# Interactive Test for RDM Metric and Normalization Analysis
# Run on server node2 in interactive mode to optimize and validate before full submission
#
# Usage:
#   ssh haba6030@node3
#   cd /scratch/connectome/haba6030/colorBlind/analysis/future_phase3_filter_optimization/pre_validation
#   bash test_metric_norm_interactive.sh

echo "=========================================="
echo "RDM Metric & Normalization - Interactive Test"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "=========================================="

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Create output directories in same folder
mkdir -p logs results

# Run minimal test: 1 CVD subject, 2 ROIs, 2 conditions (correlation + crossnobis, no norm only)
# This tests the pipeline without full computation

echo ""
echo "Running minimal test (sub-08, V1+V2, correlation+crossnobis)..."
echo "Expected runtime: ~3-5 minutes"
echo ""

# Monitor memory usage in background
(
    while true; do
        ps aux | grep -E "python.*test_rdm" | grep -v grep | awk '{print $6}' | \
        awk '{sum+=$1} END {printf "Current memory: %.1f MB\n", sum/1024}'
        sleep 10
    done
) &
MONITOR_PID=$!

# Run test with limited scope
python test_rdm_metric_and_normalization_server.py \
    --test_mode \
    --test_subjects sub-08 \
    --test_rois V1 V2 \
    --test_conditions correlation_none crossnobis_none \
    2>&1 | tee logs/interactive_test_$(date +%Y%m%d_%H%M%S).log

EXIT_CODE=$?

# Kill memory monitor
kill $MONITOR_PID 2>/dev/null

echo ""
echo "=========================================="
echo "Test completed with exit code: $EXIT_CODE"
echo "Finished: $(date)"
echo "=========================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Pipeline validated."
    echo ""
    echo "Next steps:"
    echo "1. Check results/metric_norm_test_*.json for output format"
    echo "2. Verify convergence calculations are working"
    echo "3. Submit full job: sbatch run_metric_norm_test.sbatch"
    echo ""
else
    echo ""
    echo "❌ FAILED! Check logs for errors."
    echo ""
    echo "Common issues:"
    echo "- Missing conda environment: conda activate nilearn"
    echo "- Import errors: check sklearn, scipy installed"
    echo "- Data path issues: check /scratch/connectome/.../full_dataset_C010 exists"
    echo ""
fi

# Show resource usage
echo "Peak memory usage:"
ps aux | grep "python" | head -5

echo ""
echo "Output files:"
ls -lh logs/ results/ | tail -10
