#!/bin/bash
#SBATCH --job-name=srm_loco
#SBATCH --output=logs/srm_integrated_loco_%j.out
#SBATCH --error=logs/srm_integrated_loco_%j.err
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase5_filter_optimization
# ---------------------------------------------------------------------------
# SRM-Integrated LOCO: hV4 Procrustes LOCO + V1/V2 SRM DRDM (Task A main)
#
# Cross-ROI design: LOCO from hV4, L_rdm from V1/V2 SRM space.
# Requires step0_srm_precompute.py outputs in results/srm_precompute/
#
# 3 subjects x 4 models x 2 families
# w_fixed LOCO is fast; fourier DE ~30 min per subject
# Estimated total: ~3h. Time limit 4h is safe.
#
# NOTE: No mpirun needed (does NOT import BrainIAK directly).
# ---------------------------------------------------------------------------

set -eo pipefail

mkdir -p logs results/srm_integrated_loco

echo "=============================================================="
echo "  SRM-Integrated LOCO -- $(date)"
echo "  Host      : $(hostname)"
echo "  Job ID    : ${SLURM_JOB_ID}"
echo "  Workdir   : $(pwd)"
echo "=============================================================="

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export PYTHONUNBUFFERED=1

# Verify SRM precompute outputs exist
if [ ! -f results/srm_precompute/manifest.json ]; then
    echo "ERROR: results/srm_precompute/manifest.json not found."
    echo "Run run_srm_precompute.sbatch first."
    exit 1
fi

python -c "import numpy, scipy, sklearn; print('OK: numpy', numpy.__version__)" \
    || { echo "ERROR: missing packages"; exit 1; }

python scripts/srm_integrated_loco.py \
    --subjects 08 09 10 \
    --srm_dir results/srm_precompute \
    --output_dir results/srm_integrated_loco

echo ""
echo "=============================================================="
echo "  SRM-Integrated LOCO finished -- $(date)"
echo "  Results: results/srm_integrated_loco/"
echo "=============================================================="
