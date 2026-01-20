#!/bin/bash
#SBATCH --job-name=test_trial_glm_sub01
#SBATCH --qos=shared
#SBATCH --nodelist=node4
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/logs/test_trial_glm_sub01_V1_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/logs/test_trial_glm_sub01_V1_%j.err

# Test execution for sub-01 V1 with 0mm smoothing (matching Phase 0)

echo "=========================================="
echo "Test: Trial-wise GLM with 0mm smoothing"
echo "Subject: sub-01"
echo "ROI: V1"
echo "Date: $(date)"
echo "=========================================="

# Conda activation
eval "$(conda shell.bash hook)"
conda activate nilearn

# Python unbuffered output
export PYTHONUNBUFFERED=1

# Change to scripts directory
cd /scratch/connectome/haba6030/colorBlind/prediction_model_workspace/scripts

# Run trial-wise GLM (smoothing_fwhm=0.0 is now default)
echo ""
echo "Starting trial-wise GLM extraction..."
python 02_trial_wise_glm.py \
    --subject 01 \
    --roi V1 \
    --smoothing_fwhm 0.0 \
    --confounds_strategy motion

echo ""
echo "=========================================="
echo "Test completed: $(date)"
echo "=========================================="
