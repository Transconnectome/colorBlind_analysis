#!/bin/bash
#SBATCH --job-name=focused_nest
#SBATCH --nodelist=node2
#SBATCH --array=1-10%5
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation
#SBATCH --output=logs/focused_nest_%a_%j.out
#SBATCH --error=logs/focused_nest_%a_%j.err

# Environment
source ~/.bashrc
conda activate nilearn

# Paths
SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation/scripts
BASELINE_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010
OUTPUT_BASE=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation/results/focused_nested

# Subject mapping
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID-1]}
MODELS="ForwardEncoding SVM MLP"

echo "=============================="
echo "Job: $SLURM_JOB_ID | Array: $SLURM_ARRAY_TASK_ID"
echo "Subject: sub-${SUBJECT} | Models: ${MODELS}"
echo "Node: $(hostname) | Start: $(date)"
echo "=============================="

# Condition 1: Nested Procrustes (full voxels)
echo ""
echo "=== Cond 1: Nested Procrustes ==="
python ${SCRIPT_DIR}/run_model_comparison.py \
    --baseline_dir ${BASELINE_DIR} \
    --output_dir ${OUTPUT_BASE}/nested_only \
    --subject ${SUBJECT} \
    --alignment nested_procrustes \
    --models ${MODELS}

# Condition 2: Nested Procrustes + PCA k=20
echo ""
echo "=== Cond 2: Nested Procrustes + PCA 20 ==="
python ${SCRIPT_DIR}/run_model_comparison.py \
    --baseline_dir ${BASELINE_DIR} \
    --output_dir ${OUTPUT_BASE}/nested_pca20 \
    --subject ${SUBJECT} \
    --alignment nested_procrustes \
    --dim_reduction pca --dim_k 20 \
    --models ${MODELS}

# Condition 3: Preloaded Procrustes (original — control)
echo ""
echo "=== Cond 3: Preloaded Procrustes (control) ==="
python ${SCRIPT_DIR}/run_model_comparison.py \
    --baseline_dir ${BASELINE_DIR} \
    --output_dir ${OUTPUT_BASE}/procrustes_ctrl \
    --subject ${SUBJECT} \
    --alignment procrustes \
    --models ${MODELS}

echo ""
echo "=============================="
echo "All 3 conditions complete for sub-${SUBJECT}"
echo "End: $(date)"
echo "=============================="
