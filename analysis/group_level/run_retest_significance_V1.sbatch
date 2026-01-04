#!/bin/bash
#SBATCH --job-name=retest_V1
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/logs/group_level/retest_significance_V1_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/logs/group_level/retest_significance_V1_%j.err
#SBATCH --time=02:00:00
#SBATCH --mem=32GB
#SBATCH --cpus-per-task=4
#SBATCH --nodelist=node2

echo "=========================================================================="
echo "Statistical Significance Re-testing V1 ONLY (WITHOUT sub-02)"
echo "=========================================================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Start time: $(date)"
echo ""
echo "ROI: V1 only"
echo "HC subjects: 03, 05, 06, 07 (4 subjects, excluding sub-02)"
echo "CVD subjects: 08, 09, 10 (3 subjects)"
echo ""

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Navigate to project directory
cd /scratch/connectome/haba6030/colorBlind

# Create log directory if needed
mkdir -p logs/group_level
mkdir -p results/group_level/significance_tests_no_sub02

# Run statistical tests for V1 ONLY
echo "Running V1 statistical tests..."
echo ""

python analysis/group_level/retest_significance_no_sub02.py \
    --roi V1 \
    --n-perm 10000 \
    --n-boot 10000 \
    --timestamp baseline81_deob_determin \
    --dataset deoblique_v2

EXIT_CODE=$?

echo ""
echo "=========================================================================="
echo "V1 Job finished"
echo "Exit code: $EXIT_CODE"
echo "End time: $(date)"
echo "=========================================================================="
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ V1 statistical testing completed successfully!"
    echo ""
    echo "Results saved to:"
    echo "  - results/group_level/significance_tests_no_sub02/significance_tests_V1.json"
    echo "  - results/group_level/significance_tests_no_sub02/statistical_tests_V1.png"
    echo ""
    echo "Download with:"
    echo "  scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/results/group_level/significance_tests_no_sub02/significance_tests_V1.json results/group_level/significance_tests_no_sub02/"
    echo "  scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/results/group_level/significance_tests_no_sub02/statistical_tests_V1.png results/group_level/significance_tests_no_sub02/"
else
    echo "✗ V1 statistical testing failed - check error log"
fi

exit $EXIT_CODE
