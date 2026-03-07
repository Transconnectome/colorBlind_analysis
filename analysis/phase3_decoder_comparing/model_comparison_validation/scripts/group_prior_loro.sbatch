#!/bin/bash
#SBATCH --job-name=gp_loro
#SBATCH --nodelist=node2
#SBATCH --array=1-10%5
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=06:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase3_decoder_comparing/model_comparison_validation
#SBATCH --output=logs/gp_loro_%a_%j.out
#SBATCH --error=logs/gp_loro_%a_%j.err

source ~/.bashrc
conda activate nilearn

SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID-1]}

# Group prior with nested LORO lambda selection
mpirun -np 1 python scripts/group_prior.py \
    --cv loro \
    --mode nested \
    --subjects ${SUBJECT} \
    --rois V1 V2 V3 V4 \
    --lambda_values "0.0,0.05,0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5,0.6,0.7,0.8,0.9,1.0"
