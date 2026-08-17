#!/bin/bash
#SBATCH --job-name=loss_improve
#SBATCH --output=logs/loss_improve_%A_%a.out
#SBATCH --error=logs/loss_improve_%A_%a.err
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --no-requeue
#SBATCH --array=0-8
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization
# ---------------------------------------------------------------------------
# Loss improvement diagnostic landscapes
#
# 9 tasks = 3 modes (per_run, baseline_cv, voxel_gate) × 3 subjects (08, 09, 10)
#
#   per_run     : df 8 -> 48 via per-(HC,run,color) vuln + bootstrap CI (n=200)
#   baseline_cv : control-variate L_vuln = MSE(ρ_sim - ρ(0,0), ρ_cvd - ρ(0,0))
#   voxel_gate  : keep HC voxels with split-half reliability >= 0.1
#
# Expected per task:
#   - 41 × 81 = 3321 grid points
#   - per_run: ~2-3× slower (n_boot=200) -> est ~30-60 min
#   - baseline_cv: similar to canonical -> est ~10-20 min
#   - voxel_gate: faster (fewer voxels) -> est ~5-15 min
#
# Output: results/loss_improvement/sub-{ID}_{ROI}_{MODE}_landscape.json
# ---------------------------------------------------------------------------

set -eo pipefail
mkdir -p logs results/loss_improvement

# Array task -> (mode, subject)
MODES=(per_run per_run per_run baseline_cv baseline_cv baseline_cv voxel_gate voxel_gate voxel_gate)
SUBJECTS=(08 09 10 08 09 10 08 09 10)

MODE=${MODES[$SLURM_ARRAY_TASK_ID]}
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}

echo "=============================================================="
echo "  Loss improvement diagnostic  --  $(date)"
echo "  Host        : $(hostname)"
echo "  Job ID      : ${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
echo "  Workdir     : $(pwd)"
echo "  Mode        : ${MODE}"
echo "  Subject     : sub-${SUBJECT}"
echo "=============================================================="

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}

DATA_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010

mpirun -np 1 python scripts/loss_improvement_landscapes.py \
    --mode "${MODE}" \
    --subject "${SUBJECT}" \
    --roi V4 \
    --data_dir "${DATA_DIR}" \
    --output_dir results/loss_improvement \
    --gate_thr 0.1 \
    --n_boot 200 \
    --seed 42

echo "Done at $(date)"
