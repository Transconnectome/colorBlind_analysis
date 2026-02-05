#!/bin/bash

# Interactive Test Script - Phase 1: Noise Ceiling
# Usage: Run this in interactive mode after srun allocation

echo "=================================================="
echo "Interactive Test: Phase 1 Noise Ceiling"
echo "=================================================="

# Configuration
SUBJECT="01"
ROI="V1"
SCRIPT_DIR="/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts"
OUTPUT_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/noise_ceiling_evaluation"
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
echo "Resource monitoring saved to: ${RESOURCE_LOG}"
echo ""

# Run with profiling
/usr/bin/time -v python ${SCRIPT_DIR}/evaluate_with_noise_ceiling.py \
    --subject ${SUBJECT} \
    --roi ${ROI} \
    --baseline_dir ${BASELINE_DIR} \
    --output_dir ${JOB_OUTPUT_DIR} \
    --n_iterations 1000 \
    --n_jobs 4

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
tail -n +2 ${RESOURCE_LOG} | awk -F',' '{print $2}' | sort -n | tail -1 | \
    awk '{print "  " $1 " GB used"}'

# Check results
if [ -f "${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_noise_ceiling.json" ]; then
    echo ""
    echo "✓ Results created successfully"
    echo ""
    python -c "
import json
with open('${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_noise_ceiling.json', 'r') as f:
    r = json.load(f)
print(f\"Split-half reliability: {r.get('split_half_corrected', 'N/A'):.3f}\")
print(f\"95% CI: [{r.get('split_half_ci_lower', 'N/A'):.3f}, {r.get('split_half_ci_upper', 'N/A'):.3f}]\")
"
fi

echo ""
echo "Output saved to: ${JOB_OUTPUT_DIR}"
