#!/bin/bash
#SBATCH --job-name=axis4d
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization
#SBATCH --output=logs/axis4d_%A_%a.out
#SBATCH --error=logs/axis4d_%A_%a.err
#SBATCH --array=0-1

source ~/.bashrc
conda activate nilearn

# Limit BLAS threads to avoid oversubscription when using multiprocessing
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

mkdir -p logs results/axis_free_4d

SUBJECTS=(08 09)
FAMILIES=(deutan protan)
SID=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}
FAM=${FAMILIES[$SLURM_ARRAY_TASK_ID]}

echo "=== Job ${SLURM_JOB_ID} array=${SLURM_ARRAY_TASK_ID}  sub-${SID} ${FAM} ==="
echo "Host: $(hostname)  CPUs: ${SLURM_CPUS_PER_TASK}  Start: $(date)"

python scripts/axis_free_4d_refit.py \
    --subject ${SID} \
    --family ${FAM} \
    --bs_min 0 --bs_max 50 --bs_step 5 \
    --bc_min -50 --bc_max 50 --bc_step 5 \
    --phi_s_min 0 --phi_s_max 359 \
    --phi_c_min 0 --phi_c_max 359 \
    --phi_step 45 \
    --tag emery_coarse45

echo "=== End: $(date) ==="
