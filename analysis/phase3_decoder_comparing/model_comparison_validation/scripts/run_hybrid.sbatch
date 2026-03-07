#!/bin/bash
#SBATCH --job-name=hybrid_dec
#SBATCH --nodelist=node2
#SBATCH --array=1-10%5
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase3_decoder_comparing/model_comparison_validation
#SBATCH --output=logs/hybrid_%a_%j.out
#SBATCH --error=logs/hybrid_%a_%j.err

# Environment
source ~/.bashrc
conda activate nilearn

# Paths
SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/phase3_decoder_comparing/model_comparison_validation/scripts
BASELINE_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010
OUTPUT_BASE=/scratch/connectome/haba6030/colorBlind/analysis/phase3_decoder_comparing/model_comparison_validation/results/hybrid

# Subject mapping
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID-1]}

# Models: FE (baseline) + two hybrids
MODELS="ForwardEncoding FE_MLP FE_SVM"

echo "=============================="
echo "Job: $SLURM_JOB_ID | Array: $SLURM_ARRAY_TASK_ID"
echo "Subject: sub-${SUBJECT} | Models: ${MODELS}"
echo "Node: $(hostname) | Start: $(date)"
echo "=============================="

# Condition 1: Nested Procrustes (our best alignment)
echo ""
echo "=== Cond 1: Nested Procrustes ==="
python ${SCRIPT_DIR}/loro_baseline.py \
    --baseline_dir ${BASELINE_DIR} \
    --output_dir ${OUTPUT_BASE}/nested \
    --subject ${SUBJECT} \
    --alignment nested_procrustes \
    --models ${MODELS}

# Condition 2: Preloaded Procrustes (control)
echo ""
echo "=== Cond 2: Preloaded Procrustes (control) ==="
python ${SCRIPT_DIR}/loro_baseline.py \
    --baseline_dir ${BASELINE_DIR} \
    --output_dir ${OUTPUT_BASE}/procrustes_ctrl \
    --subject ${SUBJECT} \
    --alignment procrustes \
    --models ${MODELS}

echo ""
echo "=============================="
echo "All conditions complete for sub-${SUBJECT}"
echo "End: $(date)"
echo "=============================="
