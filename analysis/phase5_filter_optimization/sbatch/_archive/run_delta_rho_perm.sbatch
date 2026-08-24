#!/bin/bash
#SBATCH --job-name=drho_perm
#SBATCH --output=logs/drho_perm_%A_%a.out
#SBATCH --error=logs/drho_perm_%A_%a.err
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=06:00:00
#SBATCH --no-requeue
#SBATCH --array=0-9
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase5_filter_optimization/cone_shift_pipeline
# ---------------------------------------------------------------------------
# B. Δρ permutation re-definition (peer_review/problematic_params_and_loss.md §4.3 #5)
#
# Re-tests the "fit-vs-baseline Δρ" null hypothesis to address the
# baseline-ρ ↔ Δρ correlation r=−0.894 (Job 96664) that compromised
# CVD-vs-HC specificity claims.
#
# Scope per subject task:
#   V4: machado_1way, rc_opponent, 2component (× protan/deutan for HC)
#   V1: 2component       (× protan/deutan for HC)
#   V2: 2component       (× protan/deutan for HC)
#
# Array task: 0-6 = HC 01-07 (LOO pseudo-CVD, 2 families)
#             7-9 = CVD 08-10 (auto family)
# ---------------------------------------------------------------------------

set -eo pipefail

mkdir -p logs results/delta_rho_perm

ALL_SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
SUBJ=${ALL_SUBJECTS[$SLURM_ARRAY_TASK_ID]}

echo "=============================================================="
echo "  Δρ perm — sub-${SUBJ} — $(date)"
echo "  Host    : $(hostname)"
echo "  Job ID  : ${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
echo "  Workdir : $(pwd)"
echo "=============================================================="

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}

DATA_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010
OUT_DIR=results/delta_rho_perm

# CVD subjects: auto-detect family
if [[ "$SUBJ" == "08" || "$SUBJ" == "09" || "$SUBJ" == "10" ]]; then
    FAMILIES=("auto")
else
    FAMILIES=("protan" "deutan")
fi

run_cell() {
    local roi=$1
    local model=$2
    local fam=$3
    local method=$4

    local extra_arg=""
    if [[ "$fam" != "auto" ]]; then
        extra_arg="--cvd_type ${fam}"
    fi

    echo ""
    echo "[$(date +%H:%M:%S)] sub-${SUBJ} ${roi} ${model} ${fam} (${method})"
    mpirun -np 1 python scripts/delta_rho_perm_test.py \
        --subject ${SUBJ} --roi ${roi} --model ${model} \
        --method ${method} ${extra_arg} \
        --data_dir ${DATA_DIR} \
        --output_dir ${OUT_DIR}
}

# === V4 (hV4) — 3 models, shift_at_both ===
for FAM in "${FAMILIES[@]}"; do
    run_cell V4 machado_1way ${FAM} shift_at_both
    run_cell V4 rc_opponent  ${FAM} shift_at_both
    run_cell V4 2component   ${FAM} shift_at_both
done

# === V1, V2 — 2component only, w_fixed ===
for ROI in V1 V2; do
    for FAM in "${FAMILIES[@]}"; do
        run_cell ${ROI} 2component ${FAM} w_fixed
    done
done

echo ""
echo "=============================================================="
echo "  Δρ perm sub-${SUBJ} finished — $(date)"
echo "  Results: ${OUT_DIR}/sub-${SUBJ}_*.json"
echo "=============================================================="
