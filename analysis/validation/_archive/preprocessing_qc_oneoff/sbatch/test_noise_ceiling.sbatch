#!/bin/bash
#SBATCH --job-name=test_nc
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/test_noise_ceiling_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/test_noise_ceiling_%j.err
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=20G
#SBATCH --time=01:00:00

# TEST RUN: Phase 1 Noise Ceiling - Single Subject-ROI
# Purpose: Profile resource usage and optimize before full array job
# Test case: sub-01, V1 (representative case)

# Configuration
CONDA_ENV="nilearn"
SCRIPT_DIR="/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts"
OUTPUT_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/noise_ceiling_evaluation"
BASELINE_DIR="/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline"

# Test case
SUBJECT="01"
ROI="V1"

echo "=================================================="
echo "TEST RUN: Phase 1 Noise Ceiling Evaluation"
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

# Activate conda environment
source /home/haba6030/miniconda3/etc/profile.d/conda.sh
conda activate ${CONDA_ENV}

# Verify environment
echo ""
echo "Environment Check:"
echo "  Python: $(which python)"
echo "  Python version: $(python --version)"
echo "  Working directory: $(pwd)"
echo ""

# Check input files
echo "Input File Check:"
BASELINE_PATTERN="${BASELINE_DIR}/sub-${SUBJECT}/${ROI}/amplitudes_raw.npy"
BASELINE_FILE=$(ls ${BASELINE_PATTERN} 2>/dev/null | head -1)

if [ -z "$BASELINE_FILE" ]; then
    echo "ERROR: Baseline amplitudes not found!"
    echo "  Pattern: ${BASELINE_PATTERN}"
    echo "  Please verify baseline results exist."
    exit 1
else
    echo "  ✓ Baseline amplitudes found: ${BASELINE_FILE}"
    BASELINE_SIZE=$(ls -lh ${BASELINE_FILE} | awk '{print $5}')
    echo "    Size: ${BASELINE_SIZE}"
fi
echo ""

# Resource monitoring in background
RESOURCE_LOG="${JOB_OUTPUT_DIR}/resource_usage.log"
echo "Timestamp,Memory_Used_GB,Memory_Total_GB,CPU_Percent" > ${RESOURCE_LOG}

(while true; do
    MEM_USED=$(free -g | grep Mem | awk '{print $3}')
    MEM_TOTAL=$(free -g | grep Mem | awk '{print $2}')
    CPU_PERCENT=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    TIMESTAMP=$(date +%Y-%m-%d_%H:%M:%S)
    echo "${TIMESTAMP},${MEM_USED},${MEM_TOTAL},${CPU_PERCENT}" >> ${RESOURCE_LOG}
    sleep 10
done) &
MONITOR_PID=$!

# Profile execution time and memory
echo "Starting evaluation with profiling..."
echo ""

/usr/bin/time -v python ${SCRIPT_DIR}/evaluate_with_noise_ceiling.py \
    --subject ${SUBJECT} \
    --roi ${ROI} \
    --baseline_dir ${BASELINE_DIR} \
    --output_dir ${JOB_OUTPUT_DIR} \
    --n_iterations 1000 \
    --n_jobs 4 \
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

        # Memory recommendation
        RECOMMENDED_MEM=$(echo "scale=0; $PEAK_MEM_GB * 1.3 / 1" | bc)
        echo "  Recommended --mem: ${RECOMMENDED_MEM}G (30% safety margin)"
    fi

    echo ""
    echo "=== CPU Usage ==="
    grep "Percent of CPU" ${JOB_OUTPUT_DIR}/execution_profile.log
    CPU_PERCENT=$(grep "Percent of CPU" ${JOB_OUTPUT_DIR}/execution_profile.log | awk '{print $7}' | sed 's/%//')
    if [ ! -z "$CPU_PERCENT" ]; then
        EFFECTIVE_CPUS=$(echo "scale=2; $CPU_PERCENT / 100" | bc)
        echo "  Effective CPUs used: ${EFFECTIVE_CPUS}"

        # CPU recommendation
        if (( $(echo "$EFFECTIVE_CPUS > 3.5" | bc -l) )); then
            echo "  Recommendation: Current --cpus-per-task=4 is appropriate"
        elif (( $(echo "$EFFECTIVE_CPUS < 2.0" | bc -l) )); then
            echo "  Recommendation: Consider --cpus-per-task=2 to allow more concurrent jobs"
        else
            echo "  Recommendation: Current --cpus-per-task=4 is reasonable"
        fi
    fi

    echo ""
    echo "=== Runtime ==="
    grep "Elapsed (wall clock) time" ${JOB_OUTPUT_DIR}/execution_profile.log
    ELAPSED=$(grep "Elapsed (wall clock) time" ${JOB_OUTPUT_DIR}/execution_profile.log | awk '{print $8}')
    echo "  Elapsed time: ${ELAPSED}"

    # Parse time and estimate for array job
    if [[ $ELAPSED =~ ([0-9]+):([0-9]+):([0-9]+) ]]; then
        HOURS=${BASH_REMATCH[1]#0}
        MINUTES=${BASH_REMATCH[2]#0}
        SECONDS=${BASH_REMATCH[3]#0}
        TOTAL_MINUTES=$(echo "$HOURS * 60 + $MINUTES + $SECONDS / 60" | bc)

        # Estimate for 40 jobs with %8 parallelization
        ARRAY_BATCHES=$(echo "40 / 8" | bc)
        TOTAL_ARRAY_MINUTES=$(echo "$TOTAL_MINUTES * $ARRAY_BATCHES" | bc)
        TOTAL_ARRAY_HOURS=$(echo "scale=1; $TOTAL_ARRAY_MINUTES / 60" | bc)

        echo "  Estimated array job time (40 jobs, %8 parallel): ${TOTAL_ARRAY_HOURS} hours"
    fi
fi

# Resource usage timeline
if [ -f "${RESOURCE_LOG}" ]; then
    echo ""
    echo "=== Resource Usage Timeline ==="
    echo "Peak memory usage during execution:"
    tail -n +2 ${RESOURCE_LOG} | awk -F',' '{print $2}' | sort -n | tail -5 | \
        awk '{print "  " $1 " GB"}'
fi

# Check results
echo ""
echo "=== Output Verification ==="
if [ -f "${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_noise_ceiling.json" ]; then
    echo "✓ Results JSON created successfully"
    echo ""
    echo "Key Results:"
    python -c "
import json
import sys

try:
    with open('${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_noise_ceiling.json', 'r') as f:
        results = json.load(f)

    print(f\"  Split-half reliability: {results.get('split_half_corrected', 'N/A'):.3f}\")
    print(f\"  Split-half CI: [{results.get('split_half_ci_lower', 'N/A'):.3f}, {results.get('split_half_ci_upper', 'N/A'):.3f}]\")
    print(f\"  Split-half raw: {results.get('split_half_raw', 'N/A'):.3f}\")
except Exception as e:
    print(f'Could not parse results: {e}', file=sys.stderr)
    sys.exit(1)
"
else
    echo "✗ ERROR: Results JSON not found"
    EXIT_CODE=1
fi

if [ -f "${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_noise_ceiling_plot.png" ]; then
    echo "✓ Visualization created"
    PLOT_SIZE=$(ls -lh ${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_noise_ceiling_plot.png | awk '{print $5}')
    echo "  Size: ${PLOT_SIZE}"
else
    echo "✗ Warning: Visualization not found"
fi

# Optimization recommendations
echo ""
echo "=================================================="
echo "OPTIMIZATION RECOMMENDATIONS"
echo "=================================================="
echo ""
echo "Based on this test run, for the full array job:"
echo ""
echo "1. If peak memory < 16GB:"
echo "   → Reduce --mem=20G to --mem=16G"
echo "   → Increase parallelization from %8 to %10"
echo ""
echo "2. If runtime < 20 minutes:"
echo "   → Reduce --time=02:00:00 to --time=01:00:00"
echo ""
echo "3. If CPU usage < 200%:"
echo "   → Reduce --cpus-per-task=4 to --cpus-per-task=2"
echo "   → Update --n_jobs in Python script to 2"
echo ""
echo "4. Current configuration (--array=1-40%8):"
echo "   → 5 batches × runtime = total time"
echo ""

# Final summary
echo "=================================================="
echo "TEST COMPLETE"
echo "Exit code: ${EXIT_CODE}"
echo "End time: $(date)"
echo "Output directory: ${JOB_OUTPUT_DIR}"
echo "=================================================="

if [ ${EXIT_CODE} -eq 0 ]; then
    echo ""
    echo "✓ Test successful! Review profiling results above."
    echo ""
    echo "Next steps:"
    echo "  1. Review ${JOB_OUTPUT_DIR}/resource_usage.log"
    echo "  2. Review ${JOB_OUTPUT_DIR}/execution_profile.log"
    echo "  3. Adjust array job parameters if needed"
    echo "  4. Run: sbatch sbatch/run_noise_ceiling_evaluation.sbatch"
else
    echo ""
    echo "✗ Test failed. Check error log:"
    echo "  ${JOB_OUTPUT_DIR}/../test_noise_ceiling_${SLURM_JOB_ID}.err"
fi

exit ${EXIT_CODE}
