#!/bin/bash
# Phase 2 Interactive Test: P3 (Motion + WM aCompCor)

echo "=================================================================="
echo "Phase 2: WM aCompCor Testing - Interactive Test"
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
TEST_CONDITION="P3"  # Most complex condition (Motion + WM aCompCor)

echo "Test configuration:"
echo "  Subject: sub-${TEST_SUBJECT}"
echo "  ROI: ${TEST_ROI}"
echo "  Condition: ${TEST_CONDITION} (Motion/Tissue + WM aCompCor)"
echo ""

# Check confounds file first (from fMRIPrep output directory)
CONFOUNDS_FILE="/storage/connectome/haba6030/fmriprep_out_method3_header_mi/sub-${TEST_SUBJECT}/func/sub-${TEST_SUBJECT}_task-rsvp_run-1_desc-confounds_timeseries.tsv"

echo "Checking confounds availability..."
if [ -f "$CONFOUNDS_FILE" ]; then
    echo "  ✓ Confounds file exists"

    # Check for WM aCompCor columns
    if head -1 "$CONFOUNDS_FILE" | grep -q "a_comp_cor_05"; then
        echo "  ✓ WM aCompCor columns present (a_comp_cor_05~09)"
    else
        echo "  ⚠️  WARNING: WM aCompCor columns NOT found"
        echo "     Available columns:"
        head -1 "$CONFOUNDS_FILE" | tr '\t' '\n' | grep -E "(comp_cor|csf|white|motion)"
    fi
else
    echo "  ❌ ERROR: Confounds file not found: $CONFOUNDS_FILE"
    echo "     Run generate_confounds.py first!"
    exit 1
fi
echo ""

# Memory monitoring
(while true; do
    echo "[$(date +%H:%M:%S)] Memory: $(free -h | grep Mem | awk '{print $3"/"$2}')"
    sleep 30
done) > memory_monitor_phase2_test.log 2>&1 &
MONITOR_PID=$!

echo "Memory monitor PID: $MONITOR_PID"
echo ""

# Run test
echo "Running test..."
echo ""

python3 << EOF
import sys
sys.path.insert(0, '$SCRIPT_DIR')

try:
    from phase2_pipeline_wm_acompcor import run_single_condition, CONDITIONS

    subject_id = '$TEST_SUBJECT'
    roi_name = '$TEST_ROI'
    condition_code = '$TEST_CONDITION'
    condition_config = CONDITIONS[condition_code]

    print(f"Running: {condition_code} for sub-{subject_id} {roi_name}")
    print(f"Config: {condition_config}\n")

    metrics = run_single_condition(subject_id, roi_name, condition_code, condition_config)

    print(f"\nSUCCESS!")
    print(f"  Raw method_diff:  {metrics['raw_noise_ceiling']['method_diff']:.4f}")
    print(f"  Proc method_diff: {metrics['procrustes_noise_ceiling']['method_diff']:.4f}")
    print(f"  Drift magnitude:  {metrics['drift_magnitude']:.4f}")
    print(f"  RDM reliability:  {metrics['raw_rdm_reliability']:.4f}")
    print(f"  Proc disparity:   {metrics['procrustes_disparity']:.4f}")

    sys.exit(0)

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

EXIT_CODE=$?

# Stop memory monitor
kill $MONITOR_PID 2>/dev/null

echo ""
echo "=================================================================="
echo "Test completed with exit code: $EXIT_CODE"
echo "=================================================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "Results saved to:"
    echo "  phase2_results/${TEST_CONDITION}/sub-${TEST_SUBJECT}/${TEST_ROI}/"
    echo ""
    echo "Check memory usage:"
    echo "  tail memory_monitor_phase2_test.log"
    echo ""
    echo "✓ Ready to submit full array job!"
else
    echo ""
    echo "❌ Test failed. Check errors above before submitting array job."
fi

exit $EXIT_CODE
