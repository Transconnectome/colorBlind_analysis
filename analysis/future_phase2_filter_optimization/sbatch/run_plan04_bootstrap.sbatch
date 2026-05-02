#!/bin/bash
#SBATCH --job-name=plan04_boot
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/derivatives/logs/plan04_boot_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/derivatives/logs/plan04_boot_%A_%a.err
#SBATCH --array=0-5%6
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=2:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization

# Plan 04 Cycle 4 deferred: HC bootstrap variance for primary cells.
# Cells: V1+V4 + sub-{08, 09} (sub-10 sanity excluded).

source /usr/anaconda3/etc/profile.d/conda.sh
conda activate nilearn

# 6 cells: (V1|V2|V4) x (08|09)
CASES=("V1_08" "V1_09" "V2_08" "V2_09" "V4_08" "V4_09")
CASE=${CASES[$SLURM_ARRAY_TASK_ID]}
ROI=${CASE%_*}
SUBJ=${CASE#*_}

echo "[$(date)] Bootstrap subj=$SUBJ roi=$ROI"

python scripts/cycle_filter_refinement/run_bootstrap.py \
    --subject "$SUBJ" --roi "$ROI" \
    --n_boot 200 \
    --bs_step 2 --bc_step 2 \
    --lam_tikh 0.1 \
    --data_dir /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010 \
    --output_dir results/cycle_filter_refinement/bootstrap

echo "[$(date)] done"
