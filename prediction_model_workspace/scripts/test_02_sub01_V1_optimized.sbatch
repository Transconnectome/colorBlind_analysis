#!/bin/bash
#SBATCH --job-name=test_trial_glm_opt
#SBATCH --qos=shared
#SBATCH --nodelist=node4
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/logs/test_trial_glm_opt_sub01_V1_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/logs/test_trial_glm_opt_sub01_V1_%j.err

# Optimized test: 6 GLM fittings instead of 432
# Expected time: ~10-15 minutes (vs 2+ hours)

echo "=========================================="
echo "Test: OPTIMIZED Trial-wise GLM"
echo "Subject: sub-01"
echo "ROI: V1"
echo "Optimization: 6 fittings (72x faster)"
echo "Date: $(date)"
echo "=========================================="

# Conda activation
eval "$(conda shell.bash hook)"
conda activate nilearn

# Python unbuffered output
export PYTHONUNBUFFERED=1

# Change to scripts directory
cd /scratch/connectome/haba6030/colorBlind/prediction_model_workspace/scripts

# Run OPTIMIZED trial-wise GLM
echo ""
echo "Starting OPTIMIZED trial-wise GLM extraction..."
python 02_trial_wise_glm_optimized.py \
    --subject 01 \
    --roi V1 \
    --smoothing_fwhm 0.0 \
    --confounds_strategy motion

echo ""
echo "=========================================="
echo "Test completed: $(date)"
echo "=========================================="
