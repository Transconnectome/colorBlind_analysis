#!/bin/bash
#SBATCH --job-name=preimage_filter
#SBATCH --output=logs/preimage_%j.out
#SBATCH --error=logs/preimage_%j.err
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/cone_shift_pipeline
# ---------------------------------------------------------------------------
# Pre-Image Filter Search + Evaluation
#
# Stage 1: preimage_filter_search.py
#   - Sub-08: R+C model (subject-specific forward model)
#   - Sub-09: Machado (subject-specific forward model)
#   - Sub-10: Both models (specificity control — expect identity)
#
# Stage 2: evaluate_preimage_filter.py
#   - Cross-sim sanity (Machado severity sweep)
#   - L_improve diagnostic (perceived-angle chain)
#   - Comparison table (no-filter / inverse / preimage)
#
# Estimated: ~10 min total (grid search + Brent per subject)
# ---------------------------------------------------------------------------

set -eo pipefail

mkdir -p logs results/loco_filter/preimage results/loco_filter/preimage/evaluation

echo "=============================================================="
echo "  Pre-Image Filter Search + Evaluation -- $(date)"
echo "  Host      : $(hostname)"
echo "  Job ID    : ${SLURM_JOB_ID}"
echo "  Workdir   : $(pwd)"
echo "=============================================================="

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}

python -c "import numpy, scipy, sklearn; print('OK: numpy', numpy.__version__)" \
    || { echo "ERROR: missing packages"; exit 1; }

DATA_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010
PHASE_A_DIR=results/loco_filter/phase_a
PREIMAGE_DIR=results/loco_filter/preimage

# ===== Stage 1: Pre-image search (subject-specific models) =====

echo ""
echo "===== STAGE 1: Pre-image search ====="

# --- Sub-08 hV4: R+C model (deutan) ---
echo ""
echo "[$(date +%H:%M:%S)]  Sub-08 hV4 rc_opponent pre-image search"
mpirun -np 1 python scripts/preimage_filter_search.py \
    --subject 08 --roi V4 --model rc_opponent \
    --phase_a_dir ${PHASE_A_DIR} \
    --output_dir ${PREIMAGE_DIR}

# --- Sub-09 hV4: Machado (protan) ---
echo ""
echo "[$(date +%H:%M:%S)]  Sub-09 hV4 machado_1way pre-image search"
mpirun -np 1 python scripts/preimage_filter_search.py \
    --subject 09 --roi V4 --model machado_1way \
    --phase_a_dir ${PHASE_A_DIR} \
    --output_dir ${PREIMAGE_DIR}

# --- Sub-10 hV4: Both models (specificity — expect identity) ---
echo ""
echo "[$(date +%H:%M:%S)]  Sub-10 hV4 machado_1way pre-image search (specificity)"
mpirun -np 1 python scripts/preimage_filter_search.py \
    --subject 10 --roi V4 --model machado_1way \
    --phase_a_dir ${PHASE_A_DIR} \
    --output_dir ${PREIMAGE_DIR}

# Sub-10 rc_opponent skipped: no Phase A JSON available

# ===== Stage 2: Evaluation =====

echo ""
echo "===== STAGE 2: Evaluation (cross-sim sanity + L_improve diagnostic) ====="

echo ""
echo "[$(date +%H:%M:%S)]  Running evaluation"
mpirun -np 1 python scripts/evaluate_preimage_filter.py \
    --preimage_dir ${PREIMAGE_DIR} \
    --data_dir ${DATA_DIR} \
    --output_dir ${PREIMAGE_DIR}/evaluation

echo ""
echo "=============================================================="
echo "  Pre-Image Filter complete -- $(date)"
echo "  Pre-image results : ${PREIMAGE_DIR}/"
echo "  Evaluation results: ${PREIMAGE_DIR}/evaluation/"
echo "=============================================================="
