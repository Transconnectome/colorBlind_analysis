#!/bin/bash
#SBATCH --job-name=roi_masks
#SBATCH --nodelist=node2
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16GB
#SBATCH --time=1:00:00
#SBATCH --output=logs/roi_creation/create_centralized_roi_masks_%j.out
#SBATCH --error=logs/roi_creation/create_centralized_roi_masks_%j.err

# ============================================================================
# SLURM Batch Script: Create Centralized ROI Masks
# ============================================================================
#
# Purpose:
#   Create centralized ROI masks for both probabilistic and non-probabilistic
#   versions that will be used across all subjects.
#
# Output:
#   - roi_pipeline_deob_prob/ (probabilistic version)
#   - roi_pipeline_deob_Noprob/ (non-probabilistic version)
#
# Usage:
#   sbatch run_create_centralized_roi_masks.sbatch
#
# ============================================================================

echo "================================================================"
echo "Creating Centralized ROI Masks"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Start: $(date)"
echo "================================================================"

# Create log directory if it doesn't exist
mkdir -p logs/roi_creation

# Activate conda environment
echo ""
echo "Activating conda environment..."
source ~/.bashrc
conda activate nilearn

echo ""
echo "Python version:"
python --version

echo ""
echo "================================================================"
echo "Running ROI mask creation script..."
echo "================================================================"
echo ""

# Run the script to create both prob and nonprob versions
python create_centralized_roi_masks.py --version both

# Check exit status
EXIT_CODE=$?

echo ""
echo "================================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ ROI mask creation completed successfully!"
    echo ""
    echo "Output directories:"
    echo "  - roi_pipeline_deob_prob/"
    echo "  - roi_pipeline_deob_Noprob/"
    echo ""
    echo "Created masks:"
    echo ""
    echo "Probabilistic version:"
    ls -lh roi_pipeline_deob_prob/*.nii.gz 2>/dev/null || echo "  (no files found)"
    echo ""
    echo "Non-probabilistic version:"
    ls -lh roi_pipeline_deob_Noprob/*.nii.gz 2>/dev/null || echo "  (no files found)"
else
    echo "✗ ROI mask creation failed (exit code: ${EXIT_CODE})"
    echo "Check error log: logs/roi_creation/create_centralized_roi_masks_${SLURM_JOB_ID}.err"
fi
echo "================================================================"
echo ""
echo "Completion time: $(date)"
echo "================================================================"

exit $EXIT_CODE
