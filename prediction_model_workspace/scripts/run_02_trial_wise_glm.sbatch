#!/bin/bash
#SBATCH --job-name=trial_glm
#SBATCH --qos=shared
#SBATCH --nodelist=node4
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --array=0-9  # 10 subjects (HC: 01-07, CVD: 08-10)
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/logs/trial_glm_sub-%a_%A.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/logs/trial_glm_sub-%a_%A.err

# Print job info
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "Job Name: $SLURM_JOB_NAME"
echo "Node: $SLURM_NODELIST"
echo "Start Time: $(date)"
echo "=========================================="

# Define all subjects (HC + CVD)
ALL_SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
ROIS=(V1 V2 V3 hV4)

# Get subject for this array task
SUBJECT=${ALL_SUBJECTS[$SLURM_ARRAY_TASK_ID]}

echo ""
echo "Processing Subject: sub-${SUBJECT}"
echo "ROIs to process: ${ROIS[@]}"
echo ""

# Activate conda environment
echo "Activating conda environment..."
eval "$(conda shell.bash hook)"
conda activate nilearn

# Verify environment
echo "Conda environment: $CONDA_DEFAULT_ENV"
which python
python --version

# Set Python unbuffered output for real-time logging
export PYTHONUNBUFFERED=1
echo "Python unbuffered mode: enabled"
echo ""

# Navigate to script directory
cd /scratch/connectome/haba6030/colorBlind/prediction_model_workspace/scripts

# Create output directory if it doesn't exist
mkdir -p ../results/trial_wise_glm

# Process all ROIs for this subject sequentially
FAILED_ROIS=()
SUCCESS_COUNT=0

for ROI in "${ROIS[@]}"; do
    echo ""
    echo "----------------------------------------------------------------"
    echo "Processing: Subject ${SUBJECT}, ROI ${ROI}"
    echo "----------------------------------------------------------------"
    echo ""

    python 02_trial_wise_glm.py \
        --subject ${SUBJECT} \
        --roi ${ROI} \
        --fmriprep_dir /storage/connectome/haba6030/fmriprep_out_original_v3 \
        --bids_dir /storage/connectome/haba6030/bids_editted \
        --derivatives_dir /scratch/connectome/haba6030/colorBlind/derivatives \
        --output_dir /scratch/connectome/haba6030/colorBlind/prediction_model_workspace/results/trial_wise_glm \
        --smoothing_fwhm 6.0 \
        --confounds_strategy motion

    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo "✅ Subject ${SUBJECT}, ROI ${ROI} completed successfully"
        ((SUCCESS_COUNT++))
    else
        echo "❌ Subject ${SUBJECT}, ROI ${ROI} failed with exit code: $EXIT_CODE"
        FAILED_ROIS+=("${ROI}")
    fi
    echo ""
done

echo ""
echo "=========================================="
echo "Subject ${SUBJECT} Summary"
echo "=========================================="
echo "Total ROIs: ${#ROIS[@]}"
echo "Successful: ${SUCCESS_COUNT}"
echo "Failed: ${#FAILED_ROIS[@]}"
if [ ${#FAILED_ROIS[@]} -gt 0 ]; then
    echo "Failed ROIs: ${FAILED_ROIS[@]}"
fi
echo "End Time: $(date)"
echo "=========================================="

# Exit with error if any ROI failed
if [ ${#FAILED_ROIS[@]} -gt 0 ]; then
    exit 1
else
    exit 0
fi
