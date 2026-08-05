#!/bin/bash
set -e

echo "Starting V1 Grid Search at $(date)"

source /opt/anaconda3/etc/profile.d/conda.sh
conda activate neuroImage

python step0_determine_optimal_dimensions.py \
    --roi V1 \
    --method both \
    --baseline-dir "/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/baseline" \
    --output-dir "./results/step0_grid_search" \
    2>&1 | tee results/v1_grid_search.log

echo "Completed V1 Grid Search at $(date)"
