#!/bin/bash
#SBATCH --job-name=bl_rdm
#SBATCH --output=logs/baseline_rdm_%j.out
#SBATCH --error=logs/baseline_rdm_%j.err
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=08:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization
# ---------------------------------------------------------------------------
# HC Validation with L_rdm Fix (Task B)
#
# Same as baseline_delta_rho_diagnostic.py but with hV4 Procrustes DRDM
# included in the loss (delta=0.2). Makes HC and CVD results comparable.
#
# 10 subjects x 4 models x 2 families
# fourier_warp adds ~2h via DE (2 restarts x 60 iter x 10 subjects)
# Estimated total: ~6h. Time limit 8h is safe margin.
# ---------------------------------------------------------------------------

set -eo pipefail

mkdir -p logs results/baseline_delta_rho_with_rdm

echo "=============================================================="
echo "  HC Validation with L_rdm -- $(date)"
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

mpirun -np 1 python scripts/baseline_delta_rho_with_rdm.py \
    --subjects 01 02 03 04 05 06 07 08 09 10 \
    --output_dir results/baseline_delta_rho_with_rdm

echo ""
echo "=============================================================="
echo "  HC Validation with L_rdm finished -- $(date)"
echo "  Results: results/baseline_delta_rho_with_rdm/"
echo "=============================================================="
