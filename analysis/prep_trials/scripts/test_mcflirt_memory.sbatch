#!/bin/bash
#SBATCH --job-name=test_mcflirt
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/test_mcflirt_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/test_mcflirt_%j.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --no-requeue

################################################################################
# Test mcflirt Memory Usage
#
# Purpose: Profile actual memory usage to optimize array job settings
################################################################################

set -e

SUBJECT_ID="01"
RUN="1"

echo "================================================================================"
echo "Testing mcflirt Memory Usage: sub-${SUBJECT_ID} run-${RUN}"
echo "================================================================================"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Node: ${SLURM_NODELIST}"
echo "Start time: $(date)"
echo ""

# Directories
BIDS_DIR="/storage/connectome/haba6030/bids_editted"
WORK_DIR="/scratch/connectome/haba6030/colorBlind/work/test_mcflirt"

mkdir -p ${WORK_DIR}

# FSL setup
if ! command -v mcflirt &> /dev/null; then
    for FSL_PATH in /usr/local/fsl /opt/fsl; do
        if [ -d "${FSL_PATH}/bin" ]; then
            export FSLDIR=${FSL_PATH}
            export PATH="${FSLDIR}/bin:${PATH}"
            if [ -f "${FSLDIR}/etc/fslconf/fsl.sh" ]; then
                source ${FSLDIR}/etc/fslconf/fsl.sh
            fi
            break
        fi
    done
fi

if ! command -v mcflirt &> /dev/null; then
    echo "❌ ERROR: mcflirt not found"
    exit 1
fi

echo "✅ FSL found: $(which mcflirt)"
echo ""

# Input files
BOLD_ORIG="${BIDS_DIR}/sub-${SUBJECT_ID}/func/sub-${SUBJECT_ID}_task-rsvp_run-${RUN}_bold.nii.gz"
BOLD_MC="${WORK_DIR}/sub-${SUBJECT_ID}_run-${RUN}_bold_mc.nii.gz"

if [ ! -f "${BOLD_ORIG}" ]; then
    echo "❌ ERROR: BOLD not found: ${BOLD_ORIG}"
    exit 1
fi

# Get BOLD file info
echo "BOLD file info:"
echo "  File: ${BOLD_ORIG}"
FILE_SIZE=$(du -h ${BOLD_ORIG} | cut -f1)
echo "  Size (compressed): ${FILE_SIZE}"

NVOLS=$(fslinfo ${BOLD_ORIG} | grep "^dim4" | awk '{print $2}')
DIMS=$(fslinfo ${BOLD_ORIG} | grep "^dim[1-3]" | awk '{print $2}' | tr '\n' 'x' | sed 's/x$//')
echo "  Dimensions: ${DIMS}"
echo "  Volumes: ${NVOLS}"
echo ""

# =========================================================================
# Run mcflirt with /usr/bin/time profiling
# =========================================================================

echo "Running mcflirt with memory profiling..."
echo ""

REF_VOL=$((NVOLS / 2))

# Use /usr/bin/time -v for detailed resource usage
/usr/bin/time -v mcflirt \
    -in ${BOLD_ORIG} \
    -out ${BOLD_MC} \
    -refvol ${REF_VOL} \
    -plots \
    -verbose 1 \
    2>&1 | tee ${WORK_DIR}/time_report.txt

echo ""
echo "================================================================================"
echo "Resource Usage Summary"
echo "================================================================================"
echo ""

# Extract key metrics from time report
if [ -f "${WORK_DIR}/time_report.txt" ]; then
    echo "Memory usage:"
    grep "Maximum resident set size" ${WORK_DIR}/time_report.txt || echo "  Not available"

    echo ""
    echo "Time usage:"
    grep "Elapsed (wall clock) time" ${WORK_DIR}/time_report.txt || echo "  Not available"

    echo ""
    echo "CPU usage:"
    grep "Percent of CPU" ${WORK_DIR}/time_report.txt || echo "  Not available"

    # Extract peak memory in KB and convert to GB
    PEAK_MEM_KB=$(grep "Maximum resident set size" ${WORK_DIR}/time_report.txt | awk '{print $6}')
    if [ ! -z "${PEAK_MEM_KB}" ]; then
        PEAK_MEM_GB=$(awk "BEGIN {printf \"%.2f\", ${PEAK_MEM_KB}/1024/1024}")
        echo ""
        echo "Peak memory: ${PEAK_MEM_GB} GB"
    fi
fi

echo ""
echo "================================================================================"
echo "Recommendations"
echo "================================================================================"
echo ""

if [ ! -z "${PEAK_MEM_GB}" ]; then
    # Calculate recommended memory (peak * 1.5 for safety)
    REC_MEM=$(awk "BEGIN {printf \"%.0f\", ${PEAK_MEM_GB} * 1.5}")

    echo "Based on peak memory usage: ${PEAK_MEM_GB} GB"
    echo ""
    echo "Recommended settings:"
    echo ""

    # Conservative (node2: 450GB typically free)
    if (( $(echo "${REC_MEM} <= 8" | bc -l) )); then
        MAX_PARALLEL_CONSERVATIVE=$((450 / (REC_MEM * 2)))
        echo "  Conservative (safe for shared usage):"
        echo "    #SBATCH --mem=${REC_MEM}G"
        echo "    #SBATCH --array=1-60%${MAX_PARALLEL_CONSERVATIVE}"
        echo "    Total memory: $((REC_MEM * MAX_PARALLEL_CONSERVATIVE)) GB"
        echo ""

        MAX_PARALLEL_AGGRESSIVE=$((450 / REC_MEM))
        if [ ${MAX_PARALLEL_AGGRESSIVE} -gt 15 ]; then
            MAX_PARALLEL_AGGRESSIVE=15
        fi
        echo "  Aggressive (when node is idle):"
        echo "    #SBATCH --mem=${REC_MEM}G"
        echo "    #SBATCH --array=1-60%${MAX_PARALLEL_AGGRESSIVE}"
        echo "    Total memory: $((REC_MEM * MAX_PARALLEL_AGGRESSIVE)) GB"
        echo ""
    fi

    # Estimated completion time
    ELAPSED_SEC=$(grep "Elapsed (wall clock) time" ${WORK_DIR}/time_report.txt | awk -F'[(:)]' '{split($2,a,":"); print a[1]*60+a[2]}')
    if [ ! -z "${ELAPSED_SEC}" ]; then
        ELAPSED_MIN=$(awk "BEGIN {printf \"%.1f\", ${ELAPSED_SEC}/60}")
        echo "Time per run: ${ELAPSED_MIN} minutes"

        if [ ! -z "${MAX_PARALLEL_CONSERVATIVE}" ]; then
            TOTAL_TIME_CONSERVATIVE=$(awk "BEGIN {printf \"%.0f\", (60/${MAX_PARALLEL_CONSERVATIVE}) * ${ELAPSED_MIN}}")
            echo "Total time (conservative): ~${TOTAL_TIME_CONSERVATIVE} minutes"
        fi

        if [ ! -z "${MAX_PARALLEL_AGGRESSIVE}" ]; then
            TOTAL_TIME_AGGRESSIVE=$(awk "BEGIN {printf \"%.0f\", (60/${MAX_PARALLEL_AGGRESSIVE}) * ${ELAPSED_MIN}}")
            echo "Total time (aggressive): ~${TOTAL_TIME_AGGRESSIVE} minutes"
        fi
    fi
else
    echo "⚠️  Could not extract memory usage"
    echo "Check time_report.txt manually:"
    echo "  ${WORK_DIR}/time_report.txt"
fi

echo ""
echo "================================================================================"
echo "Test Complete"
echo "================================================================================"
echo "End time: $(date)"
echo ""

# Cleanup
rm -f ${BOLD_MC} ${BOLD_MC}.par ${BOLD_MC}.mat

exit 0
