#!/bin/bash
#SBATCH --job-name=exp2_C010
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=1:00:00
#SBATCH --no-requeue
#SBATCH --array=1
#SBATCH --output=logs/exp2_C010_%A_%a.out
#SBATCH --error=logs/exp2_C010_%A_%a.err

# exp2 per-condition C010 amplitude extraction, sub-08.
# array maps to ROI: 1=V1 2=V2 3=V3 4=V4 . Test with --array=1, then 1-4.
ROIS=(V1 V2 V3 V4)
ROI=${ROIS[$((SLURM_ARRAY_TASK_ID - 1))]}
SUBJECT=08
MV=${1:-native}   # native (masknone n coverage, 858) | matched (exp1 maskfunc, 560)

echo "========================================"
echo "Job $SLURM_JOB_ID  task $SLURM_ARRAY_TASK_ID  sub-${SUBJECT}  ROI ${ROI}  variant ${MV}"
echo "========================================"

source ~/.bashrc
conda activate nilearn

cd /scratch/connectome/haba6030/colorBlind/analysis/future_phase3_behavioral_analysis/exp2_neural/scripts

python exp2_C010_conditions.py --subject ${SUBJECT} --roi ${ROI} --mask-variant ${MV}
