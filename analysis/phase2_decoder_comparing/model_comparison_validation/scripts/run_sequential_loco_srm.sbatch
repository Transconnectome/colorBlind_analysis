#!/bin/bash
#SBATCH --job-name=seq_loco_srm
#SBATCH --nodelist=node2
#SBATCH --array=1-10
#SBATCH --cpus-per-task=4
#SBATCH --mem=4G
#SBATCH --time=04:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation
#SBATCH --output=logs/seq_loco_srm_%a_%j.out
#SBATCH --error=logs/seq_loco_srm_%a_%j.err

source ~/.bashrc
conda activate nilearn

SCRIPT_DIR=scripts
BASELINE_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010
OUTPUT_DIR=results/loco_sequential/srm

SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID-1]}

mpirun -np 1 python ${SCRIPT_DIR}/run_loco_comparison.py \
    --baseline_dir ${BASELINE_DIR} \
    --output_dir ${OUTPUT_DIR} \
    --subject ${SUBJECT} \
    --rois V1 V2 V3 V4 \
    --models FE_Sequential HybridMLP_Sequential HybridSVR_Sequential \
    --alignment srm \
    --permutations 0
