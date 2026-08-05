#!/bin/bash
#SBATCH --job-name=baseline_resid
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/baseline_resid_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/baseline_resid_%A_%a.err
#SBATCH --qos=shared
#SBATCH --nodelist=node2,node4
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --time=00:30:00
#SBATCH --array=1-40%12
#SBATCH --no-requeue

# ============================================================================
# Baseline FIR with 1st-level Residuals Saving (CORRECT SETTINGS)
# Purpose: Save GLM residuals for whitening (Diedrichsen et al., 2016)
# Settings: highpass=0, motion=none, drift=per_run, normalize=none
#           NO 2nd-level-intercept (analysis showed baseline performs better)
# Expected runtime: 1-2 min per job (measured: 75 sec)
# Memory: 6-8 GB peak (measured: 6.3 GB, 12GB allocated)
# ============================================================================

# Critical: Error handling and conda activation
set -e
source ~/.bashrc
conda activate nilearn

# Configuration
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
ROIS=(V1 V2 V3 hV4)

# Map array task ID to subject and ROI
SUBJ_IDX=$(( ($SLURM_ARRAY_TASK_ID - 1) / 4 ))
ROI_IDX=$(( ($SLURM_ARRAY_TASK_ID - 1) % 4 ))

SUBJECT=${SUBJECTS[$SUBJ_IDX]}
ROI=${ROIS[$ROI_IDX]}
DATASET="method3_header_mi"

echo "=================================================="
echo "Baseline FIR + 1st-level Residuals"
echo "Task ID: $SLURM_ARRAY_TASK_ID"
echo "Subject: sub-${SUBJECT}"
echo "ROI: ${ROI}"
echo "Node: $(hostname)"
echo "Start time: $(date)"
echo "=================================================="

# Verify Python environment
echo "Python: $(which python)"
echo "Python version: $(python --version)"
echo ""

# Change to working directory
cd /scratch/connectome/haba6030/colorBlind

# Output directory - Correct baseline settings with residuals
OUTPUT_DIR="analysis/phase1_preprocess_decoding/results/baseline_residuals/sub-${SUBJECT}/${ROI}"

# Check if already completed (resume capability)
if [ -f "${OUTPUT_DIR}/residuals_1st_level.npy" ]; then
    echo "⚠️  Output already exists: ${OUTPUT_DIR}/residuals_1st_level.npy"
    echo "    Skipping to avoid overwrite. Delete manually to re-run."
    exit 0
fi

# Create output directory
mkdir -p ${OUTPUT_DIR}

# Monitor memory usage in background
(while true; do
    MEM_USAGE=$(free -h | grep Mem | awk '{print $3 "/" $2}')
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}')
    echo "$(date +%H:%M:%S) Memory: ${MEM_USAGE}, CPU: ${CPU_USAGE}%"
    sleep 60
done) &
MONITOR_PID=$!

echo "Running baseline FIR reconstruction with residuals saving..."
echo "Reference: Diedrichsen et al. (2016) - Multivariate Noise Normalization"
echo ""
echo "Settings (Analysis-validated optimal):"
echo "  highpass=0, motion=none, drift=per_run"
echo "  normalize=none, 2nd-level-intercept=FALSE"
echo "  save-residuals=TRUE"
echo ""

# Run FIR reconstruction with residuals (NO --2nd-level-intercept!)
python analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py \
    --subject ${SUBJECT} \
    --roi ${ROI} \
    --dataset ${DATASET} \
    --output-dir ${OUTPUT_DIR} \
    --highpass 0.0 \
    --motion none \
    --drift per_run \
    --normalize-level none \
    --save-residuals

EXIT_CODE=$?

# Stop memory monitor
kill $MONITOR_PID 2>/dev/null

# Report results
echo ""
echo "=================================================="
echo "Baseline Complete"
echo "Exit code: ${EXIT_CODE}"
echo "End time: $(date)"
echo "Output: ${OUTPUT_DIR}"
echo "=================================================="

# Check and summarize output files
echo ""
echo "Output Files:"

# Check residuals (NEW)
if [ -f "${OUTPUT_DIR}/residuals_1st_level.npy" ]; then
    SIZE=$(ls -lh ${OUTPUT_DIR}/residuals_1st_level.npy | awk '{print $5}')
    echo "✅ residuals_1st_level.npy (${SIZE})"

    # Quick validation with Python
    python << PYTHON_EOF
import numpy as np
import sys

try:
    residuals = np.load('${OUTPUT_DIR}/residuals_1st_level.npy')
    n_samples, n_voxels = residuals.shape
    ratio = n_samples / n_voxels

    print(f'  Shape: ({n_samples}, {n_voxels})')
    print(f'  Ratio: {ratio:.2f}')

    if ratio >= 2.0:
        print('  ✅ Excellent (ratio > 2.0)')
    elif ratio >= 1.0:
        print('  ✅ Good (ratio > 1.0)')
    else:
        print('  ⚠️  Low ratio')

except Exception as e:
    print(f'  ⚠️  Validation failed: {e}', file=sys.stderr)
    sys.exit(1)
PYTHON_EOF

else
    echo "❌ WARNING: residuals_1st_level.npy not found!"
fi

# Check amplitudes (existing)
if [ -f "${OUTPUT_DIR}/amplitudes_raw.npy" ]; then
    SIZE=$(ls -lh ${OUTPUT_DIR}/amplitudes_raw.npy | awk '{print $5}')
    echo "✅ amplitudes_raw.npy (${SIZE})"
else
    echo "❌ WARNING: amplitudes_raw.npy not found!"
fi

# Check results
if [ -f "${OUTPUT_DIR}/results.json" ]; then
    echo "✅ results.json"
else
    echo "⚠️  results.json not found"
fi

echo ""
echo "All files in output directory:"
ls -lh ${OUTPUT_DIR}/ 2>/dev/null | tail -n +2 | awk '{print "  " $9 " (" $5 ")"}'

exit ${EXIT_CODE}
