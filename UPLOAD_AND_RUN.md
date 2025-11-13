# How to Run Storage Diagnostic

## Step 1: Upload Diagnostic Script

```bash
# From your local machine
scp diagnose_storage.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

## Step 2: Submit Job

```bash
# SSH to server
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# Submit diagnostic job
sbatch diagnose_storage.sbatch

# Note the job ID
# Output will be: Submitted batch job 12345
```

## Step 3: Monitor Job

```bash
# Check if job is running
squeue -u haba6030

# Watch the output file (replace 12345 with your job ID)
tail -f diagnostic_report_12345.txt

# Or wait for it to finish and view
cat diagnostic_report_12345.txt
```

## Step 4: Download Report

```bash
# From your local machine (replace 12345 with actual job ID)
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/diagnostic_report_12345.txt \
    /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/
```

## What the Diagnostic Checks

1. **Directory Structure**
   - Does `sub-01/` exist?
   - Does `sub-P01/` exist?
   - When were they created?

2. **Brain Masks**
   - Are brain masks present in both?
   - Do they have the same number of voxels?
   - Are they in the expected location?

3. **Functional Images**
   - Reference image shapes (should be 97×115×97)
   - File sizes and checksums
   - Are files identical between sub-01 and sub-P01?

4. **Existing ROI Masks**
   - What ROI masks already exist?
   - Voxel counts (310 = GOOD, 536/553 = BAD)
   - When were they created?

5. **ROI Building Simulation**
   - Tests what voxel count WOULD result from each location
   - Shows if brain mask intersection is applied
   - Identifies which config produces 310 voxels

6. **Summary**
   - Clear recommendations on what to do next
   - Which configuration to use

## Expected Output

The report will show something like:

```
[sub-01 (ORIGINAL)] Testing ROI build
  ✓ Reference functional found
  ✓ Brain mask found
  Computing expected V2 voxel count...
    After brain mask: 310
    ✓✓✓ MATCHES GOOD RESULT (310 voxels)

[sub-P01 (RENAMED)] Testing ROI build
  ✓ Reference functional found
  ✗ Brain mask NOT found
  Computing expected V2 voxel count...
    ! Without brain mask: 536 voxels
    ✗✗✗ This explains the BAD result!
```

## After Getting Results

Share the diagnostic report output and I'll help you:
1. Interpret what happened
2. Create the correct config.py
3. Generate proper batch files for analysis
4. Rebuild ROI masks if needed

The diagnostic will definitively tell us WHY the voxel count changed!
