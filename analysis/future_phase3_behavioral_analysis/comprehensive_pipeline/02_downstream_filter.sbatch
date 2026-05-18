#!/bin/bash
#SBATCH --job-name=cb_filt_down
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/future_phase3_behavioral_analysis/comprehensive_pipeline/logs/02_downstream_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/future_phase3_behavioral_analysis/comprehensive_pipeline/logs/02_downstream_%j.err
#SBATCH --time=24:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=3
#SBATCH --mem=24G
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --no-requeue
#SBATCH --open-mode=append

################################################################################
# Filter-Validation Downstream (sub-08/09 ses-02)
#
# Sequential single job (depends on 01_preprocess_filter.sbatch). HC reference
# is frozen: no re-extraction of HC amplitudes, no SRM retraining. We only run:
#
#   Step 1: GLM amplitudes (run_full_dataset_C010.py) for sub-08/09 ses-02
#   Step 2: SRM RDM projection onto frozen HC W (project_filtered_session.py)
#   Step 3: LORO + LOCO decoder comparison
#   Step 4: Comprehensive summary
################################################################################

set -e
PROJECT_ROOT=/scratch/connectome/haba6030/colorBlind
cd ${PROJECT_ROOT}

eval "$(conda shell.bash hook)"
conda activate nilearn

SUBJECTS=(08 09)
SESSION=02
DATASET=method3_header_mi
ROIS=(V1 V2 V3 V4)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "================================================================================"
echo "Filter-Validation Downstream"
echo "Job: ${SLURM_JOB_ID}  Node: ${SLURM_NODELIST}"
echo "Subjects: ${SUBJECTS[*]}  Session: ${SESSION}  Timestamp: ${TIMESTAMP}"
echo "Start: $(date)"
echo "================================================================================"

# -----------------------------------------------------------------------------
# Step 1: GLM amplitudes (Procrustes / C010)
# -----------------------------------------------------------------------------
echo ""
echo "--- Step 1: GLM amplitudes (C010) ---"
for SID in "${SUBJECTS[@]}"; do
    echo "[sub-${SID} ses-${SESSION}] running run_full_dataset_C010.py"
    python analysis/phase1_procrustes_decoding/run_full_dataset_C010.py \
        --subject ${SID} --session ${SESSION} --dataset ${DATASET} \
        || { echo "ERROR: amplitudes failed for sub-${SID}"; exit 1; }
done

# -----------------------------------------------------------------------------
# Step 2: SRM RDM via frozen-HC projection
# -----------------------------------------------------------------------------
echo ""
echo "--- Step 2: SRM RDM projection onto frozen HC W ---"
SRM_OUT=results/srm_filter_validation_${TIMESTAMP}
mkdir -p ${SRM_OUT}

python analysis/phase2_SRM_across_between/project_filtered_session.py \
    --subjects "${SUBJECTS[@]}" \
    --session ${SESSION} \
    --rois "${ROIS[@]}" \
    --dataset ${DATASET} \
    --hc-results-dir results/srm_loo_consistent \
    --output-dir ${SRM_OUT} \
    || { echo "ERROR: SRM projection failed"; exit 2; }

# -----------------------------------------------------------------------------
# Step 3: LORO + LOCO decoder comparison
# -----------------------------------------------------------------------------
echo ""
echo "--- Step 3: LORO + LOCO ---"
LOSO_OUT=analysis/phase3_decoder_comparing/results/filter_validation_${TIMESTAMP}
mkdir -p ${LOSO_OUT}

for ROI in "${ROIS[@]}"; do
    echo "[${ROI}] LOSO/LORO/LOCO"
    python analysis/phase3_decoder_comparing/phase1_cross_subject_loso.py \
        --roi ${ROI} \
        --timestamp ${TIMESTAMP} \
        --dataset ${DATASET} \
        --subjects "${SUBJECTS[@]}" \
        --session ${SESSION} \
        --output-dir ${LOSO_OUT} \
        || { echo "ERROR: LOSO failed for ${ROI}"; exit 3; }
done

# -----------------------------------------------------------------------------
# Step 4: Summary
# -----------------------------------------------------------------------------
echo ""
echo "--- Step 4: Comprehensive summary ---"
python analysis/comprehensive/generate_phase_summary.py \
    --dataset ${DATASET} \
    --timestamp ${TIMESTAMP} \
    --label filter_validation \
    || { echo "WARN: summary script failed (non-fatal)"; }

echo ""
echo "================================================================================"
echo "Filter-Validation Downstream COMPLETE"
echo "  SRM RDM:     ${SRM_OUT}/"
echo "  LORO/LOCO:   ${LOSO_OUT}/"
echo "  Summary:     analysis/comprehensive/results/COMPREHENSIVE_SUMMARY_${TIMESTAMP}.txt"
echo "End: $(date)"
echo "================================================================================"
exit 0
