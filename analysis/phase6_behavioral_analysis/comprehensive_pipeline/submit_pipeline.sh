#!/bin/bash
# Filter-validation pipeline: chain preprocess (array) -> downstream (sequential)
# Usage:  bash submit_pipeline.sh           # full run on sub-08, sub-09 ses-02
#         SMOKE=1 bash submit_pipeline.sh   # smoke run flag (env var read by sbatch)

set -e

PROJECT_ROOT=/scratch/connectome/haba6030/colorBlind
cd ${PROJECT_ROOT}

PIPE_DIR=analysis/future_phase3_behavioral_analysis/comprehensive_pipeline
mkdir -p ${PIPE_DIR}/logs

echo "Submitting preprocess..."
JID1=$(sbatch --parsable ${PIPE_DIR}/01_preprocess_filter.sbatch)
echo "  JID1 (preprocess array): ${JID1}"

echo "Submitting downstream with dependency..."
JID2=$(sbatch --parsable --dependency=afterok:${JID1} ${PIPE_DIR}/02_downstream_filter.sbatch)
echo "  JID2 (downstream):       ${JID2}  (waits on ${JID1})"

echo ""
squeue -u $USER
echo ""
echo "Tail logs once jobs start running:"
echo "  tail -f ${PIPE_DIR}/logs/01_preprocess_sub-*_${JID1}.out"
echo "  tail -f ${PIPE_DIR}/logs/02_downstream_${JID2}.out"
