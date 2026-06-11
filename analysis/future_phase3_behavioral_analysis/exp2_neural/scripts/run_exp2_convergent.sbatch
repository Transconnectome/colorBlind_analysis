#!/bin/bash
#SBATCH --job-name=exp2_conv
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=0:30:00
#SBATCH --no-requeue
#SBATCH --output=logs/exp2_conv_%j.out
#SBATCH --error=logs/exp2_conv_%j.err

VARIANT=${1:-native}
source ~/.bashrc
conda activate nilearn
cd /scratch/connectome/haba6030/colorBlind/analysis/future_phase3_behavioral_analysis/exp2_neural/scripts
# brainiak SRM needs MPI init -> mpirun -np 1 (bare python forbidden, project CLAUDE.md §9)
mpirun -np 1 python exp2_convergent.py --variant ${VARIANT}
