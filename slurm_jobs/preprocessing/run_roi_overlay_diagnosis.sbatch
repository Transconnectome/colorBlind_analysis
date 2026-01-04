#!/bin/bash
#SBATCH --job-name=roi_overlay_diag
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=2:00:00
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/logs/roi_overlay_diagnosis_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/logs/roi_overlay_diagnosis_%j.err

# Diagnostic test for ROI overlay issue (Sub-03, 06, 07)
# Test subjects: 03, 06, 07 (problem) + 01 (control) = 4 subjects
# Test ROIs: V1, V2 = 2 ROIs
# Parameter combinations: 24 configs
# Total tests: 4 × 2 × 24 = 192 tests

echo "================================================================================"
echo "ROI OVERLAY DIAGNOSIS - Parameter Grid Test"
echo "================================================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Start time: $(date)"
echo ""
echo "Test subjects: Sub-03, 06, 07 (problem) + Sub-01 (control)"
echo "Test ROIs: V1, V2"
echo "Parameter combinations: 24"
echo "Total tests: 192"
echo "================================================================================"

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Navigate to project directory
cd /scratch/connectome/haba6030/colorBlind

# Create logs directory if not exists
mkdir -p logs

# Run diagnostic script
echo ""
echo "Running diagnostic parameter grid search..."
echo ""

python roi_overlay_diagnosis_1204.py

# Check exit status
EXIT_CODE=$?

echo ""
echo "================================================================================"
echo "Job completed with exit code: $EXIT_CODE"
echo "End time: $(date)"
echo "================================================================================"

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ SUCCESS: Diagnostic test completed"
    echo ""
    echo "Results saved in: derivatives/roi_overlay_diagnosis_[timestamp]/"
    echo "  - diagnostic_results.json (detailed results)"
    echo "  - diagnostic_summary.txt (summary report)"
    echo ""
    echo "Download results (from local machine):"
    echo "  scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/roi_overlay_diagnosis_*/diagnostic_summary.txt ./logs/"
    echo "  scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/roi_overlay_diagnosis_*/diagnostic_results.json ./logs/"
else
    echo "❌ FAILED: Diagnostic test failed with exit code $EXIT_CODE"
    echo "Check error log: logs/roi_overlay_diagnosis_${SLURM_JOB_ID}.err"
fi

exit $EXIT_CODE
