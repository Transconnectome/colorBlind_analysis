#!/bin/bash
#SBATCH --job-name=geom2func
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=6:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind
#SBATCH --output=logs/sim_batch_%A_%a.log
#SBATCH --error=logs/sim_batch_%A_%a.err
#SBATCH --array=0-7

# Geometry→Function Simulation: 48 combinations in 8 SLURM array tasks × 6 parallel per task
#
# Dimensions: 2 subjects × 2 ROIs × 3 models × 4 metrics = 48
# Strategy: 8 array tasks, each runs 6 combinations in parallel
#
# Usage:
#   sbatch scripts/run_all_sim.sbatch

source ~/.bashrc
conda activate nilearn

SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/cone_shift_pipeline/scripts
OUTPUT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/cone_shift_pipeline/results/sim

mkdir -p ${OUTPUT_DIR}
mkdir -p /scratch/connectome/haba6030/colorBlind/logs

# Define all 48 combinations as a flat array
# Format: "sub roi model metric"
COMBOS=(
    # Batch 0: sub-08, V1, all metrics for cone_1way + cone_3way (corr, cosine)
    "08 V1 cone_1way corr"
    "08 V1 cone_1way cosine"
    "08 V1 cone_1way triangle"
    "08 V1 cone_1way combination"
    "08 V1 cone_3way corr"
    "08 V1 cone_3way cosine"
    # Batch 1: sub-08, V1, remaining
    "08 V1 cone_3way triangle"
    "08 V1 cone_3way combination"
    "08 V1 fourier corr"
    "08 V1 fourier cosine"
    "08 V1 fourier triangle"
    "08 V1 fourier combination"
    # Batch 2: sub-08, V2, cone_1way + cone_3way (corr, cosine)
    "08 V2 cone_1way corr"
    "08 V2 cone_1way cosine"
    "08 V2 cone_1way triangle"
    "08 V2 cone_1way combination"
    "08 V2 cone_3way corr"
    "08 V2 cone_3way cosine"
    # Batch 3: sub-08, V2, remaining
    "08 V2 cone_3way triangle"
    "08 V2 cone_3way combination"
    "08 V2 fourier corr"
    "08 V2 fourier cosine"
    "08 V2 fourier triangle"
    "08 V2 fourier combination"
    # Batch 4: sub-09, V1, all metrics for cone_1way + cone_3way (corr, cosine)
    "09 V1 cone_1way corr"
    "09 V1 cone_1way cosine"
    "09 V1 cone_1way triangle"
    "09 V1 cone_1way combination"
    "09 V1 cone_3way corr"
    "09 V1 cone_3way cosine"
    # Batch 5: sub-09, V1, remaining
    "09 V1 cone_3way triangle"
    "09 V1 cone_3way combination"
    "09 V1 fourier corr"
    "09 V1 fourier cosine"
    "09 V1 fourier triangle"
    "09 V1 fourier combination"
    # Batch 6: sub-09, V2, cone_1way + cone_3way (corr, cosine)
    "09 V2 cone_1way corr"
    "09 V2 cone_1way cosine"
    "09 V2 cone_1way triangle"
    "09 V2 cone_1way combination"
    "09 V2 cone_3way corr"
    "09 V2 cone_3way cosine"
    # Batch 7: sub-09, V2, remaining
    "09 V2 cone_3way triangle"
    "09 V2 cone_3way combination"
    "09 V2 fourier corr"
    "09 V2 fourier cosine"
    "09 V2 fourier triangle"
    "09 V2 fourier combination"
)

# Each array task runs 6 combinations
START=$((SLURM_ARRAY_TASK_ID * 6))
END=$((START + 5))

echo "=== Array task ${SLURM_ARRAY_TASK_ID}: combos ${START}-${END} ==="
echo "Start time: $(date)"

PIDS=()
for i in $(seq ${START} ${END}); do
    if [ $i -ge ${#COMBOS[@]} ]; then
        break
    fi

    COMBO="${COMBOS[$i]}"
    read -r SUB ROI MODEL METRIC <<< "${COMBO}"

    echo "  Launching: sub-${SUB} ${ROI} ${MODEL} ${METRIC}"
    mpirun -np 1 python ${SCRIPT_DIR}/run_sim.py \
        --sub ${SUB} --roi ${ROI} --model ${MODEL} --metric ${METRIC} \
        --output_dir ${OUTPUT_DIR} \
        > ${OUTPUT_DIR}/sub-${SUB}_${ROI}_${MODEL}_${METRIC}.log 2>&1 &

    PIDS+=($!)
done

# Wait for all 6 parallel jobs to finish
echo "Waiting for ${#PIDS[@]} parallel jobs..."
FAIL=0
for pid in "${PIDS[@]}"; do
    wait $pid || FAIL=$((FAIL + 1))
done

echo "=== Array task ${SLURM_ARRAY_TASK_ID} done: ${FAIL} failures ==="
echo "End time: $(date)"
