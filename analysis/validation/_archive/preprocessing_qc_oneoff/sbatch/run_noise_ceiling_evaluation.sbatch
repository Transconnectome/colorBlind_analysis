#!/bin/bash
#SBATCH --job-name=noise_ceiling
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/noise_ceiling_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/noise_ceiling_%A_%a.err
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=20G
#SBATCH --time=02:00:00
#SBATCH --array=1-40%8

# Phase 1: Noise Ceiling Evaluation
# Purpose: Compute split-half and LOSO noise ceiling for all subject-ROI pairs
# Expected runtime: ~15-30 min per job
# Memory: ~12-16GB peak (20GB allocated for safety)

# Configuration
CONDA_ENV="nilearn"
SCRIPT_DIR="/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts"
OUTPUT_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/noise_ceiling_evaluation"
BASELINE_DIR="/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline"

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
echo "Phase 1: Noise Ceiling Evaluation"
echo "Task ID: $SLURM_ARRAY_TASK_ID"
echo "Subject: sub-${SUBJECT}"
echo "ROI: ${ROI}"
echo "Node: $(hostname)"
echo "Start time: $(date)"
echo "=================================================="

# Create output directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JOB_OUTPUT_DIR="${OUTPUT_DIR}/${TIMESTAMP}_${SLURM_ARRAY_JOB_ID}"
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
    echo "$(date +%H:%M:%S) Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
    sleep 60
done) &
MONITOR_PID=$!

# Run Phase 1 evaluation
echo ""
echo "Running noise ceiling evaluation..."
python ${SCRIPT_DIR}/evaluate_with_noise_ceiling.py \
    --subject ${SUBJECT} \
    --roi ${ROI} \
    --baseline_dir ${BASELINE_DIR} \
    --output_dir ${JOB_OUTPUT_DIR} \
    --n_iterations 1000 \
    --n_jobs 4

EXIT_CODE=$?

# Stop memory monitor
kill $MONITOR_PID 2>/dev/null

# Report results
echo ""
echo "=================================================="
echo "Phase 1 Complete"
echo "Exit code: ${EXIT_CODE}"
echo "End time: $(date)"
echo "Output saved to: ${JOB_OUTPUT_DIR}"
echo "=================================================="

# Check output files
if [ -f "${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_noise_ceiling.json" ]; then
    echo "✓ Results JSON created successfully"
    cat ${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_noise_ceiling.json
else
    echo "✗ Warning: Results JSON not found"
fi

exit ${EXIT_CODE}
