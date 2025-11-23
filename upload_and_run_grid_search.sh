#!/bin/bash
# Upload fixed grid search script and run

echo "=================================================="
echo "Uploading fixed grid_search_preprocessing.py"
echo "=================================================="

scp grid_search_preprocessing.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/

echo ""
echo "=================================================="
echo "Uploaded successfully!"
echo "=================================================="
echo ""
echo "Now run these commands on the server:"
echo ""
echo "  ssh haba6030@node2"
echo "  cd /scratch/connectome/haba6030/colorBlind"
echo "  sbatch run_grid_search.sbatch"
echo "  tail -f logs/grid_search_*.out"
echo ""
echo "To check for errors:"
echo "  cat logs/grid_search_*.err"
echo ""
