#!/usr/bin/env bash
set -euo pipefail

################################################################################
# Run-wise Quality Check Script
#
# Purpose: Diagnose run-level issues to minimize run rejection
# Metrics:
#   1. Registration quality (T1brain→boldref overlap)
#   2. ROI coverage (V1-V4 voxels within brain mask)
#   3. Motion (FD, DVARS from confounds)
#   4. Dropout proxy (low-intensity voxels in ROI)
#
# Output: TSV table for each subject with per-run, per-ROI diagnostics
#
# Usage:
#   bash qc_runwise.sh <subject_id>
#   Example: bash qc_runwise.sh 07
#
# To run on server:
#   1. Upload: scp qc_runwise.sh haba6030@node2:/scratch/connectome/haba6030/colorBlind/
#   2. Run: bash qc_runwise.sh 07
################################################################################

# Subject ID (passed as argument or default to 07)
SUBJECT="${1:-07}"

# ============================================================================
# DIRECTORY CONFIGURATION - MODIFY THESE FOR YOUR SETUP
# ============================================================================

# fMRIPrep output directory
# Options:
#   - /storage/connectome/haba6030/fmriprep_out_original_v2    (original data)
#   - /storage/connectome/haba6030/fmriprep_out_deoblique_v2   (deoblique v2, RECOMMENDED)
OUT="/storage/connectome/haba6030/fmriprep_out_deoblique_v2/sub-${SUBJECT}"

# Wang atlas directory (probabilistic maps)
WANG_DIR="/scratch/connectome/haba6030/colorBlind/ProbAtlas_v4_2mm/subj_vol_all"

# Singularity/Apptainer configuration
APPTAINER="/usr/local/bin/singularity"
IMG="/home/connectome/haba6030/fmriprep-23.2.3.sif"

# Output QC table
QC_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/QC"
mkdir -p "${QC_DIR}"
QC_TSV="${QC_DIR}/qc_runwise_sub-${SUBJECT}.tsv"

# ============================================================================
# WANG ATLAS ROI CONFIGURATION
# ============================================================================

# Wang ROI mapping (combine ventral/dorsal into single V1, V2, V3)
# ROI codes from ProbAtlas_v4/ROIfiles_Labeling.txt:
#   01=V1v, 02=V1d, 03=V2v, 04=V2d, 05=V3v, 06=V3d, 07=hV4
V1_CODES=(1 2)
V2_CODES=(3 4)
V3_CODES=(5 6)
V4_CODES=(7)

# ROI processing parameters
PROB_THR=50         # Probability threshold (50 = 50th percentile)
                    # Try 20/35/50 for sensitivity analysis
DILATE=2            # Dilation iterations (1-2 recommended)
                    # Increases ROI size to recover boundary voxels

# ============================================================================
# INPUT FILE PATHS
# ============================================================================

# Anatomical files (subject-level)
T1BRAIN="${OUT}/anat/sub-${SUBJECT}_acq-mprage_desc-brain_mask.nii.gz"
MNI2T1="${OUT}/anat/sub-${SUBJECT}_acq-mprage_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5"

# Verify required files exist
if [ ! -f "${T1BRAIN}" ]; then
    echo "❌ ERROR: T1 brain mask not found: ${T1BRAIN}"
    exit 1
fi

if [ ! -f "${MNI2T1}" ]; then
    echo "❌ ERROR: MNI→T1w transform not found: ${MNI2T1}"
    exit 1
fi

if [ ! -d "${WANG_DIR}" ]; then
    echo "❌ ERROR: Wang atlas directory not found: ${WANG_DIR}"
    exit 1
fi

echo "================================================================================"
echo "Run-wise Quality Check - Sub-${SUBJECT}"
echo "================================================================================"
echo "Configuration:"
echo "  fMRIPrep output:  ${OUT}"
echo "  Wang atlas:       ${WANG_DIR}"
echo "  QC output:        ${QC_TSV}"
echo "  Prob threshold:   ${PROB_THR}"
echo "  Dilation:         ${DILATE} iterations"
echo ""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

# Function: Summarize FD/DVARS from confounds TSV
summarize_confounds () {
  local TSV="$1"
  python3 - "$TSV" <<'PYTHON_SCRIPT'
import pandas as pd
import numpy as np
import sys

tsv = sys.argv[1]
df = pd.read_csv(tsv, sep="\t")

def summarize_column(col):
    """Return (mean, p95) for a column, or (nan, nan) if missing/invalid"""
    if col not in df.columns:
        return (np.nan, np.nan)
    x = pd.to_numeric(df[col], errors="coerce").to_numpy()
    x = x[np.isfinite(x)]
    if x.size == 0:
        return (np.nan, np.nan)
    return (float(x.mean()), float(np.quantile(x, 0.95)))

fd_mean, fd_p95 = summarize_column("framewise_displacement")
dv_mean, dv_p95 = summarize_column("dvars")

print(f"{fd_mean}\t{fd_p95}\t{dv_mean}\t{dv_p95}")
PYTHON_SCRIPT
}

# Function: Build ROI and calculate QC metrics
make_roi_and_qc () {
    local ROI_NAME="$1"; shift
    local -a CODES=("$@")

    local RUN_TAG="sub${SUBJECT}_run${RUN}"

    # ========================================================================
    # Step 1: Build union of Wang probability maps in MNI space
    # ========================================================================
    local TMPMNI="/tmp/${RUN_TAG}_${ROI_NAME}_mni_prob.nii.gz"
    rm -f "${TMPMNI}"

    for CODE in "${CODES[@]}"; do
      for H in lh rh; do
        local F="${WANG_DIR}/perc_VTPM_vol_roi${CODE}_${H}.nii.gz"
        [[ -f "${F}" ]] || continue
        if [[ ! -f "${TMPMNI}" ]]; then
          cp "${F}" "${TMPMNI}"
        else
          fslmaths "${TMPMNI}" -add "${F}" "${TMPMNI}"
        fi
      done
    done

    if [[ ! -f "${TMPMNI}" ]]; then
        echo "nan\tnan\tnan\tnan\tnan"
        return
    fi

    # ========================================================================
    # Step 2: Transform MNI → T1w → boldref
    # ========================================================================
    ${APPTAINER} exec --cleanenv \
      -B /storage:/storage -B /scratch:/scratch "${IMG}" \
      antsApplyTransforms -d 3 \
        -i "${TMPMNI}" -r "${BOLDREF}" \
        -t ["${XFM}",1] \
        -t "${MNI2T1}" \
        -n Linear \
        -o /tmp/${RUN_TAG}_${ROI_NAME}_in_boldref_prob.nii.gz

    # ========================================================================
    # Step 3: Binarize, dilate, clip to brain mask
    # ========================================================================
    fslmaths /tmp/${RUN_TAG}_${ROI_NAME}_in_boldref_prob.nii.gz \
      -thr ${PROB_THR} -bin \
      /tmp/${RUN_TAG}_${ROI_NAME}_bin.nii.gz

    local ROI_BIN="/tmp/${RUN_TAG}_${ROI_NAME}_bin.nii.gz"
    local ROI_DIL="/tmp/${RUN_TAG}_${ROI_NAME}_dil.nii.gz"
    local ROI_FIN="/tmp/${RUN_TAG}_${ROI_NAME}_final.nii.gz"

    cp "${ROI_BIN}" "${ROI_DIL}"
    for i in $(seq 1 ${DILATE}); do
      fslmaths "${ROI_DIL}" -dilM "${ROI_DIL}"
    done

    fslmaths "${ROI_DIL}" -mas "${BMASK}" "${ROI_FIN}"

    # ========================================================================
    # Step 4: Calculate ROI coverage metrics
    # ========================================================================
    local TOTAL=$(fslstats "${ROI_FIN}" -V | awk '{print $1}')
    local INB=$(fslstats "${ROI_FIN}" -k "${BMASK}" -V | awk '{print $1}')
    local COV="nan"
    if [[ "${TOTAL}" != "0" ]]; then
      COV=$(python3 -c "t=${TOTAL}; i=${INB}; print(i/t if t>0 else float('nan'))")
    fi

    # ========================================================================
    # Step 5: Dropout proxy (low-intensity voxels)
    # ========================================================================
    # Calculate 10th percentile of boldref intensity within ROI
    local P10=$(fslstats "${BOLDREF}" -k "${ROI_FIN}" -P 10)

    # Fraction of ROI voxels below p10 threshold
    fslmaths "${BOLDREF}" -uthr "${P10}" -bin -mas "${ROI_FIN}" \
      /tmp/${RUN_TAG}_${ROI_NAME}_lowmask.nii.gz
    local LOW=$(fslstats /tmp/${RUN_TAG}_${ROI_NAME}_lowmask.nii.gz -V | awk '{print $1}')
    local LOWFR="nan"
    if [[ "${TOTAL}" != "0" ]]; then
      LOWFR=$(python3 -c "t=${TOTAL}; l=${LOW}; print(l/t if t>0 else float('nan'))")
    fi

    echo -e "${TOTAL}\t${INB}\t${COV}\t${P10}\t${LOWFR}"
}

# ============================================================================
# MAIN QC LOOP
# ============================================================================

# Initialize output table
echo -e "sub\trun\tcoreg_overlap_vox\troi\troi_total_vox\troi_in_brain_vox\troi_coverage\tp10\tlowfrac\tFD_mean\tFD_p95\tDVARS_mean\tDVARS_p95" > "${QC_TSV}"

# Loop over runs
for RUN in 1 2 3 4 5 6; do
  FUNC_DIR="${OUT}/func"
  BOLDREF="${FUNC_DIR}/sub-${SUBJECT}_task-rsvp_run-${RUN}_desc-coreg_boldref.nii.gz"
  BMASK="${FUNC_DIR}/sub-${SUBJECT}_task-rsvp_run-${RUN}_desc-brain_mask.nii.gz"
  XFM="${FUNC_DIR}/sub-${SUBJECT}_task-rsvp_run-${RUN}_from-boldref_to-T1w_mode-image_desc-coreg_xfm.txt"
  CONF="${FUNC_DIR}/sub-${SUBJECT}_task-rsvp_run-${RUN}_desc-confounds_timeseries.tsv"

  # Skip if any required file is missing
  if [[ ! -f "${BOLDREF}" || ! -f "${BMASK}" || ! -f "${XFM}" || ! -f "${CONF}" ]]; then
    echo "⚠️  Skipping run ${RUN}: Missing required files"
    continue
  fi

  echo "Processing run ${RUN}..."

  # =========================================================================
  # Metric 1: Registration quality (T1brain → boldref overlap)
  # =========================================================================
  ${APPTAINER} exec --cleanenv \
    -B /storage:/storage -B /scratch:/scratch "${IMG}" \
    antsApplyTransforms -d 3 \
      -i "${T1BRAIN}" -r "${BOLDREF}" \
      -t ["${XFM}",1] \
      -n NearestNeighbor \
      -o /tmp/sub${SUBJECT}_run${RUN}_T1brain_in_boldref.nii.gz

  COREGO=$(fslstats /tmp/sub${SUBJECT}_run${RUN}_T1brain_in_boldref.nii.gz \
    -k "${BMASK}" -V | awk '{print $1}')

  # =========================================================================
  # Metric 2: Motion (FD/DVARS)
  # =========================================================================
  MOT=$(summarize_confounds "${CONF}")

  # =========================================================================
  # Metric 3 & 4: ROI coverage and dropout (per ROI)
  # =========================================================================
  for ROI in V1 V2 V3 V4; do
    case "${ROI}" in
      V1) MET=$(make_roi_and_qc "V1" "${V1_CODES[@]}");;
      V2) MET=$(make_roi_and_qc "V2" "${V2_CODES[@]}");;
      V3) MET=$(make_roi_and_qc "V3" "${V3_CODES[@]}");;
      V4) MET=$(make_roi_and_qc "V4" "${V4_CODES[@]}");;
    esac
    echo -e "${SUBJECT}\t${RUN}\t${COREGO}\t${ROI}\t${MET}\t${MOT}" >> "${QC_TSV}"
  done

done

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "================================================================================"
echo "QC Complete - Sub-${SUBJECT}"
echo "================================================================================"
echo ""
echo "Output: ${QC_TSV}"
echo ""
echo "Next steps:"
echo "  1. Download QC table:"
echo "     scp haba6030@node2:${QC_TSV} ./"
echo ""
echo "  2. Analyze in Python/R to identify problematic runs:"
echo "     - Low coreg_overlap_vox → registration failure"
echo "     - Low roi_coverage → ROI/brain mask mismatch"
echo "     - High lowfrac → signal dropout"
echo "     - High FD/DVARS → motion artifacts"
echo ""
echo "  3. Run for all subjects:"
echo "     for SUB in 01 02 03 04 05 06 07 08 09 10; do"
echo "       bash qc_runwise.sh \$SUB"
echo "     done"
echo ""
echo "================================================================================"

cat "${QC_TSV}"
