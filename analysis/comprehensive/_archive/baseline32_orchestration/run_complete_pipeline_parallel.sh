#!/bin/bash
# ============================================================================
# Master Script: Complete Pipeline with Parallel Execution
# ============================================================================
#
# This script orchestrates the entire analysis pipeline:
#   1. Phase 0 (parallel by subject): ROI building + Baseline analysis
#   2. Phase 1-4 (sequential): Group-level analyses
#
# Usage:
#   bash run_complete_pipeline_parallel.sh
#
# ============================================================================

echo "================================================================"
echo "Complete Analysis Pipeline - Parallel Execution"
echo "Start: $(date)"
echo "================================================================"

BASE_DIR=/scratch/connectome/haba6030/colorBlind
cd $BASE_DIR

# Create log directory
mkdir -p logs

echo ""
echo "Step 1: Submitting Phase 0 (Array Job - 10 subjects in parallel)..."
echo "================================================================"

# Submit Phase 0 array job
PHASE0_JOB=$(sbatch --parsable phase0_parallel.sbatch)

if [ -z "$PHASE0_JOB" ]; then
    echo "✗ Failed to submit Phase 0 job"
    exit 1
fi

echo "✓ Phase 0 submitted: Job ID $PHASE0_JOB"
echo "  - 10 array tasks (1 per subject)"
echo "  - Each task processes 4 ROIs sequentially"
echo "  - Estimated time: 8-12 hours per task"

echo ""
echo "Step 2: Submitting Phase 1-4 (Sequential, depends on Phase 0)..."
echo "================================================================"

# Submit Phase 1-4 with dependency on Phase 0
PHASE1TO4_JOB=$(sbatch --parsable --dependency=afterok:$PHASE0_JOB phase1to4_sequential.sbatch)

if [ -z "$PHASE1TO4_JOB" ]; then
    echo "✗ Failed to submit Phase 1-4 job"
    exit 1
fi

echo "✓ Phase 1-4 submitted: Job ID $PHASE1TO4_JOB"
echo "  - Depends on Phase 0 completion (afterok:$PHASE0_JOB)"
echo "  - Will start automatically when Phase 0 finishes"
echo "  - Estimated time: 2-4 hours"

echo ""
echo "================================================================"
echo "Pipeline Submitted Successfully!"
echo "================================================================"
echo ""
echo "Job Summary:"
echo "  Phase 0 (Parallel):  Job $PHASE0_JOB (array 1-10)"
echo "  Phase 1-4 (Sequential): Job $PHASE1TO4_JOB (depends on $PHASE0_JOB)"
echo ""
echo "Monitor with:"
echo "  squeue -u haba6030"
echo "  tail -f logs/phase0_v3_sub-*_${PHASE0_JOB}.out"
echo "  tail -f logs/phase1to4_v3_${PHASE1TO4_JOB}.out"
echo ""
echo "Total estimated time: 10-16 hours"
echo "================================================================"

exit 0
