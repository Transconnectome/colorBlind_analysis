#!/bin/bash
#SBATCH --job-name=fir_preproc
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=3:00:00
#SBATCH --output=logs/fir_preproc_%A_%a.out
#SBATCH --error=logs/fir_preproc_%A_%a.err
#SBATCH --array=0-3

# FIR GLM with preprocessing parameter testing
# Literature-based configurations (6 configs)

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Create log directory
mkdir -p logs

# Define subjects and ROIs
SUBJECTS=("01" "02" "03" "04")
ROIS=("V1" "V2" "V3" "hV4")

# Get subject from array task ID
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}

# Timestamp for this batch
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "FIR GLM - Preprocessing Testing"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "Subject: $SUBJECT"
echo "Timestamp: $TIMESTAMP"
echo "Node: $(hostname)"
echo "Start time: $(date)"
echo ""

# Preprocessing configurations (literature-based)
CONFIGS=(1 2 3 4 5 6)
CONFIG_NAMES=(
    "baseline"
    "spm_default"
    "conservative_mvpa"
    "nosmooth_mvpa"
    "poly_drift"
    "minimal"
)

# Strategies to test
STRATEGIES=("flatten" "average" "delay4")

echo "Testing 6 preprocessing configs × 3 strategies × 2 PCA variants"
echo "  Configs: ${CONFIG_NAMES[@]}"
echo "  Strategies: ${STRATEGIES[@]}"
echo ""

# Run for each ROI
for ROI in "${ROIS[@]}"; do
    echo "======================================"
    echo "ROI: $ROI"
    echo "======================================"

    for CONFIG in "${CONFIGS[@]}"; do
        CONFIG_NAME=${CONFIG_NAMES[$((CONFIG-1))]}

        echo "--------------------------------------"
        echo "Config $CONFIG: $CONFIG_NAME"
        echo "--------------------------------------"

        for STRATEGY in "${STRATEGIES[@]}"; do
            echo ">>> Strategy: $STRATEGY"

            # Without PCA
            echo "  - Without PCA"
            python fir_per_run_preprocessing.py \
                --subject $SUBJECT \
                --roi $ROI \
                --strategy $STRATEGY \
                --config $CONFIG \
                --timestamp ${TIMESTAMP}

            # With PCA
            echo "  - With PCA (n=6)"
            python fir_per_run_preprocessing.py \
                --subject $SUBJECT \
                --roi $ROI \
                --strategy $STRATEGY \
                --config $CONFIG \
                --use-pca \
                --n-components 6 \
                --timestamp ${TIMESTAMP}

            echo ""
        done
    done
done

echo "=========================================="
echo "Completed: $SUBJECT"
echo "End time: $(date)"
echo "=========================================="
