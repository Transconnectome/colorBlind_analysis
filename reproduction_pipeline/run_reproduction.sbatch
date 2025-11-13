#!/bin/bash
#SBATCH -J reproduce_all
#SBATCH -c 8
#SBATCH --mem=128G
#SBATCH -t 4:00:00
#SBATCH --nodelist=node2
#SBATCH -o logs/reproduce_%j.out
#SBATCH -e logs/reproduce_%j.err

# ==============================================================================
# Reproduction Pipeline SLURM Script
# ==============================================================================
# This script reproduces the documented color reconstruction results:
# - V2: 52.4° novel error (BEST)
# - V1: 64.1° novel error
# - hV4: 75.0° novel error
#
# Usage:
#   sbatch run_reproduction.sbatch
# ==============================================================================

echo "========================================================================"
echo "Color Reconstruction Reproduction Pipeline"
echo "========================================================================"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Node: ${SLURM_NODELIST}"
echo "Started: $(date)"
echo "========================================================================"
echo

# Activate conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate nilearn

# Create logs directory
mkdir -p logs

# Navigate to reproduction pipeline directory
cd /scratch/connectome/haba6030/colorBlind/reproduction_pipeline

# ==============================================================================
# Step 1: Build ROI Masks
# ==============================================================================

echo "========================================================================"
echo "STEP 1: Building ROI Masks"
echo "========================================================================"
echo

python build_rois_reproduction.py

if [ $? -ne 0 ]; then
    echo "ERROR: ROI building failed!"
    exit 1
fi

echo
echo "✓ ROI masks created successfully"
echo

# ==============================================================================
# Step 2: Validate ROI Masks (OPTIONAL - for quality control)
# ==============================================================================

echo "========================================================================"
echo "STEP 2: Validating ROI Masks (optional QC)"
echo "========================================================================"
echo "This verifies ROI quality and checks for additional zero-signal voxels"
echo

# Uncomment to run validation step
# python validate_and_fix_rois.py
#
# if [ $? -ne 0 ]; then
#     echo "WARNING: ROI validation reported issues (continuing anyway)"
# fi

echo "Skipping optional validation (ROIs already have EPI mask applied)"
echo

# ==============================================================================
# Step 3: Run Reconstruction for Each ROI
# ==============================================================================

echo "========================================================================"
echo "STEP 3: Running Reconstruction Analysis"
echo "========================================================================"
echo

# V2 (best performance)
echo "Running V2..."
python run_reconstruction_reproduction.py --roi V2
V2_EXIT=$?
echo

# V1
echo "Running V1..."
python run_reconstruction_reproduction.py --roi V1
V1_EXIT=$?
echo

# hV4
echo "Running hV4..."
python run_reconstruction_reproduction.py --roi hV4
HV4_EXIT=$?
echo

# ==============================================================================
# Step 4: Summary
# ==============================================================================

echo "========================================================================"
echo "RESULTS SUMMARY"
echo "========================================================================"
echo

if [ -f "derivatives/sub-01/fir_reconstruction_reproduction/V2_universal_hrf/summary.csv" ]; then
    echo "V2 Results:"
    cat derivatives/sub-01/fir_reconstruction_reproduction/V2_universal_hrf/summary.csv
    echo
fi

if [ -f "derivatives/sub-01/fir_reconstruction_reproduction/V1_universal_hrf/summary.csv" ]; then
    echo "V1 Results:"
    cat derivatives/sub-01/fir_reconstruction_reproduction/V1_universal_hrf/summary.csv
    echo
fi

if [ -f "derivatives/sub-01/fir_reconstruction_reproduction/hV4_universal_hrf/summary.csv" ]; then
    echo "hV4 Results:"
    cat derivatives/sub-01/fir_reconstruction_reproduction/hV4_universal_hrf/summary.csv
    echo
fi

# ==============================================================================
# Exit Status
# ==============================================================================

echo "========================================================================"
echo "EXIT STATUS"
echo "========================================================================"
echo "V2:  Exit code $V2_EXIT"
echo "V1:  Exit code $V1_EXIT"
echo "hV4: Exit code $HV4_EXIT"
echo
echo "Finished: $(date)"
echo "========================================================================"

# Exit with error if any analysis failed
if [ $V2_EXIT -ne 0 ] || [ $V1_EXIT -ne 0 ] || [ $HV4_EXIT -ne 0 ]; then
    echo "One or more analyses failed!"
    exit 1
fi

echo "All analyses completed successfully!"
exit 0
