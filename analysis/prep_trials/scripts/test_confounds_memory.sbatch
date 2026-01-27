#!/bin/bash
#SBATCH --job-name=test_confounds
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/test_confounds_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/test_confounds_%j.err
#SBATCH --time=00:15:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --no-requeue

################################################################################
# Test Confounds Generation Memory Usage
#
# Purpose: Profile memory usage to optimize array job settings
################################################################################

set -e

# Activate conda environment
source ~/.bashrc
conda activate nilearn

SUBJECT_ID="01"
RUN="1"

echo "================================================================================"
echo "Testing Confounds Generation Memory: sub-${SUBJECT_ID} run-${RUN}"
echo "================================================================================"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Node: ${SLURM_NODELIST}"
echo "Start time: $(date)"
echo ""

# Directories
SCRIPT_DIR="/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/scripts"
OUTPUT_DIR="/storage/connectome/haba6030/fmriprep_out_method3_header_mi"

# Check prerequisites
MOTION_PAR="${OUTPUT_DIR}/sub-${SUBJECT_ID}/func/sub-${SUBJECT_ID}_task-rsvp_run-${RUN}_desc-motion.par"

if [ ! -f "${MOTION_PAR}" ]; then
    echo "❌ Motion .par file not found: ${MOTION_PAR}"
    echo "   Run add_motion_correction.sbatch first!"
    exit 1
fi

echo "✅ Motion .par file found"
echo ""

# BOLD file info
BOLD_FILE="${OUTPUT_DIR}/sub-${SUBJECT_ID}/func/sub-${SUBJECT_ID}_task-rsvp_run-${RUN}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"

echo "BOLD file info:"
echo "  File: ${BOLD_FILE}"
FILE_SIZE=$(du -h ${BOLD_FILE} | cut -f1)
echo "  Size (compressed): ${FILE_SIZE}"
echo ""

# =========================================================================
# Run confounds generation with /usr/bin/time profiling
# =========================================================================

echo "Running confounds generation with memory profiling..."
echo ""

/usr/bin/time -v python ${SCRIPT_DIR}/generate_confounds_mcflirt.py \
    --subject ${SUBJECT_ID} \
    --run ${RUN} \
    --tr 1.5 \
    2>&1 | tee /tmp/confounds_time_report.txt

echo ""
echo "================================================================================"
echo "Resource Usage Summary"
echo "================================================================================"
echo ""

# Extract key metrics from time report
if [ -f "/tmp/confounds_time_report.txt" ]; then
    echo "Memory usage:"
    grep "Maximum resident set size" /tmp/confounds_time_report.txt || echo "  Not available"

    echo ""
    echo "Time usage:"
    grep "Elapsed (wall clock) time" /tmp/confounds_time_report.txt || echo "  Not available"

    echo ""
    echo "CPU usage:"
    grep "Percent of CPU" /tmp/confounds_time_report.txt || echo "  Not available"

    # Extract peak memory in KB and convert to GB
    PEAK_MEM_KB=$(grep "Maximum resident set size" /tmp/confounds_time_report.txt | awk '{print $6}')
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

    # Minimum 2GB
    if [ ${REC_MEM} -lt 2 ]; then
        REC_MEM=2
    fi

    echo "Based on peak memory usage: ${PEAK_MEM_GB} GB"
    echo "Recommended memory (with 1.5x safety): ${REC_MEM} GB"
    echo ""

    # Conservative (node2: 450GB typically free)
    MAX_PARALLEL_CONSERVATIVE=$((450 / (REC_MEM * 3)))
    if [ ${MAX_PARALLEL_CONSERVATIVE} -gt 20 ]; then
        MAX_PARALLEL_CONSERVATIVE=20
    fi

    echo "Conservative (safe for shared usage):"
    echo "  #SBATCH --mem=${REC_MEM}G"
    echo "  #SBATCH --array=1-60%${MAX_PARALLEL_CONSERVATIVE}"
    echo "  Total memory: $((REC_MEM * MAX_PARALLEL_CONSERVATIVE)) GB"
    echo ""

    # Aggressive
    MAX_PARALLEL_AGGRESSIVE=$((450 / REC_MEM))
    if [ ${MAX_PARALLEL_AGGRESSIVE} -gt 40 ]; then
        MAX_PARALLEL_AGGRESSIVE=40
    fi

    echo "Aggressive (when node is idle):"
    echo "  #SBATCH --mem=${REC_MEM}G"
    echo "  #SBATCH --array=1-60%${MAX_PARALLEL_AGGRESSIVE}"
    echo "  Total memory: $((REC_MEM * MAX_PARALLEL_AGGRESSIVE)) GB"
    echo ""

    # Estimated completion time
    ELAPSED_SEC=$(grep "Elapsed (wall clock) time" /tmp/confounds_time_report.txt | awk -F'[(:)]' '{split($2,a,":"); if(length(a)==3) print a[1]*3600+a[2]*60+a[3]; else print a[1]*60+a[2]}')
    if [ ! -z "${ELAPSED_SEC}" ]; then
        ELAPSED_MIN=$(awk "BEGIN {printf \"%.1f\", ${ELAPSED_SEC}/60}")
        echo "Time per run: ${ELAPSED_MIN} minutes"
        echo ""

        TOTAL_TIME_CONSERVATIVE=$(awk "BEGIN {printf \"%.0f\", (60/${MAX_PARALLEL_CONSERVATIVE}) * ${ELAPSED_MIN}}")
        echo "Total time (conservative): ~${TOTAL_TIME_CONSERVATIVE} minutes"

        TOTAL_TIME_AGGRESSIVE=$(awk "BEGIN {printf \"%.0f\", (60/${MAX_PARALLEL_AGGRESSIVE}) * ${ELAPSED_MIN}}")
        echo "Total time (aggressive): ~${TOTAL_TIME_AGGRESSIVE} minutes"
    fi
else
    echo "⚠️  Could not extract memory usage"
    echo "Check time_report.txt manually:"
    echo "  /tmp/confounds_time_report.txt"
fi

echo ""
echo "================================================================================"
echo "Test Complete"
echo "================================================================================"
echo "End time: $(date)"
echo ""

exit 0
