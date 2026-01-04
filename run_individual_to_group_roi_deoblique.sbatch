#!/bin/bash
#SBATCH -J roi_deoblique
#SBATCH -c 8
#SBATCH --mem=32G
#SBATCH -t 4:00:00
#SBATCH -o logs/roi_deoblique_%j.out
#SBATCH -e logs/roi_deoblique_%j.err
#SBATCH --nodelist=node2

#============================================================================
# ROI Pipeline for Deobliqued Data
#
# This pipeline creates MNI functional ROIs from deobliqued fMRIPrep output
#
# Usage:
#   # All subjects (01-10)
#   sbatch run_individual_to_group_roi_deoblique.sbatch
#
#   # Specific subjects
#   sbatch run_individual_to_group_roi_deoblique.sbatch --subjects "06 07 10"
#============================================================================

# Configuration
SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind
SCRIPT_NAME=individual_to_group_roi_pipeline.py
LOG_DIR=${SCRIPT_DIR}/logs
FMRIPREP_DIR=/storage/connectome/haba6030/fmriprep_out_deoblique
OUTPUT_DIR=derivatives/roi_deoblique

# Create log directory
mkdir -p ${LOG_DIR}

# Parse arguments
SUBJECTS=""
THRESHOLD=20

while [[ $# -gt 0 ]]; do
    case $1 in
        --subject)
            SUBJECTS="$2"
            shift 2
            ;;
        --subjects)
            SUBJECTS="$2"
            shift 2
            ;;
        --threshold)
            THRESHOLD="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: sbatch $0 [--subjects \"01 02 ...\"] [--threshold N]"
            exit 1
            ;;
    esac
done

# Print configuration
echo "============================================================================"
echo "ROI Pipeline - Deobliqued Data"
echo "============================================================================"
echo "Start time: $(date)"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Node: $(hostname)"
echo "Working directory: ${SCRIPT_DIR}"
echo ""
echo "Configuration:"
echo "  Subjects: ${SUBJECTS:-All (01-10)}"
echo "  Atlas threshold: ${THRESHOLD}"
echo "  fMRIPrep output: ${FMRIPREP_DIR}"
echo "  ROI output: ${OUTPUT_DIR}"
echo "============================================================================"
echo ""

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Check dependencies
echo "Checking dependencies..."
python -u -c "import ants; print(f'ANTsPy version: {ants.__version__}')" || {
    echo "ERROR: ANTsPy not found!"
    exit 1
}
python -u -c "import nibabel; print(f'Nibabel version: {nibabel.__version__}')"
python -u -c "import nilearn; print(f'Nilearn version: {nilearn.__version__}')"
echo ""

# Verify fMRIPrep output exists
if [ ! -d "${FMRIPREP_DIR}" ]; then
    echo "❌ ERROR: fMRIPrep output not found: ${FMRIPREP_DIR}"
    echo "Please run fMRIPrep first (run_fmriprep_deoblique.sbatch)"
    exit 1
fi

# Change to script directory
cd ${SCRIPT_DIR}

# Create modified Python script to use deobliqued data
cat > individual_to_group_roi_pipeline_deoblique.py << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
"""
ROI Pipeline for Deobliqued Data

Uses deobliqued fMRIPrep output for accurate ROI generation.
"""

# Read the original script and modify FMRIPREP_DIR
import sys
with open('individual_to_group_roi_pipeline.py', 'r') as f:
    script_content = f.read()

# Replace fMRIPrep directory path
script_content = script_content.replace(
    "FMRIPREP_DIR = Path('/storage/connectome/haba6030/fmriprep_out_new')",
    "FMRIPREP_DIR = Path('/storage/connectome/haba6030/fmriprep_out_deoblique')"
)

# Replace output directory
script_content = script_content.replace(
    "BASE_OUTPUT_DIR = Path('/scratch/connectome/haba6030/colorBlind/derivatives/roi_doubleT')",
    "BASE_OUTPUT_DIR = Path('/scratch/connectome/haba6030/colorBlind/derivatives/roi_deoblique')"
)

# Execute modified script
exec(script_content)
PYTHON_SCRIPT

# Run pipeline
echo "============================================================================"
echo "Running ROI Pipeline"
echo "============================================================================"
echo ""

if [ -z "${SUBJECTS}" ]; then
    # Run all subjects
    echo "Processing all subjects (01-10)..."
    python -u individual_to_group_roi_pipeline_deoblique.py --threshold ${THRESHOLD}
else
    # Run specific subject(s)
    echo "Processing subject(s): ${SUBJECTS}..."
    python -u individual_to_group_roi_pipeline_deoblique.py --subjects ${SUBJECTS} --threshold ${THRESHOLD}
fi

EXIT_CODE=$?

# Print completion message
echo ""
echo "============================================================================"
echo "Job completed"
echo "============================================================================"
echo "End time: $(date)"
echo "Exit code: ${EXIT_CODE}"
echo ""

if [ ${EXIT_CODE} -eq 0 ]; then
    echo "✅ SUCCESS!"
    echo ""
    echo "Results location:"
    echo "  MNI ROIs:        ${SCRIPT_DIR}/${OUTPUT_DIR}/sub-*/*_roi.nii.gz"
    echo "  Summary CSV:     ${SCRIPT_DIR}/${OUTPUT_DIR}/roi_summary.csv"
    echo "  Visualizations:  ${SCRIPT_DIR}/${OUTPUT_DIR}/sub-*/figures/*.png"
    echo ""
    echo "ROI Usage:"
    echo "  For ALL analyses: Use *_roi.nii.gz files"
    echo "  These are MNI functional space ROIs with:"
    echo "    - Deobliqued data (0-5° obliquity)"
    echo "    - Individual anatomy preserved"
    echo "    - Accurate spatial normalization"
    echo ""
    echo "Compare with original (oblique) ROIs:"
    echo "  Original: derivatives/roi_doubleT/sub-06/figures/V3_overlay_mni_func.png"
    echo "  Deoblique: ${OUTPUT_DIR}/sub-06/figures/V3_overlay_mni_func.png"
    echo ""
    echo "Download results:"
    echo "  scp -r haba6030@node2:${SCRIPT_DIR}/${OUTPUT_DIR}/ ./"
else
    echo "❌ FAILED with exit code ${EXIT_CODE}"
    echo "Check error log: ${LOG_DIR}/roi_deoblique_${SLURM_JOB_ID}.err"
fi

echo "============================================================================"

exit ${EXIT_CODE}
