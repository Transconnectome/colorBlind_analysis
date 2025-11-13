# Using Old Output Directory Structure

This guide explains how to use the reproduction pipeline with the old data structure in `/scratch/connectome/haba6030/colorBlind/output`.

## Quick Start

### Step 1: Discover Data Paths (On Server)

First, SSH to the server and run this to find where your data actually is:

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/reproduction_pipeline

# Run path discovery
python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd().parent))
from reproduction_pipeline.config_reproduction_output import discover_data_paths
discover_data_paths('/scratch/connectome/haba6030/colorBlind/output')
"
```

### Step 2: Update Config Paths

Based on the output from Step 1, edit `config_reproduction_output.py` to set the correct paths:

```python
# Around line 85-95
FMRIPREP_BASE = OUTPUT_DIR  # Or adjust based on where functional data is
```

Common structures:
- **Option A**: Everything in output
  ```python
  FMRIPREP_BASE = Path("/scratch/connectome/haba6030/colorBlind/output")
  ```

- **Option B**: fMRIPrep still in storage
  ```python
  FMRIPREP_BASE = Path("/storage/connectome/haba6030/fmriprep_out")
  ```

- **Option C**: Custom structure
  ```python
  # Modify get_func_img_path() and get_event_file_path() methods
  ```

### Step 3: Run Reproduction with Output Config

Use the `_output` versions of the scripts:

```bash
# On server
cd /scratch/connectome/haba6030/colorBlind/reproduction_pipeline

# 1. Build ROI masks
python build_rois_reproduction_output.py

# 2. Run analysis for V2
python run_reconstruction_reproduction_output.py --roi V2

# Or use SLURM
sbatch run_reproduction_output.sbatch
```

## File Structure

### New Files Created

```
reproduction_pipeline/
├── config_reproduction_output.py           # Config for /output directory
├── build_rois_reproduction_output.py       # ROI builder using output config
├── run_reconstruction_reproduction_output.py  # Analysis using output config
├── run_reproduction_output.sbatch          # SLURM script using output config
└── USE_OUTPUT_DIRECTORY.md                 # This file
```

### Output Location

Results will be saved to:
```
/scratch/connectome/haba6030/colorBlind/output/derivatives_reproduction/sub-01/
```

This prevents overwriting any existing derivatives.

## Differences from Main Config

| Aspect | Main Config | Output Config |
|--------|------------|---------------|
| **Data location** | `/storage/connectome/haba6030/fmriprep_out` | `/scratch/connectome/haba6030/colorBlind/output` |
| **Event files** | `pilot/sub-01/func/*.tsv` | Tries multiple locations (output, pilot, dataOct) |
| **Derivatives** | `derivatives/` | `output/derivatives_reproduction/` |
| **Subject naming** | Always uses SUB_ID | Uses FILE_PRE for backward compat |

## Troubleshooting

### "Functional image not found"

Check where your BOLD files actually are:

```bash
find /scratch/connectome/haba6030/colorBlind/output -name "*bold.nii.gz" -type f
```

Then update `FMRIPREP_BASE` in `config_reproduction_output.py`.

### "Event file not found"

Check where your event files are:

```bash
find /scratch/connectome/haba6030/colorBlind/output -name "*events.tsv" -type f
```

The config tries multiple locations automatically, but you can add more in `get_event_file_path()`.

### Path Discovery Output Example

```
Searching in: /scratch/connectome/haba6030/colorBlind/output
======================================================================

1. Subject directories:
   /scratch/connectome/haba6030/colorBlind/output/sub-01
     → func/
        BOLD files: 6
        Example: sub-01_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz
        Event files: 6
        Example: sub-01_task-rsvp_run-1_events.tsv

======================================================================
```

## Advanced: Manual Path Configuration

If automatic path detection doesn't work, manually edit the helper methods in `config_reproduction_output.py`:

```python
@classmethod
def get_func_img_path(cls, run, subject_id=None):
    """Get path to preprocessed functional image"""
    # YOUR CUSTOM PATH HERE
    return Path(f"/your/custom/path/sub-01/func/sub-01_task-rsvp_run-{run}_bold.nii.gz")

@classmethod
def get_event_file_path(cls, run, subject_id=None):
    """Get path to event file"""
    # YOUR CUSTOM PATH HERE
    return Path(f"/your/custom/path/sub-01/func/sub-01_task-rsvp_run-{run}_events.tsv")
```

## Verification

After configuration, verify paths are correct:

```bash
python verify_setup_output.py
```

This will check all required files exist before running the full pipeline.
