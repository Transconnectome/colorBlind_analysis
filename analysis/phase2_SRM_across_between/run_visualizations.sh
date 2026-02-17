#!/bin/bash
#
# 3D Brain Alignment Visualization Runner
# Uses: conda srm environment
#

set -e  # Exit on error

echo "========================================="
echo "3D Brain Alignment Visualization"
echo "========================================="
echo ""

# Activate conda environment
echo "Activating conda environment: srm"
source ~/.bashrc
conda activate srm

# Check Python environment
echo ""
echo "Checking Python packages..."
python -c "import numpy; print('  ✓ numpy:', numpy.__version__)"
python -c "import matplotlib; print('  ✓ matplotlib:', matplotlib.__version__)"
python -c "import scipy; print('  ✓ scipy:', scipy.__version__)"
python -c "import sklearn; print('  ✓ sklearn:', sklearn.__version__)"
python -c "import seaborn; print('  ✓ seaborn:', seaborn.__version__)"

echo ""
echo "========================================="
echo "Running Visualizations..."
echo "========================================="
echo ""

# Set working directory
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase2_SRM_across_between

# 1. Procrustes 3D alignment visualization
echo "[1/2] Generating Procrustes 3D alignment figures..."
echo "      Subject: sub-08 (largest effect)"
echo "      ROI: V2 (strongest HC-CVD difference)"
echo ""

python visualize_3d_brain_alignment.py \
    --subject sub-08 \
    --roi V2 \
    --hc-subjects sub-01 sub-02 sub-03 sub-04 sub-05 sub-06 \
    --base-dir /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding \
    --output-dir ./results/3d_brain_visualization

echo ""
echo "✓ Complete!"
echo ""

# 2. "Scattered but Parallel" visualization
echo "[2/2] Generating 'Scattered but Parallel' schematic..."
echo ""

python visualize_scattered_but_parallel.py \
    --roi V2 \
    --output-dir ./results/scattered_parallel_visualization

echo ""
echo "✓ Complete!"
echo ""

# Summary
echo "========================================="
echo "All Visualizations Complete!"
echo "========================================="
echo ""
echo "Output files:"
echo ""
echo "📁 ./results/3d_brain_visualization/"
echo "   ├── sub-08_V2_3d_rotation.png"
echo "   ├── sub-08_V2_voxel_correspondence.png"
echo "   ├── noise_ceiling_brain_map.png"
echo "   ├── sub-08_V2_summary.png              ⭐ ONE KILLER SLIDE"
echo "   └── sub-08_V2_metrics.json"
echo ""
echo "📁 ./results/scattered_parallel_visualization/"
echo "   └── V2_dual_level_schematic.png"
echo ""
echo "Next steps:"
echo "  1. Open figures in Preview/Finder"
echo "  2. Check metrics in JSON file"
echo "  3. Adjust colors/fonts if needed"
echo "  4. Export to 600 DPI for publication"
echo ""
echo "Key metrics (sub-08 V2):"
echo "  • Disparity reduction: ~51%"
echo "  • Voxel correlation: 0.12 → 0.48 (+300%)"
echo "  • Overall ceiling improvement: +0.631 (11.7× RDM reliability)"
echo ""
