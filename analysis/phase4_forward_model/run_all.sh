#!/bin/bash
# run_all.sh — Sequential orchestrator with SLURM dependency chaining
#
# Usage (from server):
#   cd /scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model
#   bash run_all.sh

set -e

echo "=== Future Phase 1: Forward Model Pipeline ==="
echo ""

# Step 1: SRM + stability gate
JOB1=$(sbatch --parsable run_step1_srm.sbatch)
echo "Step 1 (SRM + gate): job $JOB1"

# Step 2: Group prior + projection (after step 1 succeeds)
JOB2=$(sbatch --parsable --dependency=afterok:$JOB1 run_step2_prior.sbatch)
echo "Step 2 (prior + W0): job $JOB2 (after $JOB1)"

# Step 3: Fine-tune per subject (after step 2 succeeds)
JOB3=$(sbatch --parsable --dependency=afterok:$JOB2 run_step3_finetune.sbatch)
echo "Step 3 (fine-tune): job $JOB3 (after $JOB2)"

# Step 4: Validate per subject (after step 3 succeeds)
JOB4=$(sbatch --parsable --dependency=afterok:$JOB3 run_step4_validate.sbatch)
echo "Step 4 (validate):  job $JOB4 (after $JOB3)"

echo ""
echo "Pipeline submitted. Monitor with:"
echo "  squeue -u \$USER"
echo "  tail -f logs/step*"
