#!/bin/bash
#SBATCH --job-name=loco_phaseA
#SBATCH --output=logs/loco_phaseA_%j.out
#SBATCH --error=logs/loco_phaseA_%j.err
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/cone_shift_pipeline
# ---------------------------------------------------------------------------
# LOCO Filter Phase A v2: R+C g extended [-3,3] + Fourier DE (3 restarts)
#
# Changes from v1:
#   - rc_opponent g: [-3, 1] -> [-3, 3] (1067 grid points vs 697)
#   - fourier_warp: L-BFGS-B -> DE with 3 restarts (~5 min/subj)
#   - machado_1way: unchanged (41 grid points)
# Estimated: sub-08 ~8 min, sub-09 ~8 min, sub-10 ~0.1 min = ~17 min
# Time limit 1h is safe margin.
# ---------------------------------------------------------------------------

set -eo pipefail

mkdir -p logs results/loco_filter/phase_a

echo "=============================================================="
echo "  LOCO Filter Phase A v2 -- $(date)"
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
OUT_DIR=results/loco_filter/phase_a

# --- Sub-08 hV4 (primary: deutan) ---
echo ""
echo "[$(date +%H:%M:%S)]  Sub-08 hV4 shift_at_both -- ALL models"
mpirun -np 1 python scripts/loco_distortion_fit.py \
    --subject 08 --roi V4 --method shift_at_both \
    --models machado_1way rc_opponent fourier_warp \
    --data_dir ${DATA_DIR} \
    --output_dir ${OUT_DIR}

# --- Sub-09 hV4 (secondary: protan) ---
echo ""
echo "[$(date +%H:%M:%S)]  Sub-09 hV4 shift_at_both -- ALL models"
mpirun -np 1 python scripts/loco_distortion_fit.py \
    --subject 09 --roi V4 --method shift_at_both \
    --models machado_1way rc_opponent fourier_warp \
    --data_dir ${DATA_DIR} \
    --output_dir ${OUT_DIR}

# --- Sub-10 hV4 (specificity control: normal) ---
echo ""
echo "[$(date +%H:%M:%S)]  Sub-10 hV4 shift_at_both -- machado_1way only"
mpirun -np 1 python scripts/loco_distortion_fit.py \
    --subject 10 --roi V4 --method shift_at_both \
    --models machado_1way \
    --data_dir ${DATA_DIR} \
    --output_dir ${OUT_DIR}

echo ""
echo "=============================================================="
echo "  Phase A v2 finished -- $(date)"
echo "  Results: ${OUT_DIR}/"
echo "=============================================================="
