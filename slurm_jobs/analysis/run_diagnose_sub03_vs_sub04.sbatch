#!/bin/bash
#SBATCH --job-name=diagnose_sub03
#SBATCH --output=logs/diagnose_sub03_%j.out
#SBATCH --error=logs/diagnose_sub03_%j.err
#SBATCH --time=1:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --qos=shared
#SBATCH --nodelist=node2

################################################################################
# Diagnostic Analysis: Why Sub-03 Failed but Sub-04 Succeeded
#
# Purpose: Systematically compare sub-03 vs sub-04 to identify the root cause
#          of registration failure
#
# Analysis phases:
#   1. Raw data quality (voxel size, SNR, orientation)
#   2. BBR registration matrices and cost functions
#   3. BIDS metadata comparison
#   4. Brain mask and signal coverage
#
# Output: sub03_vs_sub04_diagnosis.txt + visualization PNGs
################################################################################

set -e

echo "================================================================================"
echo "Diagnostic Analysis: Sub-03 (Failed) vs Sub-04 (Succeeded)"
echo "================================================================================"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Node: ${SLURM_NODELIST}"
echo "Start time: $(date)"
echo ""
echo "Goal: Identify why sub-03 registration failed (0.4% V1 overlap)"
echo "      while sub-04 succeeded (74% V1 overlap) despite higher obliquity"
echo "================================================================================"
echo ""

# Working directory
cd /scratch/connectome/haba6030/colorBlind

# Create output directory
mkdir -p diagnostics
OUTPUT_FILE="diagnostics/sub03_vs_sub04_diagnosis_$(date +%Y%m%d_%H%M%S).txt"

# Redirect all output to file
exec > >(tee -a ${OUTPUT_FILE})
exec 2>&1

echo "Output will be saved to: ${OUTPUT_FILE}"
echo ""

# ============================================================================
# PHASE 1: Raw Data Quality Comparison
# ============================================================================

echo ""
echo "================================================================================"
echo "PHASE 1: Raw Data Quality Comparison"
echo "================================================================================"
echo ""

BIDS_DIR="/storage/connectome/haba6030/bids_editted"

echo "--- Sub-03 BOLD Data ---"
echo ""

if [ -f "${BIDS_DIR}/sub-03/func/sub-03_task-rsvp_run-1_bold.nii.gz" ]; then
    echo "Basic info:"
    3dinfo -n4 -d3 -orient -obliquity "${BIDS_DIR}/sub-03/func/sub-03_task-rsvp_run-1_bold.nii.gz" 2>/dev/null || echo "  3dinfo failed"

    echo ""
    echo "Data range:"
    3dBrickStat -min -max "${BIDS_DIR}/sub-03/func/sub-03_task-rsvp_run-1_bold.nii.gz" 2>/dev/null || echo "  3dBrickStat failed"

    echo ""
    echo "Automask coverage:"
    3dAutomask -prefix /tmp/sub03_automask.nii.gz "${BIDS_DIR}/sub-03/func/sub-03_task-rsvp_run-1_bold.nii.gz" 2>/dev/null
    3dBrickStat -count -non-zero /tmp/sub03_automask.nii.gz 2>/dev/null || echo "  Automask failed"
else
    echo "⚠️  BOLD file not found"
fi

echo ""
echo "--- Sub-04 BOLD Data ---"
echo ""

if [ -f "${BIDS_DIR}/sub-04/func/sub-04_task-rsvp_run-1_bold.nii.gz" ]; then
    echo "Basic info:"
    3dinfo -n4 -d3 -orient -obliquity "${BIDS_DIR}/sub-04/func/sub-04_task-rsvp_run-1_bold.nii.gz" 2>/dev/null || echo "  3dinfo failed"

    echo ""
    echo "Data range:"
    3dBrickStat -min -max "${BIDS_DIR}/sub-04/func/sub-04_task-rsvp_run-1_bold.nii.gz" 2>/dev/null || echo "  3dBrickStat failed"

    echo ""
    echo "Automask coverage:"
    3dAutomask -prefix /tmp/sub04_automask.nii.gz "${BIDS_DIR}/sub-04/func/sub-04_task-rsvp_run-1_bold.nii.gz" 2>/dev/null
    3dBrickStat -count -non-zero /tmp/sub04_automask.nii.gz 2>/dev/null || echo "  Automask failed"
else
    echo "⚠️  BOLD file not found"
fi

# ============================================================================
# PHASE 2: fMRIPrep Registration Matrices
# ============================================================================

echo ""
echo "================================================================================"
echo "PHASE 2: fMRIPrep Registration Matrices"
echo "================================================================================"
echo ""

FMRIPREP_OUT="/storage/connectome/haba6030/fmriprep_out"

echo "--- Sub-03 BOLD→T1w Registration ---"
echo ""

SUB03_XFM=$(find ${FMRIPREP_OUT}/sub-03/func -name "*from-boldref_to-T1w*coreg_xfm.txt" 2>/dev/null | head -1)
if [ -f "${SUB03_XFM}" ]; then
    cat "${SUB03_XFM}"
else
    echo "⚠️  Transform file not found"
    echo "Searching for any xfm files:"
    find ${FMRIPREP_OUT}/sub-03/func -name "*xfm.txt" 2>/dev/null | head -5
fi

echo ""
echo "--- Sub-04 BOLD→T1w Registration ---"
echo ""

SUB04_XFM=$(find ${FMRIPREP_OUT}/sub-04/func -name "*from-boldref_to-T1w*coreg_xfm.txt" 2>/dev/null | head -1)
if [ -f "${SUB04_XFM}" ]; then
    cat "${SUB04_XFM}"
else
    echo "⚠️  Transform file not found"
    echo "Searching for any xfm files:"
    find ${FMRIPREP_OUT}/sub-04/func -name "*xfm.txt" 2>/dev/null | head -5
fi

# ============================================================================
# PHASE 3: BIDS Metadata Comparison
# ============================================================================

echo ""
echo "================================================================================"
echo "PHASE 3: BIDS Metadata Comparison"
echo "================================================================================"
echo ""

echo "--- Sub-03 JSON Metadata ---"
echo ""

if [ -f "${BIDS_DIR}/sub-03/func/sub-03_task-rsvp_run-1_bold.json" ]; then
    cat "${BIDS_DIR}/sub-03/func/sub-03_task-rsvp_run-1_bold.json" | python -m json.tool 2>/dev/null || cat "${BIDS_DIR}/sub-03/func/sub-03_task-rsvp_run-1_bold.json"
else
    echo "⚠️  JSON not found"
fi

echo ""
echo "--- Sub-04 JSON Metadata ---"
echo ""

if [ -f "${BIDS_DIR}/sub-04/func/sub-04_task-rsvp_run-1_bold.json" ]; then
    cat "${BIDS_DIR}/sub-04/func/sub-04_task-rsvp_run-1_bold.json" | python -m json.tool 2>/dev/null || cat "${BIDS_DIR}/sub-04/func/sub-04_task-rsvp_run-1_bold.json"
else
    echo "⚠️  JSON not found"
fi

echo ""
echo "--- Metadata Differences ---"
echo ""

if [ -f "${BIDS_DIR}/sub-03/func/sub-03_task-rsvp_run-1_bold.json" ] && \
   [ -f "${BIDS_DIR}/sub-04/func/sub-04_task-rsvp_run-1_bold.json" ]; then
    diff <(cat "${BIDS_DIR}/sub-03/func/sub-03_task-rsvp_run-1_bold.json" | sort) \
         <(cat "${BIDS_DIR}/sub-04/func/sub-04_task-rsvp_run-1_bold.json" | sort) || echo "  (Differences shown above)"
else
    echo "⚠️  Cannot compare - JSON files not found"
fi

# ============================================================================
# PHASE 4: Python Visualization and Analysis
# ============================================================================

echo ""
echo "================================================================================"
echo "PHASE 4: Python Visualization and Analysis"
echo "================================================================================"
echo ""

# Activate conda environment
source ~/.bashrc
conda activate nilearn

echo "Running Python diagnostic script..."
echo ""

if [ -f "DIAGNOSE_SUB03_REGISTRATION.py" ]; then
    python DIAGNOSE_SUB03_REGISTRATION.py

    # Move generated images to diagnostics folder
    if ls sub-*_registration_diagnosis.png 1> /dev/null 2>&1; then
        mv sub-*_registration_diagnosis.png diagnostics/
        echo ""
        echo "✅ Visualization images saved to diagnostics/"
    fi
else
    echo "⚠️  DIAGNOSE_SUB03_REGISTRATION.py not found"
    echo "   Please upload the script first"
fi

# ============================================================================
# PHASE 5: Brain Mask Coverage Analysis
# ============================================================================

echo ""
echo "================================================================================"
echo "PHASE 5: Brain Mask Coverage Analysis"
echo "================================================================================"
echo ""

echo "--- Sub-03 Brain Mask ---"
echo ""

SUB03_MASK="${FMRIPREP_OUT}/sub-03/func/sub-03_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz"
if [ -f "${SUB03_MASK}" ]; then
    3dinfo -n4 -ad3 "${SUB03_MASK}" 2>/dev/null
    echo ""
    echo "Mask coverage (voxel count):"
    3dBrickStat -count -non-zero "${SUB03_MASK}" 2>/dev/null
else
    echo "⚠️  Brain mask not found"
fi

echo ""
echo "--- Sub-04 Brain Mask ---"
echo ""

SUB04_MASK="${FMRIPREP_OUT}/sub-04/func/sub-04_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz"
if [ -f "${SUB04_MASK}" ]; then
    3dinfo -n4 -ad3 "${SUB04_MASK}" 2>/dev/null
    echo ""
    echo "Mask coverage (voxel count):"
    3dBrickStat -count -non-zero "${SUB04_MASK}" 2>/dev/null
else
    echo "⚠️  Brain mask not found"
fi

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "================================================================================"
echo "DIAGNOSTIC SUMMARY"
echo "================================================================================"
echo ""

echo "Analysis completed at: $(date)"
echo ""
echo "Output files:"
echo "  Text report: ${OUTPUT_FILE}"
echo "  Images:      diagnostics/sub-*_registration_diagnosis.png"
echo ""
echo "Key comparisons made:"
echo "  1. Raw BOLD data properties (voxel size, orientation, obliquity)"
echo "  2. Signal quality (intensity range, SNR)"
echo "  3. Registration transformation matrices"
echo "  4. BIDS metadata (acquisition parameters)"
echo "  5. Brain mask coverage in MNI space"
echo ""
echo "Next steps:"
echo "  1. Download and review: ${OUTPUT_FILE}"
echo "  2. Review visualization images"
echo "  3. Identify specific failure point"
echo "  4. Test targeted fix (DOF 9, different initialization, etc.)"
echo ""
echo "================================================================================"

# Cleanup
rm -f /tmp/sub03_automask.nii.gz /tmp/sub04_automask.nii.gz 2>/dev/null

echo ""
echo "Job complete: $(date)"
echo "================================================================================"

exit 0
