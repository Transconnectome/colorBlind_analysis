#!/bin/bash
#SBATCH --job-name=boot_main
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=12:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/sbatch/cycle_bootstrap/logs/boot_main_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/sbatch/cycle_bootstrap/logs/boot_main_%A_%a.err
#SBATCH --array=0-8

# Array index → (subject, roi, model)
# 0-2: sub-08 × {V1, V2, V4} × 2component
# 3-5: sub-09 × {V1, V2, V4} × 2component
# 6-8: sub-10 × {V1, V2, V4} × 2component
SUBJECTS=(08 08 08 09 09 09 10 10 10)
ROIS=(V1 V2 V4 V1 V2 V4 V1 V2 V4)
MODELS=(2component 2component 2component 2component 2component 2component 2component 2component 2component)

SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}
ROI=${ROIS[$SLURM_ARRAY_TASK_ID]}
MODEL=${MODELS[$SLURM_ARRAY_TASK_ID]}

DATA_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010
OUT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/results/cycle_bootstrap/main

mkdir -p "$OUT_DIR" "$(dirname "$0")/logs"

source /home/haba6030/.bashrc
conda activate nilearn

mpirun -np 1 python scripts/cycle_bootstrap/bootstrap_main.py \
    --subject $SUBJECT \
    --roi $ROI \
    --model $MODEL \
    --data_dir "$DATA_DIR" \
    --output_dir "$OUT_DIR" \
    --n_boot 200 \
    --seed 42

# Notes:
# - 1326 grid pts × ~24s each in W-fixed = ~530min for n_boot=200 + LOHO + HC null on a single CPU.
# - On node2 with 4 CPUs, numpy linalg should already use BLAS multithreading.
# - For 3 CVD × 3 ROI × 1 model, total wall time ~12h (parallelized via array).
# - Add machado_1way / rc_opponent in additional array indices if needed.
