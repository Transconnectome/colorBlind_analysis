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

# Baseline FIR with 1st-level Residuals Saving
# Purpose: Re-run baseline to save GLM residuals for whitening (Diedrichsen et al., 2016)
# Expected runtime: 1-2 min per job (measured: 75 sec)
# Memory: 6-8 GB peak (measured: 6.3 GB, 12GB allocated with 2× safety margin)

# Configuration
CONDA_ENV="nilearn"
SCRIPT_DIR="/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding"
OUTPUT_BASE="/scratch/connectome/haba6030/colorBlind/derivatives/BH2009_original_v3_with_residuals"
FMRIPREP_OUT="/storage/connectome/haba6030/fmriprep_out_method3_header_mi"
EVENT_DIR="/storage/connectome/haba6030/bids_editted"

# ROIs and subjects
ROIS=("V1" "V2" "V3" "hV4")
SUBJECTS=("01" "02" "03" "04" "05" "06" "07" "08" "09" "10")

# Calculate subject and ROI from SLURM_ARRAY_TASK_ID
TASK_ID=$SLURM_ARRAY_TASK_ID
N_ROIS=${#ROIS[@]}
SUBJECT_IDX=$(( (TASK_ID - 1) / N_ROIS ))
ROI_IDX=$(( (TASK_ID - 1) % N_ROIS ))

SUBJECT=${SUBJECTS[$SUBJECT_IDX]}
ROI=${ROIS[$ROI_IDX]}

echo "=================================================="
echo "Baseline FIR + 1st-level Residuals"
echo "Task ID: $SLURM_ARRAY_TASK_ID"
echo "Subject: sub-${SUBJECT}"
echo "ROI: ${ROI}"
echo "Node: $(hostname)"
echo "Start time: $(date)"
echo "=================================================="

# Create output directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JOB_OUTPUT_DIR="${OUTPUT_BASE}/${TIMESTAMP}_${SLURM_ARRAY_JOB_ID}/sub-${SUBJECT}_${ROI}"
mkdir -p ${JOB_OUTPUT_DIR}
mkdir -p /scratch/connectome/haba6030/colorBlind/analysis/validation/logs

# Activate conda environment
source /home/haba6030/miniconda3/etc/profile.d/conda.sh
conda activate ${CONDA_ENV}

# Verify Python environment
echo "Python: $(which python)"
echo "Python version: $(python --version)"

# Monitor memory usage in background
(while true; do
    MEM_USAGE=$(free -h | grep Mem | awk '{print $3 "/" $2}')
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}')
    echo "$(date +%H:%M:%S) Memory: ${MEM_USAGE}, CPU: ${CPU_USAGE}%"
    sleep 60
done) &
MONITOR_PID=$!

# Run baseline with residuals
echo ""
echo "Running baseline FIR reconstruction with residuals saving..."
echo "Reference: Diedrichsen et al. (2016) - Multivariate Noise Normalization"
echo ""

python ${SCRIPT_DIR}/fir_reconstruction_BH2009_system_clean.py \
    --subject ${SUBJECT} \
    --roi ${ROI} \
    --output-dir ${JOB_OUTPUT_DIR} \
    --highpass 0.0 \
    --motion none \
    --drift per_run \
    --normalize-level none \
    --save-residuals \
    --2nd-level-intercept

EXIT_CODE=$?

# Stop memory monitor
kill $MONITOR_PID 2>/dev/null

# Report results
echo ""
echo "=================================================="
echo "Baseline Complete"
echo "Exit code: ${EXIT_CODE}"
echo "End time: $(date)"
echo "Output: ${JOB_OUTPUT_DIR}"
echo "=================================================="

# Check and summarize output files
echo ""
echo "Output Files:"

# Check residuals (NEW)
if [ -f "${JOB_OUTPUT_DIR}/residuals_1st_level.npy" ]; then
    SIZE=$(ls -lh ${JOB_OUTPUT_DIR}/residuals_1st_level.npy | awk '{print $5}')
    echo "✅ residuals_1st_level.npy (${SIZE}) [NEW - for whitening]"

    # Quick validation with Python
    python -c "
import numpy as np
import sys

try:
    residuals = np.load('${JOB_OUTPUT_DIR}/residuals_1st_level.npy')
    n_samples, n_voxels = residuals.shape
    ratio = n_samples / n_voxels

    print(f'\n  Residuals shape: ({n_samples}, {n_voxels})')
    print(f'  Samples/Voxels ratio: {ratio:.2f}')

    if ratio >= 2.0:
        print('  ✅ Excellent ratio for covariance estimation')
    elif ratio >= 1.0:
        print('  ✅ Good ratio (Ledoit-Wolf sufficient)')
    else:
        print('  ⚠️  Low ratio (high shrinkage expected)')

except Exception as e:
    print(f'  ⚠️  Could not validate: {e}', file=sys.stderr)
"
else
    echo "❌ WARNING: residuals_1st_level.npy not found!"
fi

# Check amplitudes (existing)
if [ -f "${JOB_OUTPUT_DIR}/amplitudes_raw.npy" ]; then
    SIZE=$(ls -lh ${JOB_OUTPUT_DIR}/amplitudes_raw.npy | awk '{print $5}')
    echo "✅ amplitudes_raw.npy (${SIZE})"
else
    echo "❌ WARNING: amplitudes_raw.npy not found!"
fi

# Check results
if [ -f "${JOB_OUTPUT_DIR}/results.json" ]; then
    echo "✅ results.json"

    # Extract key metrics
    python -c "
import json
import sys

try:
    with open('${JOB_OUTPUT_DIR}/results.json', 'r') as f:
        results = json.load(f)

    print('\n=== Key Results ===')

    # Check save_residuals flag
    if 'preprocessing' in results and 'save_residuals' in results['preprocessing']:
        save_res = results['preprocessing']['save_residuals']
        print(f'save_residuals: {save_res}')

    # Performance metrics
    if 'classification_accuracy' in results:
        acc = results['classification_accuracy']
        print(f'Classification accuracy: {acc:.3f}')

    if 'reconstruction_error' in results:
        err = results['reconstruction_error']
        print(f'Reconstruction error: {err:.3f}')

    # Voxel stats
    if 'n_voxels_selected' in results:
        n_vox = results['n_voxels_selected']
        print(f'Voxels selected: {n_vox}')

    print('===================')

except Exception as e:
    print(f'Could not parse results: {e}', file=sys.stderr)
"
else
    echo "⚠️  results.json not found"
fi

# List all output files
echo ""
echo "All output files:"
ls -lh ${JOB_OUTPUT_DIR}/ | tail -n +2

exit ${EXIT_CODE}
