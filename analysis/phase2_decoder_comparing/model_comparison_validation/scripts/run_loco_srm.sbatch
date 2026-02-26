#!/bin/bash
#SBATCH --job-name=loco_srm
#SBATCH --nodelist=node2
#SBATCH --array=1-10%5
#SBATCH --cpus-per-task=4
#SBATCH --mem=4G
#SBATCH --time=06:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation/logs/loco_srm_%a_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation/logs/loco_srm_%a_%j.err

# Environment
source ~/.bashrc
conda activate nilearn

# Paths
SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation/scripts
BASELINE_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010
OUTPUT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/results/loco_srm

# Subject mapping (array index 1-10 → subject ID)
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID-1]}

echo "=============================="
echo "Job: $SLURM_JOB_ID | Array: $SLURM_ARRAY_TASK_ID"
echo "Subject: sub-${SUBJECT}"
echo "Alignment: srm"
echo "Node: $(hostname)"
echo "Start: $(date)"
echo "=============================="

mkdir -p ${OUTPUT_DIR}

# Run LOCO on SRM amplitudes (6 standard models + 2 hybrid, 1000 permutations)
python ${SCRIPT_DIR}/loco_baseline.py \
    --baseline_dir ${BASELINE_DIR} \
    --output_dir ${OUTPUT_DIR} \
    --subject ${SUBJECT} \
    --rois V1 V2 V3 V4 \
    --models LDA Ridge KernelRidge SVM MLP ForwardEncoding HybridMLP HybridSVR \
    --alignment srm \
    --permutations 1000

echo "=============================="
echo "End: $(date)"
echo "=============================="
