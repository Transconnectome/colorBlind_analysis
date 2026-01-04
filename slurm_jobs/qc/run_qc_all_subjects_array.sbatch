#!/bin/bash
#SBATCH --job-name=qc_original_v3
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --array=1-10
#SBATCH --output=logs/qc_original_v3_%A_%a.out
#SBATCH --error=logs/qc_original_v3_%A_%a.err

################################################################################
# QC Analysis for NEW fMRIPrep Output (--fs-no-reconall version)
# SLURM Array Job - Runs all 10 subjects in parallel
#
# Usage: sbatch run_qc_all_subjects_array.sbatch
################################################################################

set -e

# Subject mapping (array index 1-10 -> subject 01-10)
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
SUBJECT_ID=${SUBJECTS[$((SLURM_ARRAY_TASK_ID - 1))]}

# Paths
FMRIPREP_DIR="/storage/connectome/haba6030/fmriprep_out_original_v3"
QC_SCRIPT="/scratch/connectome/haba6030/colorBlind/qc_runwise_improved.sh"
WORK_DIR="/scratch/connectome/haba6030/colorBlind"

echo "================================================================================"
echo "QC Analysis - Subject ${SUBJECT_ID}"
echo "================================================================================"
echo ""
echo "Job ID:             ${SLURM_JOB_ID}"
echo "Array Task ID:      ${SLURM_ARRAY_TASK_ID}"
echo "Subject:            ${SUBJECT_ID}"
echo "Node:               $(hostname)"
echo "fMRIPrep directory: ${FMRIPREP_DIR}"
echo "QC script:          ${QC_SCRIPT}"
echo ""

# Change to working directory
cd "${WORK_DIR}"

# Check if fMRIPrep output exists for this subject
SUBJECT_DIR="${FMRIPREP_DIR}/sub-${SUBJECT_ID}"
if [ ! -d "${SUBJECT_DIR}" ]; then
    echo "❌ ERROR: Subject directory not found: ${SUBJECT_DIR}"
    exit 1
fi

# Check for BOLD files
BOLD_COUNT=$(ls ${SUBJECT_DIR}/func/*_space-MNI*_desc-preproc_bold.nii.gz 2>/dev/null | wc -l)
echo "BOLD files found: ${BOLD_COUNT}/6"

if [ "${BOLD_COUNT}" -eq 0 ]; then
    echo "❌ ERROR: No BOLD files found for sub-${SUBJECT_ID}"
    exit 1
fi

# Run QC script
echo ""
echo "Running QC..."
echo "--------------------------------------------------------------------------------"

bash "${QC_SCRIPT}" "${SUBJECT_ID}" "${FMRIPREP_DIR}"

# Check output
QC_OUTPUT_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/QC_fmriprep_out_original_v3"
QC_TSV="${QC_OUTPUT_DIR}/qc_runwise_sub-${SUBJECT_ID}.tsv"

if [ -f "${QC_TSV}" ]; then
    echo ""
    echo "✅ QC completed successfully"
    echo "   Output: ${QC_TSV}"

    # Show summary
    echo ""
    echo "Quick Summary:"
    LINES=$(wc -l < "${QC_TSV}")
    echo "   Total measurements: $((LINES - 1))"  # Exclude header

    # Count ROI_ZERO (roi_vox = 0)
    ROI_ZERO=$(awk -F'\t' 'NR>1 && $10==0 {count++} END {print count+0}' "${QC_TSV}")
    echo "   ROI_ZERO: ${ROI_ZERO}"

    # Mean Dice (column 7)
    MEAN_DICE=$(awk -F'\t' 'NR>1 && $7!="nan" {sum+=$7; count++} END {if(count>0) print sum/count; else print "N/A"}' "${QC_TSV}")
    echo "   Mean Dice: ${MEAN_DICE}"
else
    echo ""
    echo "❌ ERROR: QC output file not created: ${QC_TSV}"
    exit 1
fi

echo ""
echo "================================================================================"
echo "Sub-${SUBJECT_ID} QC COMPLETED"
echo "================================================================================"
