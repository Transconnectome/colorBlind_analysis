#!/bin/bash
#SBATCH --job-name=sep_search
#SBATCH --output=logs/sep_search_%j.out
#SBATCH --error=logs/sep_search_%j.err
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/cone_shift_pipeline
# ---------------------------------------------------------------------------
# Task-Oriented Separation Search for Sub-09
#
# Sub-09 Machado (Δλ=13.5nm) has many-to-one forward model:
#   c4(green), c5(cyan), c6(blue), c7(purple) merge in perceived space.
# This script optimizes CIELab inputs to maximize pairwise separation.
#
# Estimated: ~5 min (DE optimization + dense forward model map)
# ---------------------------------------------------------------------------

set -eo pipefail

mkdir -p logs results/loco_filter/preimage

echo "=============================================================="
echo "  Separation Search -- $(date)"
echo "  Host      : $(hostname)"
echo "  Job ID    : ${SLURM_JOB_ID}"
echo "  Workdir   : $(pwd)"
echo "=============================================================="

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}

python -c "import numpy, scipy; print('OK: numpy', numpy.__version__)" \
    || { echo "ERROR: missing packages"; exit 1; }

PREIMAGE_DIR=results/loco_filter/preimage

echo ""
echo "===== Sub-09 hV4 Machado separation optimization ====="

mpirun -np 1 python scripts/preimage_separation_search.py \
    --subject 09 --roi V4 --model machado_1way \
    --preimage_dir ${PREIMAGE_DIR} \
    --output_dir ${PREIMAGE_DIR}

echo ""
echo "=============================================================="
echo "  Separation search complete -- $(date)"
echo "  Results: ${PREIMAGE_DIR}/sub-09_V4_machado_1way_separation.json"
echo "=============================================================="
