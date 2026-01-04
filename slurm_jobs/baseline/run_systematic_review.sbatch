#!/bin/bash
#SBATCH --job-name=BH2009_system
#SBATCH --nodelist=node2
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64GB
#SBATCH --time=24:00:00

SUBJECT=$1
ROI=$2

# Create log files with proper naming
LOG_DIR="logs/systematic_review"
mkdir -p ${LOG_DIR}
exec > ${LOG_DIR}/sub-${SUBJECT}_${ROI}_${SLURM_JOB_ID}.out 2> ${LOG_DIR}/sub-${SUBJECT}_${ROI}_${SLURM_JOB_ID}.err

echo "================================================================"
echo "Systematic Preprocessing Review"
echo "Subject: ${SUBJECT}, ROI: ${ROI}"
echo "Start: $(date)"
echo "================================================================"

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Run all 144 configs using wrapper
python run_systematic_wrapper.py \
    --subject ${SUBJECT} \
    --roi ${ROI}

EXIT_CODE=$?

echo ""
echo "================================================================"
echo "Sorting and ranking results..."
echo "================================================================"

# Generate sorted rankings for each metric
python -c "
import json
import os
from pathlib import Path

output_base = f'derivatives/BH2009_systematic_review/sub-${SUBJECT}/${ROI}'
summary_file = f'{output_base}/summary_all_configs.json'

if os.path.exists(summary_file):
    with open(summary_file, 'r') as f:
        results = json.load(f)

    metrics_to_sort = [
        ('r2_median', 'descending'),
        ('classification_accuracy', 'descending'),
        ('reconstruction_error_mean', 'ascending'),
        ('snr_median', 'descending'),
        ('run_correlation_mean', 'descending'),
        ('hrf_consistency_mean', 'descending')
    ]

    rankings = {}
    for metric, order in metrics_to_sort:
        # Filter out failed configs
        valid = [r for r in results if 'metrics' in r and metric in r['metrics']]

        # Sort
        reverse = (order == 'descending')
        sorted_configs = sorted(valid, key=lambda x: x['metrics'][metric], reverse=reverse)

        # Save ranking
        rankings[metric] = [
            {
                'rank': i+1,
                'config_name': cfg['config_name'],
                'config_idx': cfg['config_idx'],
                'value': cfg['metrics'][metric]
            }
            for i, cfg in enumerate(sorted_configs[:20])  # Top 20
        ]

        # Print top 10
        print(f'\n=== Top 10 by {metric} ===')
        for i, cfg in enumerate(sorted_configs[:10]):
            print(f'{i+1:2d}. {cfg[\"config_name\"]:35s} = {cfg[\"metrics\"][metric]:.4f}')

    # Save rankings
    rankings_file = f'{output_base}/rankings_by_metric.json'
    with open(rankings_file, 'w') as f:
        json.dump(rankings, f, indent=2)

    print(f'\n✓ Rankings saved to: {rankings_file}')
"

echo ""
echo "================================================================"
echo "Complete: $(date)"
echo "Exit code: ${EXIT_CODE}"
echo "================================================================"

exit ${EXIT_CODE}
