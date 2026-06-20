#!/bin/bash
#SBATCH --job-name=exp2_2x2
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=0:20:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase3_behavioral_analysis/exp2_neural/scripts
#SBATCH --output=logs/exp2_2x2_%j.out
#SBATCH --error=logs/exp2_2x2_%j.err
VARIANT=${1:-native}
source ~/.bashrc
conda activate nilearn
python exp2_decoder_2x2.py --variant ${VARIANT}
