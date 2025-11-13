#!/bin/bash
#SBATCH --job-name=fir_recon_all_subjects
#SBATCH --output=slurm_logs/sub-%x-%j.out
#SBATCH --error=slurm_logs/sub-%x-%j.err
#SBATCH --time=4:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --nodelist=node2

# Multi-subject FIR reconstruction with Universal HRF method
# Usage: sbatch --export=SUBJECT=P01,ROI=V2,USE_PCA=1,N_COMPONENTS=20 run_all_subjects.sbatch
#        (Use P01 for pilot, 02-04 for test subjects)

# Navigate to project directory
cd /scratch/connectome/haba6030/colorBlind || exit 1

echo "=========================================="
echo "Job started: $(date)"
echo "Node: $(hostname)"
echo "Job ID: $SLURM_JOB_ID"
echo "Subject: $SUBJECT"
echo "ROI: $ROI"
echo "USE_PCA: $USE_PCA"
echo "N_COMPONENTS: $N_COMPONENTS"
echo "=========================================="

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Check if environment is activated
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate nilearn environment"
    exit 1
fi

echo "Conda environment activated: $(which python)"
echo "Python version: $(python --version)"

# Verify data exists (handle pilot vs test subjects)
# P01 = pilot (directory: sub-P01, files: sub-01_*, derivatives: sub-P01)
# 01-04 = test (directory: sub-XX, files: sub-XX_*, derivatives: sub-XX)
if [ "$SUBJECT" == "P01" ]; then
    FMRIPREP_DIR="/storage/connectome/haba6030/fmriprep_out/sub-P01"
    FILE_PREFIX="01"  # Pilot files are named sub-01_*
    DERIVATIVE_PREFIX="P01"  # derivatives/sub-P01/ (to distinguish from test sub-01)
else
    FMRIPREP_DIR="/storage/connectome/haba6030/fmriprep_out/sub-${SUBJECT}"
    FILE_PREFIX="${SUBJECT}"  # Test files are named sub-XX_*
    DERIVATIVE_PREFIX="${SUBJECT}"  # derivatives/sub-XX/
fi

if [ ! -d "$FMRIPREP_DIR" ]; then
    echo "ERROR: fMRIPrep data not found at $FMRIPREP_DIR"
    exit 1
fi

echo "fMRIPrep data found: $FMRIPREP_DIR"

# Step 1: Build ROI masks for this subject (if not already done)
echo "=========================================="
echo "Building ROI masks for ${SUBJECT}..."
echo "=========================================="

python build_roi_masks.py --subject $SUBJECT

ROI_BUILD_EXIT=$?
if [ $ROI_BUILD_EXIT -eq 0 ]; then
    echo "✓ ROI masks built successfully"
else
    echo "⚠ ROI mask building had issues (exit code: $ROI_BUILD_EXIT)"
    echo "  This might mean masks already exist or some atlas files are missing"
fi
echo ""

# Step 2: Check if the specific ROI mask exists
ROI_MASK_PATH="derivatives/sub-${DERIVATIVE_PREFIX}/roi/sub-${FILE_PREFIX}_${ROI}_mask.nii.gz"
if [ ! -f "$ROI_MASK_PATH" ]; then
    echo "=========================================="
    echo "SKIPPING: ROI mask not found"
    echo "=========================================="
    echo "Subject: ${SUBJECT}"
    echo "ROI: $ROI"
    echo "Expected path: $ROI_MASK_PATH"
    echo ""
    echo "Possible reasons:"
    echo "  1. Wang atlas files missing for this ROI"
    echo "  2. fMRIPrep reference image not found"
    echo "  3. ROI name not in Wang atlas (V1, V2, V3, hV4)"
    echo ""
    echo "Job will exit gracefully (not an error)"
    echo "=========================================="
    exit 0
fi

echo "✓ ROI mask found: $ROI_MASK_PATH"
echo ""

# Step 3: Build command with optional arguments
CMD="python fir_reconstruction_universal_hrf.py --subject $SUBJECT --roi $ROI"

if [ "$USE_PCA" == "1" ]; then
    CMD="$CMD --use-pca --n-components $N_COMPONENTS"
fi

if [ "$SAVE_ZMAPS" == "1" ]; then
    CMD="$CMD --save-zmaps"
fi

echo "Running: $CMD"
echo "=========================================="

# Run the analysis
$CMD

EXIT_CODE=$?

echo "=========================================="
echo "Job finished: $(date)"
echo "Exit code: $EXIT_CODE"
echo "=========================================="

exit $EXIT_CODE
