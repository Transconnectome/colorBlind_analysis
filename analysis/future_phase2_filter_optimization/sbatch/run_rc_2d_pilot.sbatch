#!/bin/bash
#SBATCH --job-name=rc_2d_pilot
#SBATCH --output=logs/rc_2d_pilot_%A_%a.out
#SBATCH --error=logs/rc_2d_pilot_%A_%a.err
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=04:00:00
#SBATCH --no-requeue
#SBATCH --array=0-2
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/cone_shift_pipeline
# ---------------------------------------------------------------------------
# A. R+C-2D rotation pilot (3-DOF: Δλ, g_RG, g_YB)
#
# Hypothesis (from peer_review/problematic_params_and_loss.md §2.1):
#   sub-08 R+C single-axis g=±2.25 absorbs B-Y axis distortion.
#   Adding g_YB may normalize g_RG into Tregillus 20-40% range.
#
# Grid: 21 × 13 × 13 = 3,549 points × shift_at_both ≈ ~60min/sub
# Array task: 0=sub-08, 1=sub-09, 2=sub-10
# ---------------------------------------------------------------------------

set -eo pipefail

mkdir -p logs results/loco_filter/rc_2d_pilot

SUBJECTS=(08 09 10)
SUBJ=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}

echo "=============================================================="
echo "  R+C-2D pilot — sub-${SUBJ} hV4 — $(date)"
echo "  Host      : $(hostname)"
echo "  Job ID    : ${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
echo "  Workdir   : $(pwd)"
echo "=============================================================="

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}

DATA_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010
OUT_DIR=results/loco_filter/rc_2d_pilot

echo ""
echo "[$(date +%H:%M:%S)] sub-${SUBJ} hV4 shift_at_both — rc_opponent_2d + rc_opponent (baseline)"
mpirun -np 1 python scripts/loco_distortion_fit.py \
    --subject ${SUBJ} --roi V4 --method shift_at_both \
    --models rc_opponent_2d rc_opponent \
    --data_dir ${DATA_DIR} \
    --output_dir ${OUT_DIR}

echo ""
echo "=============================================================="
echo "  R+C-2D pilot sub-${SUBJ} finished — $(date)"
echo "  Results: ${OUT_DIR}/sub-${SUBJ}_V4_rc_opponent_2d.json"
echo "=============================================================="
