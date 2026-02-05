#!/bin/bash

# Interactive Test Script - Phase 2: Whitening + Ceiling + SNR
# Usage: Run this in interactive mode after srun allocation

echo "=================================================="
echo "Interactive Test: Phase 2 Whitening + SNR"
echo "=================================================="

# Configuration
SUBJECT="01"
ROI="V1"
SCRIPT_DIR="/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts"
OUTPUT_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/whitening_evaluation"
BASELINE_DIR="/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline"

# Create output directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JOB_OUTPUT_DIR="${OUTPUT_DIR}/INTERACTIVE_TEST_${TIMESTAMP}"
mkdir -p ${JOB_OUTPUT_DIR}

echo ""
echo "Test Configuration:"
echo "  Subject: sub-${SUBJECT}"
echo "  ROI: ${ROI}"
echo "  Output: ${JOB_OUTPUT_DIR}"
echo ""

# Check input files
echo "Checking input files..."
BASELINE_PATTERN="${BASELINE_DIR}/sub-${SUBJECT}/${ROI}/amplitudes_raw.npy"
BASELINE_FILE=$(ls ${BASELINE_PATTERN} 2>/dev/null | head -1)

if [ -z "$BASELINE_FILE" ]; then
    echo "ERROR: Baseline amplitudes not found!"
    echo "  Pattern: ${BASELINE_PATTERN}"
    exit 1
else
    echo "✓ Found: ${BASELINE_FILE}"

    # Check data shape
    python -c "
import numpy as np
data = np.load('${BASELINE_FILE}')
print(f'  Shape: {data.shape}')
print(f'  Estimated covariance memory: {data.shape[-1]**2 * 8 / 1024**3:.2f} GB')
"
fi

# Check for residuals
BASELINE_DIR_PARENT=$(dirname ${BASELINE_FILE})
RESIDUALS_FILE="${BASELINE_DIR_PARENT}/residuals_2nd_level.npy"
if [ -f "$RESIDUALS_FILE" ]; then
    echo "✓ Found residuals: ${RESIDUALS_FILE}"
else
    echo "⚠ Residuals not found (will estimate from data variance)"
fi

# Start resource monitoring in background
RESOURCE_LOG="${JOB_OUTPUT_DIR}/resource_usage.log"
echo "Timestamp,Memory_Used_GB,Memory_Free_GB,CPU_Percent" > ${RESOURCE_LOG}

(while true; do
    MEM_USED=$(free -g | grep Mem | awk '{print $3}')
    MEM_FREE=$(free -g | grep Mem | awk '{print $4}')
    CPU_PERCENT=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    TIMESTAMP=$(date +%H:%M:%S)
    echo "${TIMESTAMP},${MEM_USED},${MEM_FREE},${CPU_PERCENT}" >> ${RESOURCE_LOG}
    sleep 5
done) &
MONITOR_PID=$!

echo ""
echo "Starting evaluation with profiling..."
echo "This tests: Does whitening improve data quality (ceiling + SNR)?"
echo "Resource monitoring saved to: ${RESOURCE_LOG}"
echo ""

# Run with profiling
/usr/bin/time -v python ${SCRIPT_DIR}/evaluate_whitening_ceiling_snr.py \
    --subject ${SUBJECT} \
    --roi ${ROI} \
    --baseline_dir ${BASELINE_DIR} \
    --output_dir ${JOB_OUTPUT_DIR} \
    --n_ceiling_iterations 1000 \
    --n_jobs 4 \
    --save_whitened_data

EXIT_CODE=$?

# Stop monitoring
kill $MONITOR_PID 2>/dev/null

echo ""
echo "=================================================="
echo "Test Complete (Exit code: ${EXIT_CODE})"
echo "=================================================="

# Show peak memory
echo ""
echo "Peak Memory Usage:"
tail -n +2 ${RESOURCE_LOG} | awk -F',' '{print $2 " GB used, " $3 " GB free"}' | \
    sort -n -r | head -1

# Check results
if [ -f "${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_whitening_results.json" ]; then
    echo ""
    echo "✓ Results created successfully"
    echo ""
    python -c "
import json
with open('${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_whitening_results.json', 'r') as f:
    r = json.load(f)

print('=== Noise Ceiling ===')
if 'noise_ceiling' in r:
    nc = r['noise_ceiling']
    print(f\"Raw:      {nc.get('raw_split_half', 'N/A'):.3f}\")
    print(f\"Whitened: {nc.get('whitened_split_half', 'N/A'):.3f}\")
    print(f\"Improvement: +{nc.get('improvement_percent', 0):.1f}%\")

print('')
print('=== Pattern SNR ===')
if 'snr_analysis' in r and 'pattern_snr' in r['snr_analysis']:
    snr = r['snr_analysis']['pattern_snr']
    print(f\"Raw:      {snr.get('raw', 'N/A'):.2f}\")
    print(f\"Whitened: {snr.get('whitened', 'N/A'):.2f}\")
    print(f\"Improvement: +{snr.get('improvement_percent', 0):.1f}%\")

print('')
print('=== RDM Correlation ===')
if 'rdm_reliability' in r:
    rdm = r['rdm_reliability']
    print(f\"Raw:              {rdm.get('raw', 'N/A'):.3f}\")
    print(f\"Raw + Procrustes: {rdm.get('raw_procrustes', 'N/A'):.3f}\")
    print(f\"Whitened + Proc:  {rdm.get('whitened_procrustes', 'N/A'):.3f}\")
"
fi

# Check output files
echo ""
echo "Output Files:"
ls -lh ${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_* 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'

echo ""
echo "Output directory: ${JOB_OUTPUT_DIR}"
