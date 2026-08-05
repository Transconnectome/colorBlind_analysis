#!/bin/bash
#SBATCH --job-name=glm_full
#SBATCH --output=logs/glmsingle_full_%A_%a.out
#SBATCH --error=logs/glmsingle_full_%A_%a.err
#SBATCH --array=1-40%6
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=03:00:00

#######################################################################
# GLMsingle Full Analysis
#
# Runs GLMsingle + Whitening pipeline on all 40 subject-ROI pairs:
# - 10 subjects (sub-01 to sub-10)
# - 4 ROIs (V1, V2, V3, V4)
#
# Total: 40 jobs, max 6 concurrent
#
# Expected runtime: 6-8 hours (parallel)
# Expected storage: ~22 GB
#######################################################################

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Paths
SCRIPT_DIR="/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/GLMsingle"
OUTPUT_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/GLMsingle_full"
LOG_DIR="${SCRIPT_DIR}/logs"

# Create directories
mkdir -p "${LOG_DIR}"
mkdir -p "${OUTPUT_DIR}"

# Configuration arrays
SUBJECTS=("01" "02" "03" "04" "05" "06" "07" "08" "09" "10")
ROIS=("V1" "V2" "V3" "V4")
N_SUBJECTS=${#SUBJECTS[@]}
N_ROIS=${#ROIS[@]}

# Calculate subject and ROI from SLURM_ARRAY_TASK_ID
# Layout: sub-01 V1, sub-01 V2, sub-01 V3, sub-01 V4, sub-02 V1, ...
SUBJECT_IDX=$(( (SLURM_ARRAY_TASK_ID - 1) / N_ROIS ))
ROI_IDX=$(( (SLURM_ARRAY_TASK_ID - 1) % N_ROIS ))

SUBJECT="${SUBJECTS[$SUBJECT_IDX]}"
ROI="${ROIS[$ROI_IDX]}"

echo "=================================="
echo "GLMsingle Full Analysis"
echo "=================================="
echo "Job ID: ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
echo "Node: $(hostname)"
echo "Subject: sub-${SUBJECT}"
echo "ROI: ${ROI}"
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
        echo "$(date): $(free -h | grep Mem)" >> "${LOG_DIR}/memory_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.log"
        sleep 120  # Every 2 minutes
    done
}
monitor_memory &
MONITOR_PID=$!

# Trap to kill monitor on exit
trap "kill ${MONITOR_PID} 2>/dev/null" EXIT

# ===== Step 1: Run GLMsingle with residuals =====

echo "Step 1/4: Running GLMsingle..."
echo "  Subject: sub-${SUBJECT}"
echo "  ROI: ${ROI}"
echo ""

/usr/bin/time -v python3 "${SCRIPT_DIR}/01_glmsingle_with_residuals.py" \
    --subject "${SUBJECT}" \
    --roi "${ROI}" \
    --config full \
    --n-pcs 10 \
    --output-dir "${RUN_OUTPUT_DIR}" \
    2>&1 | tee "${LOG_DIR}/step1_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.log"

if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "✗ Step 1 failed"
    exit 1
fi
echo "✓ Step 1 complete"
echo ""

# ===== Step 2: Estimate noise covariance =====

echo "Step 2/4: Estimating noise covariance..."
echo ""

/usr/bin/time -v python3 "${SCRIPT_DIR}/02_estimate_noise_covariance.py" \
    --input-dir "${RUN_OUTPUT_DIR}" \
    --method ledoit_wolf \
    2>&1 | tee "${LOG_DIR}/step2_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.log"

if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "✗ Step 2 failed"
    exit 1
fi
echo "✓ Step 2 complete"
echo ""

# ===== Step 3: Compute whitened amplitudes =====

echo "Step 3/4: Computing whitened amplitudes..."
echo ""

/usr/bin/time -v python3 "${SCRIPT_DIR}/03_glmsingle_whitened_amplitudes.py" \
    --input-dir "${RUN_OUTPUT_DIR}" \
    2>&1 | tee "${LOG_DIR}/step3_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.log"

if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "✗ Step 3 failed"
    exit 1
fi
echo "✓ Step 3 complete"
echo ""

# ===== Step 4: Evaluate vs FIR baseline =====

echo "Step 4/4: Evaluating vs FIR baseline..."
echo ""

/usr/bin/time -v python3 "${SCRIPT_DIR}/04_evaluate_glmsingle_vs_fir.py" \
    --input-dir "${RUN_OUTPUT_DIR}" \
    --save-figures \
    2>&1 | tee "${LOG_DIR}/step4_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.log"

if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "✗ Step 4 failed"
    exit 1
fi
echo "✓ Step 4 complete"
echo ""

# ===== Cleanup and summary =====

# Stop memory monitor
kill ${MONITOR_PID} 2>/dev/null

# Print summary
echo "=================================="
echo "Analysis Complete"
echo "=================================="
echo "Subject: sub-${SUBJECT}"
echo "ROI: ${ROI}"
echo "Output: ${RUN_OUTPUT_DIR}"
echo "End time: $(date)"
echo ""

# Extract key results from comparison JSON
if [ -f "${RUN_OUTPUT_DIR}/comparison_vs_fir.json" ]; then
    echo "Results Summary:"
    python3 -c "
import json
import sys
with open('${RUN_OUTPUT_DIR}/comparison_vs_fir.json') as f:
    results = json.load(f)

print(f\"  FIR baseline:            {results['FIR_baseline']['rdm_reliability']:.3f}\")
print(f\"  GLMsingle:               {results['GLMsingle']['rdm_reliability']:.3f} ({results['improvements']['glmsingle_vs_fir_pct']:+.1f}%)\")
print(f\"  GLMsingle + Whitening:   {results['GLMsingle_Whitened']['rdm_reliability']:.3f} ({results['improvements']['whitened_vs_fir_pct']:+.1f}%)\")
print(f\"\")
print(f\"  Recommendation: {results.get('recommendation', 'N/A')}\")
" 2>/dev/null || echo "  (Could not parse results)"
fi

echo ""
echo "Final memory usage:"
free -h

echo ""
echo "Output files:"
ls -lh "${RUN_OUTPUT_DIR}" | grep -E "(npy|json|png)$"

echo ""
echo "=================================="

exit 0
