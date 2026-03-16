#!/bin/bash
#SBATCH --job-name=metric_norm_test
#SBATCH --output=logs/slurm_%j.out
#SBATCH --error=logs/slurm_%j.err
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:30:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/pre_validation

# Create output directories in same folder as script
mkdir -p logs results

echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "Working directory: $(pwd)"
echo "Started: $(date)"
echo "=========================================="

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Monitor resources in background
echo ""
echo "Starting resource monitor..."
(
    while true; do
        MEM=$(ps aux | grep -E "python.*test_rdm" | grep -v grep | awk '{sum+=$6} END {printf "%.1f GB", sum/1024/1024}')
        echo "[$(date +%H:%M:%S)] Memory: $MEM"
        sleep 60
    done
) &
MONITOR_PID=$!

# Run full analysis
echo ""
echo "Running full analysis (all subjects, ROIs, conditions)..."
echo ""

python test_rdm_metric_and_normalization_server.py

EXIT_CODE=$?

# Kill monitor
kill $MONITOR_PID 2>/dev/null

echo ""
echo "=========================================="
echo "Finished: $(date)"
echo "Exit code: $EXIT_CODE"
echo "=========================================="

# Show output files
echo ""
echo "Output files:"
ls -lh results/metric_norm_test_*.json
echo ""
echo "Log files:"
ls -lh logs/slurm_*.out

# Provide download instructions
echo ""
echo "=========================================="
echo "Download results with:"
echo "scp haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/pre_validation/results/metric_norm_test_*.json ."
echo "scp haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/pre_validation/logs/slurm_$SLURM_JOB_ID.out ."
echo "=========================================="
