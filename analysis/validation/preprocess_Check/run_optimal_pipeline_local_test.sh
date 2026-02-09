#!/bin/bash
# Test Optimal Pipeline (C010 + P3) Locally

echo "=================================================================="
echo "Optimal Pipeline Test: C010 + P3"
echo "=================================================================="

# Set paths
SCRIPT_DIR="/scratch/connectome/haba6030/colorBlind/analysis/validation/preprocess_detrend_temp"
cd $SCRIPT_DIR

# Activate conda
source ~/.bashrc
conda activate nilearn

echo ""
echo "Environment: $(which python)"
echo "Working directory: $(pwd)"
echo ""

# Test configuration
TEST_SUBJECT="02"
TEST_ROI="V1"

echo "Test configuration:"
echo "  Subject: sub-${TEST_SUBJECT}"
echo "  ROI: ${TEST_ROI}"
echo "  Pipeline: C010 (2nd drift) + P3 (Motion/Tissue + WM aCompCor)"
echo ""

# Memory monitoring
(while true; do
    echo "[$(date +%H:%M:%S)] Memory: $(free -h | grep Mem | awk '{print $3"/"$2}')"
    sleep 30
done) > memory_monitor_optimal_test.log 2>&1 &
MONITOR_PID=$!

echo "Memory monitor PID: $MONITOR_PID"
echo ""

# Run test
echo "Running pipeline..."
echo ""

python optimal_pipeline_C010_P3.py \
    --subject $TEST_SUBJECT \
    --roi $TEST_ROI

EXIT_CODE=$?

# Stop memory monitor
kill $MONITOR_PID 2>/dev/null

echo ""
echo "=================================================================="
echo "Test completed with exit code: $EXIT_CODE"
echo "=================================================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✓ SUCCESS!"
    echo ""
    echo "Results saved to:"
    echo "  /scratch/connectome/haba6030/colorBlind/derivatives/optimal_C010_P3/sub-${TEST_SUBJECT}/${TEST_ROI}/"
    echo ""
    echo "Files:"
    echo "  - amplitudes_raw.npy"
    echo "  - amplitudes_procrustes.npy"
    echo "  - procrustes_disparities.npy"
    echo "  - roi_hrf.npy"
    echo "  - roi_hrf_deriv.npy"
    echo "  - metrics.json"
    echo "  - config.json"
    echo ""
    echo "Check memory usage:"
    echo "  tail memory_monitor_optimal_test.log"
    echo ""
    echo "✓ Ready to submit full array job!"
else
    echo ""
    echo "❌ Test failed. Check errors above before submitting array job."
fi

exit $EXIT_CODE
