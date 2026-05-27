#!/bin/bash
#SBATCH --job-name=cyc8_fp
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/derivatives/logs/cyc8_fp_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/derivatives/logs/cyc8_fp_%A_%a.err
#SBATCH --array=0-5%6
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=1:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization

# Plan 04 Cycle 8 #1-alt: HC LOO bootstrap on FP candidates (sub-04, sub-02).
# 6 cells: V1/V2/V4 x sub-{04, 02}.

source /usr/anaconda3/etc/profile.d/conda.sh
conda activate nilearn

CASES=("V1_04" "V2_04" "V4_04" "V1_02" "V2_02" "V4_02")
CASE=${CASES[$SLURM_ARRAY_TASK_ID]}
ROI=${CASE%_*}
SUBJ=${CASE#*_}

echo "[$(date)] cycle8 HC LOO bootstrap subj=$SUBJ roi=$ROI"

python scripts/cycle_filter_refinement/cycle8_voxel_bootstrap.py \
    --subject "$SUBJ" --roi "$ROI" \
    --n_boot 200 \
    --data_dir /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010 \
    --output_dir results/cycle_filter_refinement/cycle8_voxel_bootstrap

echo "[$(date)] done"
