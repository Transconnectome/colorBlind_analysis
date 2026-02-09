#!/bin/bash
# Test Full Dataset P3 Pipeline

echo "=================================================================="
echo "Full Dataset P3 Pipeline - Local Test"
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
echo "  Pipeline: P3 (validated from Phase 2)"
echo ""

# Memory monitoring
(while true; do
    echo "[$(date +%H:%M:%S)] Memory: $(free -h | grep Mem | awk '{print $3"/"$2}')"
    sleep 30
done) > memory_monitor_full_P3_test.log 2>&1 &
MONITOR_PID=$!

echo "Memory monitor PID: $MONITOR_PID"
echo ""

# Run test
echo "Running pipeline..."
echo ""

python run_full_dataset_P3.py \
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
    echo "Expected results (from Phase 2 validation):"
    echo "  Method Diff: ~0.056 (< 0.10)"
    echo "  RDM Reliability (Raw): ~0.149 (positive)"
    echo "  RDM Reliability (Proc): ~0.654 (> 0.5)"
    echo "  Procrustes Disparity: ~0.0026 (< 0.003)"
    echo ""
    echo "Results saved to:"
    echo "  /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_P3/sub-${TEST_SUBJECT}/${TEST_ROI}/"
    echo ""
    echo "Check results:"
    echo "  cat /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_P3/sub-${TEST_SUBJECT}/${TEST_ROI}/metrics.json"
    echo ""
    echo "✓ Ready to submit full array job!"
else
    echo ""
    echo "❌ Test failed. Check errors above before submitting array job."
fi

exit $EXIT_CODE
