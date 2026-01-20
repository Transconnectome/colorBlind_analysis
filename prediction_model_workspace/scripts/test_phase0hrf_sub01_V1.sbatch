#!/bin/bash
#SBATCH --job-name=test_phase0hrf
#SBATCH --qos=shared
#SBATCH --nodelist=node4
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/logs/test_phase0hrf_sub01_V1_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/logs/test_phase0hrf_sub01_V1_%j.err

echo "=========================================="
echo "Test: Trial-wise GLM with Phase 0 Method"
echo "Subject: sub-01"
echo "ROI: V1"
echo "Method: Phase 0 HRF+derivative + selected voxels + cosine confounds"
echo "Previous: Procrustes 0.002 (motion confounds)"
echo "Expected: Procrustes 0.002 → 0.01~0.05 (with cosine)"
echo "Date: $(date)"
echo "=========================================="

# Conda activation
eval "$(conda shell.bash hook)"
conda activate nilearn

# Python unbuffered output
export PYTHONUNBUFFERED=1

cd /scratch/connectome/haba6030/colorBlind/prediction_model_workspace/scripts

# Run with Phase 0 methodology (fully matched)
python 02_trial_wise_glm_phase0hrf.py \
    --subject 01 \
    --roi V1 \
    --smoothing_fwhm 0.0 \
    --confounds_strategy cosine \
    --phase0_dataset original_v3 \
    --phase0_timestamp baseline32_original_v3

echo ""
echo "=========================================="
echo "Test completed: $(date)"
echo "=========================================="
