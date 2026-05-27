#!/bin/bash
#SBATCH --job-name=srm_pre
#SBATCH --output=logs/srm_precompute_%j.out
#SBATCH --error=logs/srm_precompute_%j.err
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization
# ---------------------------------------------------------------------------
# Step 0: SRM Precompute for V1/V2 (Task A prerequisite)
#
# Trains HC-only SRM, computes W_combined = W_ridge @ W_srm,
# projects CVD into SRM space, computes SRM-space DRDM_obs.
#
# CRITICAL: Must use mpirun -np 1 for BrainIAK SRM.
#
# Estimated: ~2 min (SRM 10 iter x 2 ROIs + ridge W + projections)
# Time limit 30 min is very safe.
# ---------------------------------------------------------------------------

set -eo pipefail

mkdir -p logs results/srm_precompute

echo "=============================================================="
echo "  Step 0: SRM Precompute (V1/V2) -- $(date)"
echo "  Host      : $(hostname)"
echo "  Job ID    : ${SLURM_JOB_ID}"
echo "  Workdir   : $(pwd)"
echo "=============================================================="

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-2}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-2}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-2}

python -c "from brainiak.funcalign.srm import SRM; print('OK: brainiak SRM')" \
    || { echo "ERROR: brainiak not available"; exit 1; }

mpirun -np 1 python scripts/step0_srm_precompute.py \
    --rois V1 V2 \
    --output_dir results/srm_precompute

echo ""
echo "=============================================================="
echo "  Step 0 finished -- $(date)"
echo "  Results: results/srm_precompute/"
echo "=============================================================="
