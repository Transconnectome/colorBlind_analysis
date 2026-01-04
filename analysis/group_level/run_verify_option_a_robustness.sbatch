#!/bin/bash
#SBATCH --job-name=verify_optA
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/logs/group_level/verify_option_a_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/logs/group_level/verify_option_a_%j.err
#SBATCH --time=02:00:00
#SBATCH --mem=64GB
#SBATCH --cpus-per-task=8
#SBATCH --nodelist=node2

echo "==========================================="
echo "Option A Robustness Verification"
echo "==========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Start time: $(date)"
echo ""

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Navigate to project directory
cd /scratch/connectome/haba6030/colorBlind

# Create log directory if needed
mkdir -p logs/group_level
mkdir -p results/group_level/option_a_verification

# Run verification script
echo "Running Option A robustness verification..."
echo ""

# Run all tests (reference robustness + permutation test)
# Use same parameters as Option 2D
python analysis/group_level/verify_option_a_robustness.py \
    --roi all \
    --test all \
    --n-perm 10000 \
    --timestamp baseline81_deob_determin \
    --dataset deoblique_v2

# Check exit status
if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Verification completed successfully!"
    echo ""
    echo "Results saved to:"
    echo "  - results/group_level/option_a_verification/"
    echo ""
    echo "Download with:"
    echo "  scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/results/group_level/option_a_verification/ results/group_level/"
else
    echo ""
    echo "✗ Verification failed - check error log"
    exit 1
fi

echo ""
echo "End time: $(date)"
echo "==========================================="
