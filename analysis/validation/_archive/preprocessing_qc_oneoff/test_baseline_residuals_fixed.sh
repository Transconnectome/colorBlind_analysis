#!/bin/bash

# Interactive Test: Baseline with 1st-level Residuals (FIXED)
# Usage: Run in srun interactive session

set -e  # Exit on error

echo "=================================================="
echo "Interactive Test: Baseline + 1st-level Residuals"
echo "=================================================="

# Configuration
SUBJECT="01"
ROI="V1"

echo ""
echo "Test Configuration:"
echo "  Subject: sub-${SUBJECT}"
echo "  ROI: ${ROI}"
echo ""

# Verify conda environment
if [ -z "$CONDA_DEFAULT_ENV" ] || [ "$CONDA_DEFAULT_ENV" != "nilearn" ]; then
    echo "⚠️  Activating nilearn environment..."
    source ~/.bashrc
    conda activate nilearn
fi

echo "Python environment:"
echo "  Python: $(which python)"
echo "  Version: $(python --version)"
echo "  Conda env: $CONDA_DEFAULT_ENV"
echo ""

# Change to working directory
cd /scratch/connectome/haba6030/colorBlind

# Output directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="analysis/phase1_preprocess_decoding/results/baseline_withResiduals_TEST/sub-${SUBJECT}/${ROI}_${TIMESTAMP}"
mkdir -p ${OUTPUT_DIR}

echo "Output directory: ${OUTPUT_DIR}"
echo ""

# Check input files
echo "Checking input files..."
FMRIPREP_OUT="/storage/connectome/haba6030/fmriprep_out_method3_header_mi"
BOLD_PATTERN="${FMRIPREP_OUT}/sub-${SUBJECT}/func/sub-${SUBJECT}_task-rsvp_run-1_space-*.nii.gz"
BOLD_FILE=$(ls ${BOLD_PATTERN} 2>/dev/null | head -1)

if [ -z "$BOLD_FILE" ]; then
    echo "❌ ERROR: BOLD data not found!"
    echo "  Pattern: ${BOLD_PATTERN}"
    exit 1
else
    echo "✅ Found BOLD data: $(basename ${BOLD_FILE})"
fi
echo ""

# Start resource monitoring
RESOURCE_LOG="${OUTPUT_DIR}/resource_usage.log"
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

echo "Starting baseline with residuals saving..."
echo "Resource monitoring: ${RESOURCE_LOG}"
echo ""

# Run with profiling
/usr/bin/time -v python analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py \
    --subject ${SUBJECT} \
    --roi ${ROI} \
    --dataset method3_header_mi \
    --output-dir ${OUTPUT_DIR} \
    --highpass 0.0 \
    --motion none \
    --drift per_run \
    --normalize-level none \
    --save-residuals \
    --2nd-level-intercept

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
echo ""
echo "Checking Output Files:"
echo ""

# Check residuals
RESIDUALS_FILE="${OUTPUT_DIR}/residuals_1st_level.npy"
if [ -f "${RESIDUALS_FILE}" ]; then
    SIZE=$(ls -lh ${RESIDUALS_FILE} | awk '{print $5}')
    echo "✅ residuals_1st_level.npy created (${SIZE})"

    # Analyze residuals
    python << 'PYTHON_EOF'
import numpy as np
residuals = np.load('RESIDUALS_FILE_PLACEHOLDER')
n_samples, n_voxels = residuals.shape
ratio = n_samples / n_voxels

print(f'\n=== Residuals Analysis ===')
print(f'Shape:              {residuals.shape}')
print(f'Samples (TRs):      {n_samples}')
print(f'Voxels:             {n_voxels}')
print(f'Ratio (s/v):        {ratio:.2f}')
print(f'Residual std:       {np.std(residuals):.4f}')
print(f'Residual var:       {np.var(residuals):.4f}')
print(f'Memory usage:       {residuals.nbytes / 1024**2:.1f} MB')

if ratio >= 2.0:
    print('\n✅ EXCELLENT: Ratio > 2.0 → Stable covariance estimation')
elif ratio >= 1.0:
    print('\n✅ GOOD: Ratio > 1.0 → Ledoit-Wolf sufficient')
else:
    print('\n⚠️  WARNING: Ratio < 1.0 → High shrinkage expected')
PYTHON_EOF

    # Replace placeholder with actual path
    sed -i "s|RESIDUALS_FILE_PLACEHOLDER|${RESIDUALS_FILE}|g" <<< "$python_code" 2>/dev/null || true

    # Run directly with proper path
    python -c "
import numpy as np
residuals = np.load('${RESIDUALS_FILE}')
n_samples, n_voxels = residuals.shape
ratio = n_samples / n_voxels

print(f'\n=== Residuals Analysis ===')
print(f'Shape:              {residuals.shape}')
print(f'Samples (TRs):      {n_samples}')
print(f'Voxels:             {n_voxels}')
print(f'Ratio (s/v):        {ratio:.2f}')
print(f'Residual std:       {np.std(residuals):.4f}')
print(f'Residual var:       {np.var(residuals):.4f}')
print(f'Memory usage:       {residuals.nbytes / 1024**2:.1f} MB')

if ratio >= 2.0:
    print('\n✅ EXCELLENT: Ratio > 2.0 → Stable covariance estimation')
elif ratio >= 1.0:
    print('\n✅ GOOD: Ratio > 1.0 → Ledoit-Wolf sufficient')
else:
    print('\n⚠️  WARNING: Ratio < 1.0 → High shrinkage expected')
"
else
    echo "❌ ERROR: residuals_1st_level.npy NOT created!"
    exit 1
fi

# Check amplitudes
AMPLITUDES_FILE="${OUTPUT_DIR}/amplitudes_raw.npy"
if [ -f "${AMPLITUDES_FILE}" ]; then
    SIZE=$(ls -lh ${AMPLITUDES_FILE} | awk '{print $5}')
    echo ""
    echo "✅ amplitudes_raw.npy created (${SIZE})"
else
    echo "❌ ERROR: amplitudes_raw.npy NOT created!"
fi

# Check settings
SETTINGS_FILE="${OUTPUT_DIR}/results.json"
if [ -f "${SETTINGS_FILE}" ]; then
    echo ""
    echo "✅ results.json created"

    # Check save_residuals flag
    python -c "
import json
with open('${SETTINGS_FILE}') as f:
    settings = json.load(f)

if 'preprocessing' in settings and 'save_residuals' in settings['preprocessing']:
    save_residuals = settings['preprocessing']['save_residuals']
    print(f'\n  save_residuals: {save_residuals}')
    if save_residuals:
        print('  ✅ Correctly recorded in settings')
    else:
        print('  ⚠️  Flag is False (unexpected)')
else:
    print('  ⚠️  save_residuals not found in settings')
"
else
    echo "⚠️  results.json not found"
fi

echo ""
echo "Output directory: ${OUTPUT_DIR}"
echo ""

if [ ${EXIT_CODE} -eq 0 ]; then
    echo "✅ Test PASSED - Ready for full deployment"
else
    echo "❌ Test FAILED - Check errors above"
fi
