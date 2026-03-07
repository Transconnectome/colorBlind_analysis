#!/bin/bash
#SBATCH --job-name=gp_cvd_srm
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=06:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase3_decoder_comparing/model_comparison_validation
#SBATCH --output=logs/gp_cvd_srm_%j.out
#SBATCH --error=logs/gp_cvd_srm_%j.err

source ~/.bashrc
conda activate nilearn

# HC-mean group prior on CVD subjects' SRM data
# - W_group = mean of 7 HC subjects' pooled W (all 48 samples each)
# - W_individual = CVD target's training data
# - Nested CV selects optimal lambda per fold
mpirun -np 1 python scripts/group_prior.py \
    --cv loco \
    --mode nested \
    --subjects 08 09 10 \
    --rois V1 V2 V3 V4 \
    --lambda_values "0.0 1.0" \
