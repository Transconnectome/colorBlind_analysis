#!/bin/bash
# Submit sequential LOCO jobs (3 alignments)

SCRIPT_DIR=$(dirname "$0")
cd /scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation

# Create log directory
mkdir -p logs

# LOCO jobs
echo "Submitting Sequential LOCO jobs..."
sbatch ${SCRIPT_DIR}/run_sequential_loco_raw.sbatch
sbatch ${SCRIPT_DIR}/run_sequential_loco_procrustes.sbatch
sbatch ${SCRIPT_DIR}/run_sequential_loco_srm.sbatch

echo "All 3 jobs submitted (30 tasks total: 3 alignments × 10 subjects)"
echo "Monitor: squeue -u \$USER"
echo ""
echo "Output directories:"
echo "  - results/loco_sequential/raw/"
echo "  - results/loco_sequential/procrustes/"
echo "  - results/loco_sequential/srm/"
