#!/usr/bin/env bash
set -euo pipefail

################################################################################
# Improved Run-wise Quality Check Script
#
# Improvements:
#   1. Adaptive ROI threshold selection (20/35/50)
#   2. Dilation + brain mask clipping
#   3. Better dropout metrics (p10_ROI/median_brain, median_ROI/median_brain)
#   4. Works with existing fMRIPrep outputs (pre-completion)
#
# Usage: bash qc_runwise_improved.sh <subject_id> [fmriprep_base_dir]
#
# Examples:
#   bash qc_runwise_improved.sh 01
#   bash qc_runwise_improved.sh 01 /storage/connectome/haba6030/fmriprep_out_deoblique_v2
################################################################################

SUBJECT="${1:-07}"
FMRIPREP_BASE="${2:-/storage/connectome/haba6030/fmriprep_out_original_v3}"

# ============================================================================
# CONFIGURATION
# ============================================================================

# fMRIPrep output (works with any version that has boldref/mask)
OUT="${FMRIPREP_BASE}/sub-${SUBJECT}"

# Wang atlas directory
WANG_DIR="/scratch/connectome/haba6030/colorBlind/ProbAtlas_v4_2mm/subj_vol_all"

# Singularity
APPTAINER="/usr/local/bin/singularity"
IMG="/home/connectome/haba6030/fmriprep-23.2.3.sif"

# Output - Extract version from fMRIPrep directory name
FMRIPREP_VERSION=$(basename "${FMRIPREP_BASE}")  # e.g., "fmriprep_out_original_v3"
QC_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/QC_${FMRIPREP_VERSION}"
mkdir -p "${QC_DIR}"
QC_TSV="${QC_DIR}/qc_runwise_sub-${SUBJECT}.tsv"

# ROI configuration
V1_CODES=(1 2)
V2_CODES=(3 4)
V3_CODES=(5 6)
V4_CODES=(7)

# Adaptive threshold selection
THRESHOLDS=(50 35 20)  # Try in order: 50 -> 35 -> 20
MIN_VOXELS=10          # Minimum acceptable voxel count
DILATE=2               # Dilation iterations

# ============================================================================
# FILE VALIDATION
# ============================================================================

T1BRAIN="${OUT}/anat/sub-${SUBJECT}_acq-mprage_desc-brain_mask.nii.gz"
MNI2T1="${OUT}/anat/sub-${SUBJECT}_acq-mprage_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5"

if [ ! -f "${T1BRAIN}" ]; then
    echo "❌ ERROR: T1 brain mask not found: ${T1BRAIN}"
    exit 1
fi

if [ ! -f "${MNI2T1}" ]; then
    echo "❌ ERROR: MNI→T1w transform not found: ${MNI2T1}"
    exit 1
fi

if [ ! -d "${WANG_DIR}" ]; then
    echo "❌ ERROR: Wang atlas not found: ${WANG_DIR}"
    exit 1
fi

echo "================================================================================"
echo "Improved Run-wise QC - Sub-${SUBJECT}"
echo "================================================================================"
echo "Features:"
echo "  ✅ Adaptive ROI threshold (20/35/50)"
echo "  ✅ Dilation + brain mask clipping"
echo "  ✅ Improved dropout metrics"
echo ""
echo "Output: ${QC_TSV}"
echo "================================================================================"
echo ""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

# Function: Summarize confounds
summarize_confounds() {
    local TSV="$1"
    python3 - "$TSV" <<'PYTHON_SCRIPT'
import pandas as pd
import numpy as np
import sys

tsv = sys.argv[1]
df = pd.read_csv(tsv, sep="\t")

def summarize_column(col):
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

# Function: Build ROI with adaptive threshold selection
build_roi_adaptive() {
    local ROI_NAME="$1"; shift
    local -a CODES=("$@")
    local RUN_TAG="sub${SUBJECT}_run${RUN}"

    # ========================================================================
    # Step 1: Build union of Wang probability maps in MNI
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
        echo "nan\tnan\tnan\tnan\tnan\tnan"
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
        -o /tmp/${RUN_TAG}_${ROI_NAME}_prob.nii.gz

    # ========================================================================
    # Step 3: Adaptive threshold selection
    # ========================================================================
    local SELECTED_THR="nan"
    local ROI_FIN=""

    for THR in "${THRESHOLDS[@]}"; do
        local ROI_BIN="/tmp/${RUN_TAG}_${ROI_NAME}_thr${THR}_bin.nii.gz"
        local ROI_DIL="/tmp/${RUN_TAG}_${ROI_NAME}_thr${THR}_dil.nii.gz"
        local ROI_CLIP="/tmp/${RUN_TAG}_${ROI_NAME}_thr${THR}_final.nii.gz"

        # Binarize at threshold
        fslmaths /tmp/${RUN_TAG}_${ROI_NAME}_prob.nii.gz \
          -thr ${THR} -bin "${ROI_BIN}"

        # Dilate
        cp "${ROI_BIN}" "${ROI_DIL}"
        for i in $(seq 1 ${DILATE}); do
            fslmaths "${ROI_DIL}" -dilM "${ROI_DIL}"
        done

        # Clip to brain mask
        fslmaths "${ROI_DIL}" -mas "${BMASK}" "${ROI_CLIP}"

        # Check voxel count
        local NVOX=$(fslstats "${ROI_CLIP}" -V | awk '{print $1}')

        if (( $(echo "$NVOX >= $MIN_VOXELS" | bc -l) )); then
            SELECTED_THR=${THR}
            ROI_FIN="${ROI_CLIP}"
            break
        fi
    done

    # If all thresholds failed, use the lowest one anyway
    if [[ -z "${ROI_FIN}" ]]; then
        SELECTED_THR=20
        ROI_FIN="/tmp/${RUN_TAG}_${ROI_NAME}_thr20_final.nii.gz"
    fi

    # ========================================================================
    # Step 4: ROI coverage metrics
    # ========================================================================
    local TOTAL=$(fslstats "${ROI_FIN}" -V | awk '{print $1}')
    local INB=$(fslstats "${ROI_FIN}" -k "${BMASK}" -V | awk '{print $1}')
    local COV="nan"
    if [[ "${TOTAL}" != "0" ]]; then
        COV=$(python3 -c "print(${INB}/${TOTAL} if ${TOTAL}>0 else float('nan'))")
    fi

    # ========================================================================
    # Step 5: Improved dropout metrics
    # ========================================================================
    # Calculate median intensity in brain and ROI
    local MEDIAN_BRAIN=$(fslstats "${BOLDREF}" -k "${BMASK}" -P 50)
    local MEDIAN_ROI=$(fslstats "${BOLDREF}" -k "${ROI_FIN}" -P 50)
    local P10_ROI=$(fslstats "${BOLDREF}" -k "${ROI_FIN}" -P 10)

    # metric1 = p10_ROI / median_brain
    # metric2 = median_ROI / median_brain
    local METRIC1=$(python3 -c "print(${P10_ROI}/${MEDIAN_BRAIN} if ${MEDIAN_BRAIN}>0 else float('nan'))")
    local METRIC2=$(python3 -c "print(${MEDIAN_ROI}/${MEDIAN_BRAIN} if ${MEDIAN_BRAIN}>0 else float('nan'))")

    echo -e "${SELECTED_THR}\t${TOTAL}\t${INB}\t${COV}\t${METRIC1}\t${METRIC2}"
}

# ============================================================================
# MAIN QC LOOP
# ============================================================================

# Initialize TSV header (WITH DENOMINATORS!)
echo -e "sub\trun\toverlap_vox\tbmask_vox\tt1mask_vox\toverlap_frac\tdice\troi\troi_thr\troi_vox\troi_in_brain_vox\troi_coverage\tdropout_metric1\tdropout_metric2\tFD_mean\tFD_p95\tDVARS_mean\tDVARS_p95" > "${QC_TSV}"

for RUN in 1 2 3 4 5 6; do
    FUNC_DIR="${OUT}/func"
    BOLDREF="${FUNC_DIR}/sub-${SUBJECT}_task-rsvp_run-${RUN}_desc-coreg_boldref.nii.gz"
    BMASK="${FUNC_DIR}/sub-${SUBJECT}_task-rsvp_run-${RUN}_desc-brain_mask.nii.gz"
    XFM="${FUNC_DIR}/sub-${SUBJECT}_task-rsvp_run-${RUN}_from-boldref_to-T1w_mode-image_desc-coreg_xfm.txt"
    CONF="${FUNC_DIR}/sub-${SUBJECT}_task-rsvp_run-${RUN}_desc-confounds_timeseries.tsv"

    # Skip if missing
    if [[ ! -f "${BOLDREF}" || ! -f "${BMASK}" || ! -f "${XFM}" || ! -f "${CONF}" ]]; then
        echo "⚠️  Run ${RUN}: Missing files, skipping"
        continue
    fi

    echo "Processing run ${RUN}..."

    # =========================================================================
    # Registration quality (WITH DENOMINATORS!)
    # =========================================================================
    ${APPTAINER} exec --cleanenv \
      -B /storage:/storage -B /scratch:/scratch "${IMG}" \
      antsApplyTransforms -d 3 \
        -i "${T1BRAIN}" -r "${BOLDREF}" \
        -t ["${XFM}",1] \
        -n NearestNeighbor \
        -o /tmp/sub${SUBJECT}_run${RUN}_T1brain_in_boldref.nii.gz

    # Critical metrics with denominators
    OVERLAP_VOX=$(fslstats /tmp/sub${SUBJECT}_run${RUN}_T1brain_in_boldref.nii.gz \
      -k "${BMASK}" -V | awk '{print $1}')
    BMASK_VOX=$(fslstats "${BMASK}" -V | awk '{print $1}')
    T1MASK_VOX=$(fslstats /tmp/sub${SUBJECT}_run${RUN}_T1brain_in_boldref.nii.gz -V | awk '{print $1}')

    # Calculate overlap fraction and Dice
    OVERLAP_FRAC=$(python3 -c "print(${OVERLAP_VOX}/${BMASK_VOX} if ${BMASK_VOX}>0 else 0)")
    DICE=$(python3 -c "print(2*${OVERLAP_VOX}/(${BMASK_VOX}+${T1MASK_VOX}) if (${BMASK_VOX}+${T1MASK_VOX})>0 else 0)")

    # =========================================================================
    # Motion metrics
    # =========================================================================
    MOT=$(summarize_confounds "${CONF}")

    # =========================================================================
    # ROI metrics (adaptive threshold + improved dropout)
    # =========================================================================
    for ROI in V1 V2 V3 V4; do
        case "${ROI}" in
            V1) MET=$(build_roi_adaptive "V1" "${V1_CODES[@]}");;
            V2) MET=$(build_roi_adaptive "V2" "${V2_CODES[@]}");;
            V3) MET=$(build_roi_adaptive "V3" "${V3_CODES[@]}");;
            V4) MET=$(build_roi_adaptive "V4" "${V4_CODES[@]}");;
        esac
        echo -e "${SUBJECT}\t${RUN}\t${OVERLAP_VOX}\t${BMASK_VOX}\t${T1MASK_VOX}\t${OVERLAP_FRAC}\t${DICE}\t${ROI}\t${MET}\t${MOT}" >> "${QC_TSV}"
    done

    echo "  ✅ Run ${RUN} complete"
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
echo "Columns:"
echo "  - sub, run, roi: Identifiers"
echo "  - coreg_overlap_vox: T1brain ∩ BOLD brain mask (voxels)"
echo "  - roi_thr: Selected threshold (50/35/20)"
echo "  - roi_vox: Total ROI voxels after dilation+clip"
echo "  - roi_in_brain_vox: ROI voxels within brain mask"
echo "  - roi_coverage: roi_in_brain_vox / roi_vox"
echo "  - dropout_metric1: p10_ROI / median_brain (lower = more dropout)"
echo "  - dropout_metric2: median_ROI / median_brain (lower = more dropout)"
echo "  - FD_mean, FD_p95: Motion (framewise displacement)"
echo "  - DVARS_mean, DVARS_p95: Signal variance"
echo ""
echo "Interpretation:"
echo "  ⚠️  Low coreg_overlap_vox → Registration failure"
echo "  ⚠️  Low roi_coverage → ROI/brain mask mismatch"
echo "  ⚠️  dropout_metric1 < 0.5 → Severe signal dropout in ROI"
echo "  ⚠️  dropout_metric2 < 0.7 → Moderate signal dropout in ROI"
echo "  ⚠️  FD_mean > 0.5 or FD_p95 > 1.0 → Excessive motion"
echo ""
echo "Next steps:"
echo "  1. Download: scp haba6030@node2:${QC_TSV} ./"
echo "  2. Analyze in Python/R to identify problematic runs"
echo "  3. Run for all subjects:"
echo "     for SUB in 01 02 03 05 06 07 08 09 10; do"
echo "       bash qc_runwise_improved.sh \$SUB"
echo "     done"
echo ""
echo "================================================================================"

cat "${QC_TSV}"
