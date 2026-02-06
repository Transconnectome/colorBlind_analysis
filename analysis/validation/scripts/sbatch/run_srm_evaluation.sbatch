#!/bin/bash
#SBATCH --job-name=srm_eval
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --array=1-40
#SBATCH --output=../logs/srm_eval_%A_%a.out
#SBATCH --error=../logs/srm_eval_%A_%a.err

# ============================================================================
# SRM vs Procrustes Evaluation - Array Job
#
# Evaluates SRM with different feature counts (k) and compares with Procrustes
# baseline on z-scored data from Phase 1 Baseline.
#
# Array job: 40 subject-ROI pairs
# Memory: 32GB (SRM computation is memory-intensive)
# Time: ~3 hours for full k-tuning
#
# Prerequisites:
#   - Phase 1 Baseline completed
#   - BASELINE_RESULTS_DIR exists and contains:
#       * amplitudes_z.npy
#       * amplitudes_procrustes.npy
#
# Output:
#   results/srm_evaluation/{TIMESTAMP}/
#   ├── sub-{ID}_{ROI}_srm_results.json
#   └── sub-{ID}_{ROI}_srm_k_tuning.png
# ============================================================================

set -e  # Exit on error

echo "=========================================="
echo "SRM Evaluation - Array Job ${SLURM_ARRAY_TASK_ID}"
echo "=========================================="
echo "Job ID: ${SLURM_JOB_ID}"
echo "Array Task ID: ${SLURM_ARRAY_TASK_ID}"
echo "Node: $(hostname)"
echo "Start time: $(date)"
echo ""

# ============================================================================
# CONFIGURATION
# ============================================================================

# Baseline results directory (Phase 1)
BASELINE_RESULTS_DIR="/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline"

# Script paths
SCRIPT_DIR="/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts"
EVAL_SCRIPT="${SCRIPT_DIR}/evaluate_srm_vs_procrustes.py"

# Output directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="${SCRIPT_DIR}/results/srm_evaluation/${TIMESTAMP}"
mkdir -p "${OUTPUT_DIR}"

# Conda environment
CONDA_ENV="nilearn"

# ============================================================================
# SUBJECT-ROI MAPPING
# ============================================================================

# Define all subject-ROI pairs (40 total)
SUBJECTS=(
    "sub-01" "sub-01" "sub-01" "sub-01"  # V1, V2, V3, hV4
    "sub-02" "sub-02" "sub-02" "sub-02"
    "sub-03" "sub-03" "sub-03" "sub-03"
    "sub-04" "sub-04" "sub-04" "sub-04"
    "sub-05" "sub-05" "sub-05" "sub-05"
    "sub-06" "sub-06" "sub-06" "sub-06"
    "sub-07" "sub-07" "sub-07" "sub-07"
    "sub-08" "sub-08" "sub-08" "sub-08"
    "sub-09" "sub-09" "sub-09" "sub-09"
    "sub-10" "sub-10" "sub-10" "sub-10"
)

ROIS=(
    "V1" "V2" "V3" "hV4"
    "V1" "V2" "V3" "hV4"
    "V1" "V2" "V3" "hV4"
    "V1" "V2" "V3" "hV4"
    "V1" "V2" "V3" "hV4"
    "V1" "V2" "V3" "hV4"
    "V1" "V2" "V3" "hV4"
    "V1" "V2" "V3" "hV4"
    "V1" "V2" "V3" "hV4"
    "V1" "V2" "V3" "hV4"
)

# Get current task's subject and ROI (1-indexed)
SUBJECT=${SUBJECTS[$((SLURM_ARRAY_TASK_ID - 1))]}
ROI=${ROIS[$((SLURM_ARRAY_TASK_ID - 1))]}

echo "Task ${SLURM_ARRAY_TASK_ID}: ${SUBJECT} ${ROI}"
echo ""

# ============================================================================
# CHECK PREREQUISITES
# ============================================================================

echo "[Checking prerequisites...]"

# Check if baseline results directory exists
if [ ! -d "${BASELINE_RESULTS_DIR}" ]; then
    echo "ERROR: Baseline results directory not found: ${BASELINE_RESULTS_DIR}"
    echo "Please ensure Phase 1 baseline results are available."
    exit 1
fi

# Check if subject-ROI data exists
SUBJ_ROI_DIR="${BASELINE_RESULTS_DIR}/${SUBJECT}/${ROI}"
if [ ! -d "${SUBJ_ROI_DIR}" ]; then
    echo "ERROR: Subject-ROI directory not found: ${SUBJ_ROI_DIR}"
    exit 1
fi

# Check required files
REQUIRED_FILES=(
    "${SUBJ_ROI_DIR}/amplitudes_z.npy"
    "${SUBJ_ROI_DIR}/amplitudes_procrustes.npy"
)

for FILE in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "${FILE}" ]; then
        echo "ERROR: Required file not found: ${FILE}"
        exit 1
    fi
done

echo "  ✓ Baseline results directory exists"
echo "  ✓ Subject-ROI data exists"
echo "  ✓ All required files present"
echo ""

# ============================================================================
# ACTIVATE CONDA ENVIRONMENT
# ============================================================================

echo "[Activating conda environment: ${CONDA_ENV}]"

# Initialize conda
set -e
source ~/.bashrc
eval "$(conda shell.bash hook)"
conda activate "${CONDA_ENV}"

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate conda environment: ${CONDA_ENV}"
    exit 1
fi

echo "  ✓ Conda environment activated"
echo "  Python: $(which python)"
echo ""

# Check if BrainIAK is available
python -c "import brainiak; print('  ✓ BrainIAK version:', brainiak.__version__)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: BrainIAK not available in ${CONDA_ENV}"
    echo "Install with: conda install -c brainiak -c conda-forge brainiak"
    exit 1
fi

echo ""

# ============================================================================
# MEMORY MONITORING (Background)
# ============================================================================

echo "[Starting memory monitoring...]"

# Monitor memory usage every 30 seconds
MEMORY_LOG="${OUTPUT_DIR}/${SUBJECT}_${ROI}_memory.log"
(
    while true; do
        echo "$(date +%Y-%m-%d_%H:%M:%S) $(free -h | grep Mem)" >> "${MEMORY_LOG}"
        sleep 30
    done
) &
MONITOR_PID=$!

echo "  Memory log: ${MEMORY_LOG}"
echo "  Monitor PID: ${MONITOR_PID}"
echo ""

# ============================================================================
# RUN SRM EVALUATION
# ============================================================================

echo "[Running SRM evaluation...]"
echo "  Subject: ${SUBJECT}"
echo "  ROI: ${ROI}"
echo "  Output: ${OUTPUT_DIR}"
echo ""

START_TIME=$(date +%s)

# Use unbuffered output (-u) for real-time progress in logs
python -u "${EVAL_SCRIPT}" \
    --subject "${SUBJECT}" \
    --roi "${ROI}" \
    --output-dir "${OUTPUT_DIR}"

EXIT_CODE=$?

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo "=========================================="
if [ ${EXIT_CODE} -eq 0 ]; then
    echo "✓ SRM evaluation completed successfully"
else
    echo "✗ SRM evaluation failed with exit code ${EXIT_CODE}"
fi
echo "Elapsed time: ${ELAPSED}s"
echo "=========================================="

# ============================================================================
# CLEANUP
# ============================================================================

# Stop memory monitoring
kill ${MONITOR_PID} 2>/dev/null || true

# Save job info
JOB_INFO="${OUTPUT_DIR}/${SUBJECT}_${ROI}_job_info.txt"
cat > "${JOB_INFO}" <<EOF
Job Name: ${SLURM_JOB_NAME}
Job ID: ${SLURM_JOB_ID}
Array Task ID: ${SLURM_ARRAY_TASK_ID}
Subject: ${SUBJECT}
ROI: ${ROI}
Node: $(hostname)
CPUs: ${SLURM_CPUS_PER_TASK}
Memory: 32GB
Start Time: $(date -d @${START_TIME} +"%Y-%m-%d %H:%M:%S")
End Time: $(date -d @${END_TIME} +"%Y-%m-%d %H:%M:%S")
Elapsed: ${ELAPSED}s
Exit Code: ${EXIT_CODE}
EOF

echo ""
echo "End time: $(date)"
echo "Job info saved to: ${JOB_INFO}"

exit ${EXIT_CODE}
