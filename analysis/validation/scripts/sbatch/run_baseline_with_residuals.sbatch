#!/bin/bash
#SBATCH --job-name=baseline_resid
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/logs/baseline_resid_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/logs/baseline_resid_%A_%a.err
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=04:00:00
#SBATCH --array=1-40%6

# Baseline FIR Reconstruction with Residual Saving
# Purpose: Re-run baseline pipeline to save GLM residuals for whitening
# This is a prerequisite for Phase 2 if residuals aren't already saved
# Expected runtime: ~60-90 min per job
# Memory: ~18-22GB peak (24GB allocated)

# Configuration
CONDA_ENV="nilearn"
SCRIPT_DIR="/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding"
OUTPUT_BASE="/scratch/connectome/haba6030/colorBlind/derivatives/BH2009_original_v3"
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
echo "Baseline FIR with Residual Saving"
echo "Task ID: $SLURM_ARRAY_TASK_ID"
echo "Subject: sub-${SUBJECT}"
echo "ROI: ${ROI}"
echo "Node: $(hostname)"
echo "Start time: $(date)"
echo "=================================================="

# Create output directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JOB_OUTPUT_DIR="${OUTPUT_BASE}/${TIMESTAMP}_${SLURM_ARRAY_JOB_ID}/sub-${SUBJECT}_${ROI}_baseline_with_residuals"
mkdir -p ${JOB_OUTPUT_DIR}
mkdir -p /scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/logs

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
    DISK_USAGE=$(df -h ${JOB_OUTPUT_DIR} | tail -1 | awk '{print $3 "/" $2}')
    echo "$(date +%H:%M:%S) Memory: ${MEM_USAGE}, CPU: ${CPU_USAGE}%, Disk: ${DISK_USAGE}"
    sleep 60
done) &
MONITOR_PID=$!

# Run baseline FIR reconstruction with residual saving
echo ""
echo "Running FIR reconstruction with residual saving..."
echo "This will save:"
echo "  - amplitudes_raw.npy (existing)"
echo "  - residuals_1st_level.npy (NEW)"
echo "  - residuals_2nd_level.npy (NEW)"
echo ""

# NOTE: This assumes fir_reconstruction_BH2009_system_clean.py has been modified
# to save residuals at lines ~980 and ~1580 as specified in the plan

python ${SCRIPT_DIR}/fir_reconstruction_BH2009_system_clean.py \
    --subject ${SUBJECT} \
    --roi ${ROI} \
    --fmriprep_dir ${FMRIPREP_OUT} \
    --event_dir ${EVENT_DIR} \
    --output_dir ${JOB_OUTPUT_DIR} \
    --save_residuals \
    --normalization raw \
    --n_jobs 4

EXIT_CODE=$?

# Stop memory monitor
kill $MONITOR_PID 2>/dev/null

# Report results
echo ""
echo "=================================================="
echo "Baseline FIR with Residuals Complete"
echo "Exit code: ${EXIT_CODE}"
echo "End time: $(date)"
echo "Output saved to: ${JOB_OUTPUT_DIR}"
echo "=================================================="

# Check output files
echo ""
echo "Output Files:"

if [ -f "${JOB_OUTPUT_DIR}/amplitudes_raw.npy" ]; then
    SIZE=$(ls -lh ${JOB_OUTPUT_DIR}/amplitudes_raw.npy | awk '{print $5}')
    echo "✓ amplitudes_raw.npy (${SIZE})"
else
    echo "✗ Warning: amplitudes_raw.npy not found"
fi

if [ -f "${JOB_OUTPUT_DIR}/residuals_1st_level.npy" ]; then
    SIZE=$(ls -lh ${JOB_OUTPUT_DIR}/residuals_1st_level.npy | awk '{print $5}')
    echo "✓ residuals_1st_level.npy (${SIZE}) [NEW]"
else
    echo "✗ Warning: residuals_1st_level.npy not found"
fi

if [ -f "${JOB_OUTPUT_DIR}/residuals_2nd_level.npy" ]; then
    SIZE=$(ls -lh ${JOB_OUTPUT_DIR}/residuals_2nd_level.npy | awk '{print $5}')
    echo "✓ residuals_2nd_level.npy (${SIZE}) [NEW]"
else
    echo "✗ Warning: residuals_2nd_level.npy not found"
fi

if [ -f "${JOB_OUTPUT_DIR}/settings.json" ]; then
    echo "✓ settings.json"
fi

# Display settings
if [ -f "${JOB_OUTPUT_DIR}/settings.json" ]; then
    echo ""
    echo "Settings:"
    cat ${JOB_OUTPUT_DIR}/settings.json
fi

# Estimate storage usage
echo ""
echo "Storage Summary:"
du -sh ${JOB_OUTPUT_DIR}

exit ${EXIT_CODE}
