#!/bin/bash
#SBATCH --job-name=test_wh
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/test_whitening_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/test_whitening_%j.err
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=02:00:00
#SBATCH --no-requeue

# TEST RUN: Phase 2 Whitening + Ceiling + SNR - Single Subject-ROI
# Purpose: Profile resource usage and optimize before full array job
# Test case: sub-01, V1 (representative case)
# Note: Whitening uses more memory due to covariance estimation
# UPDATED: Uses baseline_residuals (correct settings: no 2nd-level-intercept)

# Activate conda environment
set -e
source ~/.bashrc
eval "$(conda shell.bash hook)"
conda activate nilearn

# Configuration
SCRIPT_DIR="/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts"
OUTPUT_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/whitening_evaluation"
BASELINE_DIR="/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline_residuals"

# Test case
SUBJECT="01"
ROI="V1"

echo "=================================================="
echo "TEST RUN: Phase 2 Whitening + Ceiling + SNR"
echo "Subject: sub-${SUBJECT}"
echo "ROI: ${ROI}"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Node: $(hostname)"
echo "Start time: $(date)"
echo "=================================================="

# Create output directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JOB_OUTPUT_DIR="${OUTPUT_DIR}/TEST_${TIMESTAMP}_${SLURM_JOB_ID}"
mkdir -p ${JOB_OUTPUT_DIR}
mkdir -p /scratch/connectome/haba6030/colorBlind/analysis/validation/logs

# Check input files
echo "Input File Check:"
BASELINE_PATTERN="${BASELINE_DIR}/sub-${SUBJECT}/${ROI}/amplitudes_raw.npy"
BASELINE_FILE=$(ls ${BASELINE_PATTERN} 2>/dev/null | head -1)

if [ -z "$BASELINE_FILE" ]; then
    echo "ERROR: Baseline amplitudes not found!"
    echo "  Pattern: ${BASELINE_PATTERN}"
    exit 1
else
    echo "  ✓ Baseline amplitudes found: ${BASELINE_FILE}"
    BASELINE_SIZE=$(ls -lh ${BASELINE_FILE} | awk '{print $5}')
    echo "    Size: ${BASELINE_SIZE}"
fi

# Check for residuals (REQUIRED for whitening)
BASELINE_DIR_PARENT=$(dirname ${BASELINE_FILE})
RESIDUALS_FILE="${BASELINE_DIR_PARENT}/residuals_1st_level.npy"
if [ -f "$RESIDUALS_FILE" ]; then
    echo "  ✓ Residuals found: ${RESIDUALS_FILE}"
    RESIDUALS_SIZE=$(ls -lh ${RESIDUALS_FILE} | awk '{print $5}')
    echo "    Size: ${RESIDUALS_SIZE}"

    # Validate residuals shape
    python -c "
import numpy as np
try:
    residuals = np.load('${RESIDUALS_FILE}')
    n_samples, n_voxels = residuals.shape
    ratio = n_samples / n_voxels
    print(f'    Residuals shape: ({n_samples}, {n_voxels})')
    print(f'    Samples/Voxels ratio: {ratio:.2f}')
    if ratio >= 2.0:
        print('    ✓ Excellent ratio (>2.0) for stable covariance estimation')
    elif ratio >= 1.0:
        print('    ⚠ Acceptable ratio (>1.0)')
    else:
        print('    ✗ Low ratio (<1.0) - covariance may be unstable')
except Exception as e:
    print(f'    ✗ Error loading residuals: {e}')
"
else
    echo "  ✗ ERROR: Residuals not found at ${RESIDUALS_FILE}"
    echo "    Whitening REQUIRES residuals for noise covariance estimation"
    echo "    Run Phase 1 first: sbatch sbatch/run_baseline_save_residuals_fixed.sbatch"
    exit 1
fi
echo ""

# Check numpy shape of amplitudes
echo "Data Shape Check:"
python -c "
import numpy as np
try:
    data = np.load('${BASELINE_FILE}')
    print(f'  Amplitudes shape: {data.shape}')
    print(f'  Expected: (n_runs, 8_colors, n_voxels)')
    print(f'  Memory estimate for covariance: {data.shape[-1]**2 * 8 / 1024**3:.2f} GB')
except Exception as e:
    print(f'  Error loading data: {e}')
"
echo ""

# Resource monitoring in background
RESOURCE_LOG="${JOB_OUTPUT_DIR}/resource_usage.log"
echo "Timestamp,Memory_Used_GB,Memory_Total_GB,Memory_Free_GB,CPU_Percent" > ${RESOURCE_LOG}

(while true; do
    MEM_USED=$(free -g | grep Mem | awk '{print $3}')
    MEM_TOTAL=$(free -g | grep Mem | awk '{print $2}')
    MEM_FREE=$(free -g | grep Mem | awk '{print $4}')
    CPU_PERCENT=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    TIMESTAMP=$(date +%Y-%m-%d_%H:%M:%S)
    echo "${TIMESTAMP},${MEM_USED},${MEM_TOTAL},${MEM_FREE},${CPU_PERCENT}" >> ${RESOURCE_LOG}
    sleep 10
done) &
MONITOR_PID=$!

# Profile execution time and memory
echo "Starting evaluation with profiling..."
echo "This will compute:"
echo "  1. Noise covariance estimation (most memory-intensive)"
echo "  2. Whitening transformation"
echo "  3. Noise ceiling (raw vs whitened)"
echo "  4. SNR analysis (Pattern/GLM/Effective)"
echo "  5. RDM reliability comparison"
echo ""

/usr/bin/time -v python ${SCRIPT_DIR}/evaluate_whitening_ceiling_snr.py \
    --subject ${SUBJECT} \
    --roi ${ROI} \
    --baseline_dir ${BASELINE_DIR} \
    --output_dir ${JOB_OUTPUT_DIR} \
    --n_ceiling_iterations 1000 \
    --n_jobs 4 \
    --save_whitened_data \
    2>&1 | tee ${JOB_OUTPUT_DIR}/execution_profile.log

EXIT_CODE=${PIPESTATUS[0]}

# Stop resource monitor
kill $MONITOR_PID 2>/dev/null

# Extract profiling information
echo ""
echo "=================================================="
echo "PROFILING RESULTS"
echo "=================================================="

if [ -f "${JOB_OUTPUT_DIR}/execution_profile.log" ]; then
    echo ""
    echo "=== Memory Usage ==="
    grep "Maximum resident set size" ${JOB_OUTPUT_DIR}/execution_profile.log
    PEAK_MEM_KB=$(grep "Maximum resident set size" ${JOB_OUTPUT_DIR}/execution_profile.log | awk '{print $6}')
    if [ ! -z "$PEAK_MEM_KB" ]; then
        PEAK_MEM_GB=$(echo "scale=2; $PEAK_MEM_KB / 1024 / 1024" | bc)
        echo "  Peak memory: ${PEAK_MEM_GB} GB"

        # Memory recommendation with extra margin for covariance
        RECOMMENDED_MEM=$(echo "scale=0; ($PEAK_MEM_GB * 1.4 + 0.5) / 1" | bc)
        echo "  Recommended --mem: ${RECOMMENDED_MEM}G (40% safety margin for covariance)"

        # Warning if close to limit
        if (( $(echo "$PEAK_MEM_GB > 20" | bc -l) )); then
            echo "  ⚠ WARNING: Memory usage close to 24GB limit!"
            echo "  Consider: --mem=32G for safety"
        fi
    fi

    echo ""
    echo "=== CPU Usage ==="
    grep "Percent of CPU" ${JOB_OUTPUT_DIR}/execution_profile.log
    CPU_PERCENT=$(grep "Percent of CPU" ${JOB_OUTPUT_DIR}/execution_profile.log | awk '{print $7}' | sed 's/%//')
    if [ ! -z "$CPU_PERCENT" ]; then
        EFFECTIVE_CPUS=$(echo "scale=2; $CPU_PERCENT / 100" | bc)
        echo "  Effective CPUs used: ${EFFECTIVE_CPUS}"

        if (( $(echo "$EFFECTIVE_CPUS > 3.5" | bc -l) )); then
            echo "  ✓ Good CPU utilization with --cpus-per-task=4"
        elif (( $(echo "$EFFECTIVE_CPUS < 2.5" | bc -l) )); then
            echo "  → Consider --cpus-per-task=2 for better throughput"
        else
            echo "  ✓ Reasonable CPU utilization"
        fi
    fi

    echo ""
    echo "=== Runtime ==="
    grep "Elapsed (wall clock) time" ${JOB_OUTPUT_DIR}/execution_profile.log
    ELAPSED=$(grep "Elapsed (wall clock) time" ${JOB_OUTPUT_DIR}/execution_profile.log | awk '{print $8}')
    echo "  Elapsed time: ${ELAPSED}"

    # Parse and estimate array job time
    if [[ $ELAPSED =~ ([0-9]+):([0-9]+):([0-9]+) ]]; then
        HOURS=${BASH_REMATCH[1]#0}
        MINUTES=${BASH_REMATCH[2]#0}
        SECONDS=${BASH_REMATCH[3]#0}
        TOTAL_MINUTES=$(echo "$HOURS * 60 + $MINUTES + $SECONDS / 60" | bc)

        # With %6 parallelization
        ARRAY_BATCHES=$(echo "(40 + 5) / 6" | bc)  # ceiling
        TOTAL_ARRAY_MINUTES=$(echo "$TOTAL_MINUTES * $ARRAY_BATCHES" | bc)
        TOTAL_ARRAY_HOURS=$(echo "scale=1; $TOTAL_ARRAY_MINUTES / 60" | bc)

        echo "  Estimated array job time (40 jobs, %6 parallel): ${TOTAL_ARRAY_HOURS} hours"

        # Time recommendation
        if (( $(echo "$TOTAL_MINUTES < 30" | bc -l) )); then
            echo "  → Can reduce --time to 01:30:00"
        elif (( $(echo "$TOTAL_MINUTES > 90" | bc -l) )); then
            echo "  ⚠ Consider --time=04:00:00 for safety"
        else
            echo "  ✓ Current --time=03:00:00 is appropriate"
        fi
    fi

    echo ""
    echo "=== Disk I/O ==="
    grep "File system inputs" ${JOB_OUTPUT_DIR}/execution_profile.log
    grep "File system outputs" ${JOB_OUTPUT_DIR}/execution_profile.log
fi

# Resource usage timeline
if [ -f "${RESOURCE_LOG}" ]; then
    echo ""
    echo "=== Memory Usage Timeline ==="
    echo "Peak 5 memory readings during execution:"
    tail -n +2 ${RESOURCE_LOG} | awk -F',' '{print $2 " GB used, " $3 " GB free"}' | \
        sort -n -r | head -5 | nl
fi

# Check results
echo ""
echo "=================================================="
echo "OUTPUT VERIFICATION"
echo "=================================================="

RESULTS_FOUND=0

if [ -f "${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_whitening_results.json" ]; then
    echo "✓ Results JSON created"
    RESULTS_FOUND=1

    echo ""
    echo "=== Key Results ==="
    python -c "
import json
import sys

try:
    with open('${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_whitening_results.json', 'r') as f:
        results = json.load(f)

    # Noise ceiling
    if 'noise_ceiling' in results:
        nc = results['noise_ceiling']
        print(f\"Noise Ceiling:\")
        print(f\"  Raw:      {nc.get('raw_split_half', 'N/A'):.3f}\")
        print(f\"  Whitened: {nc.get('whitened_split_half', 'N/A'):.3f}\")
        if 'improvement_percent' in nc:
            print(f\"  Improvement: +{nc['improvement_percent']:.1f}%\")

    # SNR
    if 'snr_analysis' in results:
        snr = results['snr_analysis']
        if 'pattern_snr' in snr:
            print(f\"\nPattern SNR:\")
            print(f\"  Raw:      {snr['pattern_snr'].get('raw', 'N/A'):.2f}\")
            print(f\"  Whitened: {snr['pattern_snr'].get('whitened', 'N/A'):.2f}\")
            print(f\"  Improvement: +{snr['pattern_snr'].get('improvement_percent', 0):.1f}%\")

    # RDM reliability
    if 'rdm_reliability' in results:
        rdm = results['rdm_reliability']
        print(f\"\nRDM Correlation:\")
        print(f\"  Raw:              {rdm.get('raw', 'N/A'):.3f}\")
        print(f\"  Raw + Procrustes: {rdm.get('raw_procrustes', 'N/A'):.3f}\")
        print(f\"  Whitened + Proc:  {rdm.get('whitened_procrustes', 'N/A'):.3f}\")

except Exception as e:
    print(f'Error parsing results: {e}', file=sys.stderr)
    sys.exit(1)
"
else
    echo "✗ ERROR: Results JSON not found"
    EXIT_CODE=1
fi

if [ -f "${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_noise_cov.npy" ]; then
    echo ""
    echo "✓ Noise covariance matrix saved"
    COV_SIZE=$(ls -lh ${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_noise_cov.npy | awk '{print $5}')
    echo "  Size: ${COV_SIZE}"
fi

if [ -f "${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_amplitudes_whitened.npy" ]; then
    echo "✓ Whitened amplitudes saved"
    WHITENED_SIZE=$(ls -lh ${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_amplitudes_whitened.npy | awk '{print $5}')
    echo "  Size: ${WHITENED_SIZE}"
fi

if [ -f "${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_snr_comparison.png" ]; then
    echo "✓ SNR visualization created"
fi

if [ -f "${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_ceiling_comparison.png" ]; then
    echo "✓ Ceiling visualization created"
fi

# Optimization recommendations
echo ""
echo "=================================================="
echo "OPTIMIZATION RECOMMENDATIONS"
echo "=================================================="
echo ""

if [ ! -z "$PEAK_MEM_GB" ]; then
    if (( $(echo "$PEAK_MEM_GB < 18" | bc -l) )); then
        echo "✓ Memory usage comfortable (${PEAK_MEM_GB}G / 24G)"
        echo "  → Can increase parallelization from %6 to %8"
    elif (( $(echo "$PEAK_MEM_GB > 22" | bc -l) )); then
        echo "⚠ Memory usage high (${PEAK_MEM_GB}G / 24G)"
        echo "  → Reduce parallelization to %4"
        echo "  → Consider --mem=32G"
    else
        echo "✓ Memory usage acceptable (${PEAK_MEM_GB}G / 24G)"
        echo "  → Current --array=1-40%6 is appropriate"
    fi
fi

echo ""
echo "For full array job optimization:"
echo "  1. Adjust --mem based on peak memory + 30-40% margin"
echo "  2. Adjust %N in --array to fit node memory:"
echo "     N × --mem ≤ 360GB (Node2 safe limit)"
echo "  3. If runtime stable, can reduce --time"
echo ""

# Final summary
echo "=================================================="
echo "TEST COMPLETE"
echo "Exit code: ${EXIT_CODE}"
echo "End time: $(date)"
echo "=================================================="

if [ ${EXIT_CODE} -eq 0 ]; then
    echo ""
    echo "✓ Test successful!"
    echo ""
    echo "Review files:"
    echo "  ${JOB_OUTPUT_DIR}/resource_usage.log"
    echo "  ${JOB_OUTPUT_DIR}/execution_profile.log"
    echo "  ${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_whitening_results.json"
    echo ""
    echo "Next steps:"
    echo "  1. Review profiling results above"
    echo "  2. Adjust array job parameters if needed"
    echo "  3. Run: sbatch sbatch/run_whitening_ceiling_evaluation.sbatch"
else
    echo ""
    echo "✗ Test failed. Check logs:"
    echo "  Error log: /scratch/connectome/haba6030/colorBlind/analysis/validation/logs/test_whitening_${SLURM_JOB_ID}.err"
    echo "  Output: ${JOB_OUTPUT_DIR}/"
fi

echo ""
echo "Output saved to: ${JOB_OUTPUT_DIR}"

exit ${EXIT_CODE}
