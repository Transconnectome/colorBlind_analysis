#!/bin/bash
#SBATCH --job-name=nested_proc
#SBATCH --nodelist=node2
#SBATCH --array=1-10%5
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation
#SBATCH --output=logs/nested_proc_%a_%j.out
#SBATCH --error=logs/nested_proc_%a_%j.err

# Environment
source ~/.bashrc
conda activate nilearn

# Paths
SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation/scripts
BASELINE_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010
OUTPUT_BASE=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation/results/nested_procrustes

# Subject mapping (array index 1-10 -> subject ID)
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID-1]}

echo "=============================="
echo "Job: $SLURM_JOB_ID | Array: $SLURM_ARRAY_TASK_ID"
echo "Subject: sub-${SUBJECT}"
echo "Node: $(hostname)"
echo "Start: $(date)"
echo "=============================="

# Condition 1: Raw control (must match original raw results)
echo ""
echo "=== Condition 1: Raw control ==="
python ${SCRIPT_DIR}/run_model_comparison.py \
    --baseline_dir ${BASELINE_DIR} \
    --output_dir ${OUTPUT_BASE}/raw_ctrl \
    --subject ${SUBJECT} \
    --alignment raw \
    --models LDA Ridge KernelRidge SVM MLP ForwardEncoding

# Condition 2: Nested Procrustes only (RT-2)
echo ""
echo "=== Condition 2: Nested Procrustes only ==="
python ${SCRIPT_DIR}/run_model_comparison.py \
    --baseline_dir ${BASELINE_DIR} \
    --output_dir ${OUTPUT_BASE}/nested_only \
    --subject ${SUBJECT} \
    --alignment nested_procrustes \
    --models LDA Ridge KernelRidge SVM MLP ForwardEncoding

# Condition 3: Nested Procrustes + ANOVA k=100 (RT-2 + RT-3)
echo ""
echo "=== Condition 3: Nested Procrustes + ANOVA 100 ==="
python ${SCRIPT_DIR}/run_model_comparison.py \
    --baseline_dir ${BASELINE_DIR} \
    --output_dir ${OUTPUT_BASE}/nested_anova100 \
    --subject ${SUBJECT} \
    --alignment nested_procrustes \
    --dim_reduction anova --dim_k 100 \
    --models LDA Ridge KernelRidge SVM MLP ForwardEncoding

# Condition 4: Nested Procrustes + PCA k=20 (RT-2 + RT-3)
echo ""
echo "=== Condition 4: Nested Procrustes + PCA 20 ==="
python ${SCRIPT_DIR}/run_model_comparison.py \
    --baseline_dir ${BASELINE_DIR} \
    --output_dir ${OUTPUT_BASE}/nested_pca20 \
    --subject ${SUBJECT} \
    --alignment nested_procrustes \
    --dim_reduction pca --dim_k 20 \
    --models LDA Ridge KernelRidge SVM MLP ForwardEncoding

# Condition 5: Raw + ANOVA k=100 (isolates dim reduction effect)
echo ""
echo "=== Condition 5: Raw + ANOVA 100 ==="
python ${SCRIPT_DIR}/run_model_comparison.py \
    --baseline_dir ${BASELINE_DIR} \
    --output_dir ${OUTPUT_BASE}/raw_anova100 \
    --subject ${SUBJECT} \
    --alignment raw \
    --dim_reduction anova --dim_k 100 \
    --models LDA Ridge KernelRidge SVM MLP ForwardEncoding

echo ""
echo "=============================="
echo "All 5 conditions complete for sub-${SUBJECT}"
echo "End: $(date)"
echo "=============================="
