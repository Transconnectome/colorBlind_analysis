#!/bin/bash
#SBATCH --job-name=drdm_both
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=8:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind
#SBATCH --output=logs/drdm_both_%j.log
#SBATCH --error=logs/drdm_both_%j.err

source ~/.bashrc
conda activate nilearn

SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/cone_shift_pipeline/scripts
BASE_RESULTS=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/cone_shift_pipeline/results
BASELINE_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010

mkdir -p ${BASE_RESULTS}
mkdir -p /scratch/connectome/haba6030/colorBlind/logs

MODELS="cone_1way cone_3way fourier"
SUBJECTS="08 09 10"

echo "========================================================"
echo "ΔRDM Loss Pipeline: Cosine vs Spearman Comparison"
echo "Models: ${MODELS}"
echo "Subjects: ${SUBJECTS}"
echo "Start: $(date)"
echo "========================================================"

# ============================================================================
# COSINE METRIC
# ============================================================================

OUTPUT_DIR=${BASE_RESULTS}/sim_cosine
mkdir -p ${OUTPUT_DIR}

echo ""
echo "######## COSINE METRIC ########"
echo "=== Step 1: DRDM Fitting (cosine) ==="
echo "Start: $(date)"
free -h | head -2

mpirun -np 1 python ${SCRIPT_DIR}/fit_cone_shift_delta_rdm.py \
    --output_dir ${OUTPUT_DIR} \
    --baseline_dir ${BASELINE_DIR} \
    --metric cosine \
    --models ${MODELS} \
    --cvd_subjects ${SUBJECTS}

echo ""
echo "Memory after cosine fitting:"
free -h | head -2

echo ""
echo "=== Step 2: V4 LOCO Validation (cosine) ==="
echo "Start: $(date)"

mpirun -np 1 python ${SCRIPT_DIR}/validate_cone_shift_v4_loco.py \
    --sim_dir ${OUTPUT_DIR} \
    --output_dir ${OUTPUT_DIR} \
    --baseline_dir ${BASELINE_DIR} \
    --models ${MODELS} \
    --cvd_subjects ${SUBJECTS}

echo ""
echo "Cosine metric complete: $(date)"
free -h | head -2

# ============================================================================
# SPEARMAN METRIC
# ============================================================================

OUTPUT_DIR=${BASE_RESULTS}/sim_spearman
mkdir -p ${OUTPUT_DIR}

echo ""
echo ""
echo "######## SPEARMAN METRIC ########"
echo "=== Step 1: DRDM Fitting (spearman) ==="
echo "Start: $(date)"
free -h | head -2

mpirun -np 1 python ${SCRIPT_DIR}/fit_cone_shift_delta_rdm.py \
    --output_dir ${OUTPUT_DIR} \
    --baseline_dir ${BASELINE_DIR} \
    --metric spearman \
    --models ${MODELS} \
    --cvd_subjects ${SUBJECTS}

echo ""
echo "Memory after spearman fitting:"
free -h | head -2

echo ""
echo "=== Step 2: V4 LOCO Validation (spearman) ==="
echo "Start: $(date)"

mpirun -np 1 python ${SCRIPT_DIR}/validate_cone_shift_v4_loco.py \
    --sim_dir ${OUTPUT_DIR} \
    --output_dir ${OUTPUT_DIR} \
    --baseline_dir ${BASELINE_DIR} \
    --models ${MODELS} \
    --cvd_subjects ${SUBJECTS}

echo ""
echo "Spearman metric complete: $(date)"
free -h | head -2

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "========================================================"
echo "=== ALL DONE ==="
echo "End: $(date)"
echo "========================================================"
echo ""
echo "Output locations:"
echo "  Cosine:   ${BASE_RESULTS}/sim_cosine/"
echo "  Spearman: ${BASE_RESULTS}/sim_spearman/"
echo ""
echo "Result files:"
find ${BASE_RESULTS}/sim_cosine -name "*.json" | head -10
echo "..."
find ${BASE_RESULTS}/sim_spearman -name "*.json" | head -10
echo ""
free -h | head -2
