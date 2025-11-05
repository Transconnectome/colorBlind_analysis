# Server Workflow Instructions

## Step 1: Upload Required Files to Server

Run these commands from your **local terminal** (they will prompt for password):

```bash
# 1. Upload diagnostic analysis script
scp diagnostic_analysis.py node2:/scratch/connectome/haba6030/colorBlind/

# 2. Upload server config (will overwrite existing config.py on server)
scp config_server.py node2:/scratch/connectome/haba6030/colorBlind/config.py

# 3. Upload SLURM script
scp sbatch_diagnostic.sub node2:/scratch/connectome/haba6030/colorBlind/

# 4. Create logs directory on server (if it doesn't exist)
ssh node2 "mkdir -p /scratch/connectome/haba6030/colorBlind/logs"
```

**Files being uploaded:**
- `diagnostic_analysis.py` - Main diagnostic script
- `config_server.py` → `config.py` - Server-specific configuration
- `sbatch_diagnostic.sub` - SLURM batch script

---

## Step 2: Submit SLURM Job

SSH into the server and submit the job:

```bash
# Login to server
ssh node2

# Navigate to project directory
cd /scratch/connectome/haba6030/colorBlind

# Submit the job
sbatch sbatch_diagnostic.sub

# Check job status
squeue -u $USER

# To view job ID and details
squeue -u $USER -o "%.18i %.9P %.30j %.8u %.8T %.10M %.9l %.6D %R"
```

**Expected output:**
```
Submitted batch job XXXXXX
```

Make note of the job ID (XXXXXX).

---

## Step 3: Monitor Job Progress

```bash
# Check if job is still running
squeue -u $USER

# Watch output in real-time (replace XXXXXX with your job ID)
tail -f logs/diagnostic_XXXXXX.out

# Check for errors (replace XXXXXX with your job ID)
tail -f logs/diagnostic_XXXXXX.err

# To exit tail, press Ctrl+C
```

**Typical runtime:** 10-30 minutes depending on data size

---

## Step 4: Download Results (After Job Completes)

Run these commands from your **local terminal**:

```bash
# 1. Download diagnostic report
scp node2:/scratch/connectome/haba6030/colorBlind/derivatives/sub-01/diagnostic_report.txt ./

# 2. Download log files (replace XXXXXX with actual job ID)
scp node2:/scratch/connectome/haba6030/colorBlind/logs/diagnostic_XXXXXX.out ./logs/
scp node2:/scratch/connectome/haba6030/colorBlind/logs/diagnostic_XXXXXX.err ./logs/

# 3. Download any generated numpy arrays (if they exist)
scp node2:/scratch/connectome/haba6030/colorBlind/derivatives/sub-01/*.npy ./ 2>/dev/null || echo "No .npy files to download"
```

**Alternative: Download entire derivatives folder**
```bash
# Download full derivatives directory for comprehensive analysis
scp -r node2:/scratch/connectome/haba6030/colorBlind/derivatives/sub-01/ ./derivatives/
```

---

## Step 5: Check What to Download Based on Results

After the job completes, check what files were generated:

```bash
# SSH into server
ssh node2

# List all output files
ls -lh /scratch/connectome/haba6030/colorBlind/derivatives/sub-01/

# Look for:
# - diagnostic_report.txt (always generated)
# - *_responses.npy (ROI responses if ROIs exist)
# - *_responses_perrun.npy (per-run ROI responses)
```

Then download the files that exist using the commands in Step 4.

---

## Troubleshooting

### If job fails immediately:
```bash
# Check error log
cat logs/diagnostic_XXXXXX.err

# Common issues:
# 1. Conda environment not found → check 'conda activate nilearn' works
# 2. Data files not found → verify paths in config.py
# 3. Missing dependencies → check nilearn is installed
```

### If job runs but produces no output:
```bash
# Check if data files exist
ls -lh /scratch/connectome/haba6030/colorBlind/output/pilot/sub-01/func/
ls -lh /scratch/connectome/haba6030/colorBlind/pilot/sub-01/func/

# Check if derivatives directory exists
ls -lh /scratch/connectome/haba6030/colorBlind/derivatives/sub-01/
```

### To cancel a running job:
```bash
scancel XXXXXX  # Replace with your job ID
```

---

## Quick Reference - All Commands in Sequence

```bash
# LOCAL: Upload files
scp diagnostic_analysis.py node2:/scratch/connectome/haba6030/colorBlind/
scp config_server.py node2:/scratch/connectome/haba6030/colorBlind/config.py
scp sbatch_diagnostic.sub node2:/scratch/connectome/haba6030/colorBlind/
ssh node2 "mkdir -p /scratch/connectome/haba6030/colorBlind/logs"

# SERVER: Submit job
ssh node2
cd /scratch/connectome/haba6030/colorBlind
sbatch sbatch_diagnostic.sub
squeue -u $USER
exit

# SERVER: Monitor (optional, in separate terminal)
ssh node2
tail -f /scratch/connectome/haba6030/colorBlind/logs/diagnostic_XXXXXX.out

# LOCAL: Download results (after job completes)
scp node2:/scratch/connectome/haba6030/colorBlind/derivatives/sub-01/diagnostic_report.txt ./
scp node2:/scratch/connectome/haba6030/colorBlind/logs/diagnostic_XXXXXX.out ./logs/
scp node2:/scratch/connectome/haba6030/colorBlind/logs/diagnostic_XXXXXX.err ./logs/
```

---

## What Happens Next

Once you've downloaded the diagnostic results:
1. Claude will analyze the `diagnostic_report.txt` and log files
2. Identify which fixes from ANALYSIS_RECOMMENDATIONS.md are most critical
3. Implement the fixes in the code
4. Repeat the workflow with `systematic_testing.py` to test the improvements
