#!/bin/bash
# Download MNI Chain Diagnosis Results

echo "📥 Downloading MNI Chain Diagnosis Results..."
echo ""

# Create local directory
mkdir -p logs/mni_diagnosis

# Download all diagnosis results
echo "1️⃣ Downloading log files..."
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/logs/mni_diagnosis/* logs/mni_diagnosis/

echo ""
echo "✅ Download complete!"
echo ""
echo "📂 Files downloaded to: logs/mni_diagnosis/"
echo ""
echo "📊 Quick summary:"
echo ""

# Show summary for all subjects
for sub in 01 02 03 04 05 06 07 08 09 10; do
    if [ -f "logs/mni_diagnosis/mni_diag_sub-${sub}.out" ]; then
        echo "=== sub-${sub} ==="
        grep -A 3 "Summary" logs/mni_diagnosis/mni_diag_sub-${sub}.out || echo "  (No summary found)"
        echo ""
    fi
done

echo ""
echo "🔍 Next steps:"
echo "1. Review results: cat logs/mni_diagnosis/mni_diag_sub-01.out"
echo "2. Check fsleyes commands: cat logs/mni_diagnosis/mni_chain_diagnosis_sub-01.txt"
echo "3. Download images for visual inspection (see VISUAL_INSPECTION_GUIDE.md)"
