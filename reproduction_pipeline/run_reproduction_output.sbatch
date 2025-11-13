#!/bin/bash
#SBATCH -J reproduce_output
#SBATCH -c 8
#SBATCH --mem=128G
#SBATCH -t 4:00:00
#SBATCH --nodelist=node2
#SBATCH -o logs/reproduce_output_%j.out
#SBATCH -e logs/reproduce_output_%j.err

# ==============================================================================
# Reproduction Pipeline SLURM Script (OUTPUT Directory Version)
# ==============================================================================
# This script reproduces the documented color reconstruction results using
# the OLD data structure from /scratch/connectome/haba6030/colorBlind/output
#
# Target results:
# - V2: 52.4° novel error (BEST)
# - V1: 64.1° novel error
# - hV4: 75.0° novel error
#
# Usage:
#   sbatch run_reproduction_output.sbatch
# ==============================================================================

echo "========================================================================"
echo "Color Reconstruction Reproduction Pipeline (OUTPUT Directory)"
echo "========================================================================"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Node: ${SLURM_NODELIST}"
echo "Started: $(date)"
echo "Data source: /scratch/connectome/haba6030/colorBlind/output"
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
# Step 0: Verify Setup
# ==============================================================================

echo "========================================================================"
echo "STEP 0: Verifying Setup"
echo "========================================================================"
echo

python verify_setup_output.py

if [ $? -ne 0 ]; then
    echo "ERROR: Setup verification failed!"
    echo "Please check paths in config_reproduction_output.py"
    exit 1
fi

echo
echo "✓ Setup verified successfully"
echo

# ==============================================================================
# Step 1: Build ROI Masks
# ==============================================================================

echo "========================================================================"
echo "STEP 1: Building ROI Masks"
echo "========================================================================"
echo

python build_rois_reproduction_output.py

if [ $? -ne 0 ]; then
    echo "ERROR: ROI building failed!"
    exit 1
fi

echo
echo "✓ ROI masks created successfully"
echo

# ==============================================================================
# Step 2: Run Reconstruction for Each ROI
# ==============================================================================

echo "========================================================================"
echo "STEP 2: Running Reconstruction Analysis"
echo "========================================================================"
echo

# V2 (best performance)
echo "Running V2..."
python run_reconstruction_reproduction_output.py --roi V2
V2_EXIT=$?
echo

# V1
echo "Running V1..."
python run_reconstruction_reproduction_output.py --roi V1
V1_EXIT=$?
echo

# hV4
echo "Running hV4..."
python run_reconstruction_reproduction_output.py --roi hV4
HV4_EXIT=$?
echo

# ==============================================================================
# Step 3: Summary
# ==============================================================================

echo "========================================================================"
echo "RESULTS SUMMARY"
echo "========================================================================"
echo

OUTPUT_BASE="/scratch/connectome/haba6030/colorBlind/output/derivatives_reproduction/sub-01/fir_reconstruction_reproduction"

if [ -f "${OUTPUT_BASE}/V2_universal_hrf/summary.csv" ]; then
    echo "V2 Results:"
    cat "${OUTPUT_BASE}/V2_universal_hrf/summary.csv"
    echo
fi

if [ -f "${OUTPUT_BASE}/V1_universal_hrf/summary.csv" ]; then
    echo "V1 Results:"
    cat "${OUTPUT_BASE}/V1_universal_hrf/summary.csv"
    echo
fi

if [ -f "${OUTPUT_BASE}/hV4_universal_hrf/summary.csv" ]; then
    echo "hV4 Results:"
    cat "${OUTPUT_BASE}/hV4_universal_hrf/summary.csv"
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
echo
echo "Results saved to:"
echo "  ${OUTPUT_BASE}/"
exit 0
