#!/bin/bash
#SBATCH --job-name=loco_phaseB_v2
#SBATCH --output=logs/loco_phaseB_v2_%j.out
#SBATCH --error=logs/loco_phaseB_v2_%j.err
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/cone_shift_pipeline
# ---------------------------------------------------------------------------
# LOCO Filter Phase B v2: Filter Derivation
# v2 changes: sign-based preserved (vuln > 0 only) + max_shift 5 deg
# ---------------------------------------------------------------------------

set -eo pipefail

mkdir -p logs results/loco_filter/phase_b_v2

echo "=============================================================="
echo "  LOCO Filter Phase B v2 (sign-based + 5deg) -- $(date)"
echo "  Host      : $(hostname)"
echo "  Job ID    : ${SLURM_JOB_ID}"
echo "=============================================================="

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}

DATA_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010
A_DIR=results/loco_filter/phase_a
B_DIR=results/loco_filter/phase_b_v2

# --- Sub-08: R+C (primary) ---
echo ""
echo "[$(date +%H:%M:%S)]  Sub-08 hV4 R+C filter derivation (sign-based)"
mpirun -np 1 python scripts/loco_filter_derive.py \
    --subject 08 --roi V4 --model rc_opponent \
    --method shift_at_both \
    --phase_a_dir ${A_DIR} --data_dir ${DATA_DIR} --output_dir ${B_DIR}

# --- Sub-09: Machado (primary) ---
echo ""
echo "[$(date +%H:%M:%S)]  Sub-09 hV4 Machado filter derivation (sign-based)"
mpirun -np 1 python scripts/loco_filter_derive.py \
    --subject 09 --roi V4 --model machado_1way \
    --method shift_at_both \
    --phase_a_dir ${A_DIR} --data_dir ${DATA_DIR} --output_dir ${B_DIR}

# --- Sub-10: Machado (specificity check -- expect NO_FILTER) ---
echo ""
echo "[$(date +%H:%M:%S)]  Sub-10 hV4 Machado specificity check"
mpirun -np 1 python scripts/loco_filter_derive.py \
    --subject 10 --roi V4 --model machado_1way \
    --method shift_at_both \
    --phase_a_dir ${A_DIR} --data_dir ${DATA_DIR} --output_dir ${B_DIR}

echo ""
echo "=============================================================="
echo "  Phase B v2 finished -- $(date)"
echo "  Results: ${B_DIR}/"
echo "=============================================================="
