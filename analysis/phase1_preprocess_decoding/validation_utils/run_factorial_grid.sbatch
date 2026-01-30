#!/bin/bash
#SBATCH --job-name=grid_factorial
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/logs/grid_factorial_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/logs/grid_factorial_%A_%a.err
#SBATCH --array=1-36%18
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --no-requeue

set -e
source ~/.bashrc
conda activate nilearn

SUBJECT="01"
ROI="V1"
DATASET="method3_header_mi"

CONDITION_ID=$(printf "c%02d" $SLURM_ARRAY_TASK_ID)

echo "========================================================================"
echo "Grid Resampling Factorial Experiment"
echo "========================================================================"
echo "Job ID: ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
echo "Condition: ${CONDITION_ID}"
echo "Node: $(hostname)"
echo "Start time: $(date)"
echo ""

cd /scratch/connectome/haba6030/colorBlind

# Load configuration
CONFIG_FILE="analysis/phase1_preprocess_decoding/factorial_config.json"

if [ ! -f "${CONFIG_FILE}" ]; then
    echo "ERROR: Configuration file not found: ${CONFIG_FILE}"
    exit 1
fi

PARAMS=$(python3 -c "
import json
with open('${CONFIG_FILE}') as f:
    config = json.load(f)
    cond = [c for c in config['conditions'] if c['id'] == '${CONDITION_ID}'][0]
    p = cond['params']
    add_2nd = 'yes' if p.get('add_2nd_intercept', False) else 'no'
    drift_name = cond['name'].split('_')[-1]  # Get drift name from condition name
    print(f\"{p['grid_resample']} {p['highpass']} {p['motion']} {p['drift']} {add_2nd} {drift_name}\")
")

read GRID_RESAMPLE HIGHPASS MOTION DRIFT ADD_2ND_INTERCEPT DRIFT_NAME <<< $PARAMS

echo "Parameters:"
echo "  Grid resample:     ${GRID_RESAMPLE}"
echo "  Highpass:          ${HIGHPASS}"
echo "  Motion:            ${MOTION}"
echo "  Drift:             ${DRIFT}"
echo "  2nd-level interc:  ${ADD_2ND_INTERCEPT}"
echo ""

# Format for output directory name
HP_STR="hp0"
if [ "$HIGHPASS" != "0" ]; then
    HP_STR="hp001"
fi

CONDITION_NAME="${CONDITION_ID}_${GRID_RESAMPLE}_${HP_STR}_${MOTION}_${DRIFT_NAME}"

# Output directory
OUTPUT_DIR="analysis/phase1_preprocess_decoding/results/grid_factorial/${CONDITION_NAME}/sub-${SUBJECT}/${ROI}"

echo "Output directory: ${OUTPUT_DIR}"
echo ""
echo "========================================================================"
echo "Starting FIR reconstruction"
echo "========================================================================"
echo ""

# Build command with conditional 2nd-level-intercept flag
CMD="python analysis/phase1_preprocess_decoding/fir_reconstruction_with_grid.py \
    --subject ${SUBJECT} \
    --roi ${ROI} \
    --dataset ${DATASET} \
    --grid-resample ${GRID_RESAMPLE} \
    --highpass ${HIGHPASS} \
    --motion ${MOTION} \
    --drift ${DRIFT} \
    --smooth 0 \
    --normalize-level none"

if [ "${ADD_2ND_INTERCEPT}" = "yes" ]; then
    CMD="${CMD} --2nd-level-intercept"
fi

CMD="${CMD} --output-dir ${OUTPUT_DIR}"

# Run FIR reconstruction
eval $CMD

EXIT_CODE=$?

echo ""
echo "========================================================================"
if [ ${EXIT_CODE} -eq 0 ]; then
    echo "✅ Condition ${CONDITION_ID} completed successfully"
    echo ""
    echo "Outputs saved to: ${OUTPUT_DIR}"
    echo ""
    echo "Files:"
    ls -lh ${OUTPUT_DIR}/*.npy ${OUTPUT_DIR}/*.json 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
    echo ""
else
    echo "❌ Condition ${CONDITION_ID} failed (exit code: ${EXIT_CODE})"
    echo ""
    echo "Check error log for details:"
    echo "  /scratch/connectome/haba6030/colorBlind/logs/grid_factorial_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.err"
fi
echo "========================================================================"
echo "End time: $(date)"
echo "========================================================================"

exit ${EXIT_CODE}
