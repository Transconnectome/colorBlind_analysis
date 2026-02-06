#!/bin/bash
#SBATCH --job-name=glm_pilot
#SBATCH --output=logs/glmsingle_pilot_%A_%a.out
#SBATCH --error=logs/glmsingle_pilot_%A_%a.err
#SBATCH --array=1-12
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=02:00:00

#######################################################################
# GLMsingle Pilot Test
#
# Tests 3 methods on 4 ROIs for subject 01:
# - FIR baseline (existing)
# - GLMsingle only
# - GLMsingle + Whitening
#
# Total: 4 ROIs × 3 methods = 12 jobs
#
# Expected runtime: 2-3 hours (parallel)
# Expected storage: ~6 GB
#######################################################################

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Paths
SCRIPT_DIR="/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/GLMsingle"
OUTPUT_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/GLMsingle_pilot"
LOG_DIR="${SCRIPT_DIR}/logs"

# Create directories
mkdir -p "${LOG_DIR}"
mkdir -p "${OUTPUT_DIR}"

# Configuration arrays
SUBJECT="01"
ROIS=("V1" "V2" "V3" "V4")
N_ROIS=${#ROIS[@]}

# Calculate ROI index and method from SLURM_ARRAY_TASK_ID
# Jobs 1-4: ROI 1-4, GLMsingle
# Jobs 5-8: ROI 1-4, GLMsingle + Whitening
# Jobs 9-12: ROI 1-4, FIR baseline (reference)

ROI_IDX=$(( (SLURM_ARRAY_TASK_ID - 1) % N_ROIS ))
METHOD_IDX=$(( (SLURM_ARRAY_TASK_ID - 1) / N_ROIS ))

ROI="${ROIS[$ROI_IDX]}"

# Determine method
case ${METHOD_IDX} in
    0)
        METHOD="glmsingle"
        ;;
    1)
        METHOD="whitened"
        ;;
    2)
        METHOD="fir_baseline"
        ;;
esac

echo "=================================="
echo "GLMsingle Pilot Test"
echo "=================================="
echo "Job ID: ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
echo "Node: $(hostname)"
echo "Subject: ${SUBJECT}"
echo "ROI: ${ROI}"
echo "Method: ${METHOD}"
echo "Start time: $(date)"
echo "=================================="
echo ""

# Create unique output directory for this run
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUN_OUTPUT_DIR="${OUTPUT_DIR}/${TIMESTAMP}_sub-${SUBJECT}_${ROI}"
mkdir -p "${RUN_OUTPUT_DIR}"

# Monitor memory in background
function monitor_memory() {
    while true; do
        free -h >> "${LOG_DIR}/memory_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.log"
        sleep 60
    done
}
monitor_memory &
MONITOR_PID=$!

# Trap to kill monitor on exit
trap "kill ${MONITOR_PID} 2>/dev/null" EXIT

# ===== Execute based on method =====

if [ "${METHOD}" == "fir_baseline" ]; then
    # FIR baseline: just copy existing results for comparison
    echo "Looking for existing FIR baseline..."

    FIR_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/BH2009_original_v3"
    FIR_FILE=$(find "${FIR_DIR}" -name "amplitudes_z.npy" -path "*sub-${SUBJECT}*${ROI}*" | head -n 1)

    if [ -n "${FIR_FILE}" ]; then
        echo "Found: ${FIR_FILE}"
        cp "${FIR_FILE}" "${RUN_OUTPUT_DIR}/amplitudes_z_fir_baseline.npy"
        echo "✓ FIR baseline copied"
    else
        echo "✗ FIR baseline not found"
        exit 1
    fi

elif [ "${METHOD}" == "glmsingle" ] || [ "${METHOD}" == "whitened" ]; then

    # Step 1: Run GLMsingle with residuals
    echo ""
    echo "Step 1/4: Running GLMsingle..."
    python3 "${SCRIPT_DIR}/01_glmsingle_with_residuals.py" \
        --subject "${SUBJECT}" \
        --roi "${ROI}" \
        --config full \
        --n-pcs 10 \
        --output-dir "${RUN_OUTPUT_DIR}"

    if [ $? -ne 0 ]; then
        echo "✗ Step 1 failed"
        exit 1
    fi
    echo "✓ Step 1 complete"

    if [ "${METHOD}" == "whitened" ]; then
        # Step 2: Estimate noise covariance
        echo ""
        echo "Step 2/4: Estimating noise covariance..."
        python3 "${SCRIPT_DIR}/02_estimate_noise_covariance.py" \
            --input-dir "${RUN_OUTPUT_DIR}" \
            --method ledoit_wolf

        if [ $? -ne 0 ]; then
            echo "✗ Step 2 failed"
            exit 1
        fi
        echo "✓ Step 2 complete"

        # Step 3: Compute whitened amplitudes
        echo ""
        echo "Step 3/4: Computing whitened amplitudes..."
        python3 "${SCRIPT_DIR}/03_glmsingle_whitened_amplitudes.py" \
            --input-dir "${RUN_OUTPUT_DIR}"

        if [ $? -ne 0 ]; then
            echo "✗ Step 3 failed"
            exit 1
        fi
        echo "✓ Step 3 complete"
    fi

    # Step 4: Evaluate vs FIR baseline
    echo ""
    echo "Step 4/4: Evaluating..."
    python3 "${SCRIPT_DIR}/04_evaluate_glmsingle_vs_fir.py" \
        --input-dir "${RUN_OUTPUT_DIR}" \
        --save-figures

    if [ $? -ne 0 ]; then
        echo "✗ Step 4 failed"
        exit 1
    fi
    echo "✓ Step 4 complete"
fi

# ===== Cleanup =====

# Stop memory monitor
kill ${MONITOR_PID} 2>/dev/null

# Print summary
echo ""
echo "=================================="
echo "Pilot Test Complete"
echo "=================================="
echo "Subject: ${SUBJECT}"
echo "ROI: ${ROI}"
echo "Method: ${METHOD}"
echo "Output: ${RUN_OUTPUT_DIR}"
echo "End time: $(date)"
echo "=================================="

# Check final memory usage
echo ""
echo "Final memory usage:"
free -h

# List output files
echo ""
echo "Output files:"
ls -lh "${RUN_OUTPUT_DIR}"

exit 0
