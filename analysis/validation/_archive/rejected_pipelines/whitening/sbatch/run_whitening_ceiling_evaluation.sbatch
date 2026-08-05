#!/bin/bash
#SBATCH --job-name=whitening_snr
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/whitening_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/whitening_%A_%a.err
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --array=1-40%6

# Phase 2: Whitening + Ceiling + SNR Evaluation
# Purpose: Test critical hypothesis - Does whitening improve data quality (ceiling + SNR)?
# Expected runtime: ~30-60 min per job
# Memory: ~16-20GB peak (24GB allocated for covariance estimation)
# UPDATED: Uses baseline_residuals (correct settings: no 2nd-level-intercept)

# Configuration
CONDA_ENV="nilearn"
SCRIPT_DIR="/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts"
OUTPUT_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/whitening_evaluation"
BASELINE_DIR="/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline_residuals"

# ROIs and subjects
ROIS=("V1" "V2" "V3" "hV4")
SUBJECTS=("01" "02" "03" "04" "05" "06" "07" "08" "09" "10")

# Calculate subject and ROI from SLURM_ARRAY_TASK_ID
TASK_ID=$SLURM_ARRAY_TASK_ID
N_ROIS=${#ROIS[@]}
SUBJECT_IDX=$(( (TASK_ID - 1) / N_ROIS ))
ROI_IDX=$(( (TASK_ID - 1) % N_ROIS ))

SUBJECT=${SUBJECTS[$SUBJECT_IDX]}
ROI=${ROIS[$ROI_IDX]}

echo "=================================================="
echo "Phase 2: Whitening + Ceiling + SNR Evaluation"
echo "Task ID: $SLURM_ARRAY_TASK_ID"
echo "Subject: sub-${SUBJECT}"
echo "ROI: ${ROI}"
echo "Node: $(hostname)"
echo "Start time: $(date)"
echo "=================================================="

# Create output directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JOB_OUTPUT_DIR="${OUTPUT_DIR}/${TIMESTAMP}_${SLURM_ARRAY_JOB_ID}"
mkdir -p ${JOB_OUTPUT_DIR}
mkdir -p /scratch/connectome/haba6030/colorBlind/analysis/validation/logs

# Activate conda environment
set -e
source ~/.bashrc
eval "$(conda shell.bash hook)"
conda activate ${CONDA_ENV}

# Verify Python environment
echo "Python: $(which python)"
echo "Python version: $(python --version)"

# Monitor memory usage in background
(while true; do
    MEM_USAGE=$(free -h | grep Mem | awk '{print $3 "/" $2}')
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}')
    echo "$(date +%H:%M:%S) Memory: ${MEM_USAGE}, CPU: ${CPU_USAGE}%"
    sleep 60
done) &
MONITOR_PID=$!

# Run Phase 2 evaluation
echo ""
echo "Running whitening + ceiling + SNR evaluation..."
echo "This will test: Does whitening improve data quality (ceiling + SNR)?"
echo ""

python ${SCRIPT_DIR}/evaluate_whitening_ceiling_snr.py \
    --subject ${SUBJECT} \
    --roi ${ROI} \
    --baseline_dir ${BASELINE_DIR} \
    --output_dir ${JOB_OUTPUT_DIR} \
    --n_ceiling_iterations 1000 \
    --n_jobs 4 \
    --save_whitened_data

EXIT_CODE=$?

# Stop memory monitor
kill $MONITOR_PID 2>/dev/null

# Report results
echo ""
echo "=================================================="
echo "Phase 2 Complete"
echo "Exit code: ${EXIT_CODE}"
echo "End time: $(date)"
echo "Output saved to: ${JOB_OUTPUT_DIR}"
echo "=================================================="

# Check and summarize output files
echo ""
echo "Output Files:"
if [ -f "${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_whitening_results.json" ]; then
    echo "✓ Whitening results JSON created"

    # Extract key metrics using Python
    python -c "
import json
import sys

try:
    with open('${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_whitening_results.json', 'r') as f:
        results = json.load(f)

    print('\n=== Key Results ===')

    # Noise ceiling comparison
    if 'noise_ceiling' in results:
        nc = results['noise_ceiling']
        print(f\"Noise Ceiling (Raw):      {nc.get('raw_split_half', 'N/A'):.3f}\")
        print(f\"Noise Ceiling (Whitened): {nc.get('whitened_split_half', 'N/A'):.3f}\")
        if 'improvement_percent' in nc:
            print(f\"Ceiling Improvement:      +{nc['improvement_percent']:.1f}%\")

    # SNR comparison
    if 'snr_analysis' in results:
        snr = results['snr_analysis']
        if 'pattern_snr' in snr:
            print(f\"\nPattern SNR (Raw):        {snr['pattern_snr'].get('raw', 'N/A'):.2f}\")
            print(f\"Pattern SNR (Whitened):   {snr['pattern_snr'].get('whitened', 'N/A'):.2f}\")
            print(f\"SNR Improvement:          +{snr['pattern_snr'].get('improvement_percent', 0):.1f}%\")

    # RDM reliability
    if 'rdm_reliability' in results:
        rdm = results['rdm_reliability']
        print(f\"\nRDM Correlation (Raw):         {rdm.get('raw', 'N/A'):.3f}\")
        print(f\"RDM Correlation (Raw+Proc):    {rdm.get('raw_procrustes', 'N/A'):.3f}\")
        print(f\"RDM Correlation (Whitened+Proc): {rdm.get('whitened_procrustes', 'N/A'):.3f}\")

    print('\n===================')

except Exception as e:
    print(f'Could not parse results: {e}', file=sys.stderr)
    sys.exit(1)
"

    if [ $? -eq 0 ]; then
        echo "✓ Results summary displayed"
    else
        echo "✗ Warning: Could not parse results"
        echo "Raw JSON content:"
        cat ${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_whitening_results.json
    fi
else
    echo "✗ Warning: Results JSON not found"
fi

if [ -f "${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_noise_cov.npy" ]; then
    echo "✓ Noise covariance matrix saved"
fi

if [ -f "${JOB_OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_amplitudes_whitened.npy" ]; then
    echo "✓ Whitened amplitudes saved"
fi

# List all output files
echo ""
echo "All output files:"
ls -lh ${JOB_OUTPUT_DIR}/ | grep "sub-${SUBJECT}_${ROI}"

exit ${EXIT_CODE}
