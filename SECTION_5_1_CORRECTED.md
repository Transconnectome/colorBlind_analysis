## 5. COMPLETE CODE WALKTHROUGH

### 5.1 Main Execution Flow

**⭐ CRITICAL: NO `main()` FUNCTION EXISTS**

**File:** `fir_reconstruction_zScore.py` (1,814 lines)

The code does NOT use a `main()` function. Instead, it runs **sequentially from top to bottom** with direct execution starting at line 285.

---

#### 5.1.1 Code Structure Overview

```
┌──────────────────────────────────────────────────────────┐
│ Lines 1-40: Module imports and docstring                │
│ Lines 41-114: Configuration (TR, N_RUNS, color mappings)│
│ Lines 115-267: Helper functions (THESE EXIST!)          │
│   - diag_linear_predict()                               │
│   - circular_diff_deg()                                 │
│   - circular_mean_deg()                                 │
│   - lab_hue_to_rgb()                                    │
│   - lab2rgb_accurate()                                  │
│   - get_stimulus_color_rgb()                            │
│   - create_basis_functions()                            │
│   - hue_to_channels()                                   │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│ Lines 268-283: parse_args() function (ONLY FUNCTION)    │
│   - Defines argparse.ArgumentParser                     │
│   - Returns parsed arguments                            │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│ Lines 285-373: MAIN EXECUTION STARTS (Direct code!)     │
│   - args = parse_args()                                 │
│   - Setup paths (pilot vs test)                         │
│   - Create output directory                             │
│   - Setup dual logging                                  │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│ Lines 375-404: Load ROI mask (Direct code!)             │
│   - Load NIfTI file                                     │
│   - Create NiftiMasker                                  │
│   - Count voxels                                        │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│ Lines 405-459: Load data with FOR-LOOP (Direct code!)   │
│   - FOR-LOOP over 6 runs                                │
│   - Load functional images                              │
│   - Load events                                         │
│   - Drop first 4 volumes                                │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│ Lines 460-542: FIR GLM with FOR-LOOPS (Direct code!)    │
│   - FOR-LOOP over runs to fit FirstLevelModel           │
│   - FOR-LOOP over colors/delays to extract HRF          │
│   - Compute universal HRF                               │
│   - Find optimal delay                                  │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│ Lines 543-684: Extract Z-scores (FOR-LOOPS, Direct!)    │
│   - FOR-LOOP over runs                                  │
│   - FOR-LOOP over colors                                │
│   - Extract z-scores at optimal delay                   │
│   - [voxelSelect version only: Lines 625-684 selection] │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│ Lines 685-762: Visualization - HRF & Z-maps (Direct!)   │
│   - Plot universal HRF                                  │
│   - Plot z-score matrices                               │
│   - Plot voxel preferences                              │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│ Lines 763-1202: PCA (FOR-LOOP, Direct code!)            │
│   - FOR-LOOP over leave-one-run-out folds               │
│   - Fit PCA on training data                            │
│   - Transform test data                                 │
│   - Plot PCA components and color space                 │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│ Lines 1203-1318: Classification (FOR-LOOP, Direct!)     │
│   - FOR-LOOP over leave-one-run-out folds               │
│   - Train diagonal LDA                                  │
│   - Predict test run                                    │
│   - Compute accuracy and confusion matrix               │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│ Lines 1319-1465: Reconstruction (FOR-LOOPS, Direct!)    │
│   - FOR-LOOP over leave-one-run-out folds               │
│   - FOR-LOOP over leave-one-color-out inner folds       │
│   - Train forward encoding model (OLS)                  │
│   - Predict held-out color                              │
│   - Compute reconstruction error                        │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│ Lines 1466-1556: Novel Colors (FOR-LOOPS, Direct!)      │
│   - FOR-LOOP over leave-one-run-out folds               │
│   - FOR-LOOP over 8 novel colors                        │
│   - Predict novel color from trained model              │
│   - Compute novel color error                           │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│ Lines 1557-1789: Visualization - Results (Direct!)      │
│   - Plot reconstruction per-run                         │
│   - Plot circular color space                           │
│   - Plot confusion matrix                               │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│ Lines 1790-1814: Print summary and cleanup (Direct!)    │
│   - Print final results                                 │
│   - Close dual logger                                   │
│   - Restore stdout/stderr                               │
└──────────────────────────────────────────────────────────┘
```

---

#### 5.1.2 Actual Main Execution (Lines 268-400)

**⭐ THIS IS THE ACTUAL CODE - NOT AN INVENTED FUNCTION**

```python
# ============================================================================
# Lines 268-283: parse_args() function (ONLY FUNCTION FOR MAIN FLOW)
# ============================================================================
def parse_args():
    parser = argparse.ArgumentParser(description='FIR-based color reconstruction (Z-score version)')
    parser.add_argument('--subject', type=str, default='P01',
                        help='Subject ID (P01 for pilot, 02-04 for test subjects)')
    parser.add_argument('--roi', type=str, default='V2',
                        help='ROI name (e.g., V1, V2, V3, V4, hV4)')
    parser.add_argument('--use-pca', action='store_true',
                        help='Use PCA dimensionality reduction')
    parser.add_argument('--n-components', type=int, default=20,
                        help='Number of PCA components (only if --use-pca)')
    parser.add_argument('--save-zmaps', action='store_true',
                        help='Save z-maps for each color')
    parser.add_argument('--timestamp', type=str, default=None,
                        help='Timestamp for output directory')
    return parser.parse_args()

# ============================================================================
# Lines 285-293: MAIN EXECUTION STARTS HERE (Direct code, NO function!)
# ============================================================================
args = parse_args()  # ⭐ This is where execution begins!

SUBJECT_ID = args.subject
ROI_NAME = args.roi
USE_PCA = args.use_pca
N_PCA_COMPONENTS = args.n_components
SAVE_ZMAPS = args.save_zmaps
TIMESTAMP_ARG = args.timestamp

# ============================================================================
# Lines 294-313: Path Configuration (Pilot vs Test)
# ============================================================================
FMRIPREP_BASE = "/storage/connectome/haba6030/fmriprep_out"
EVENT_DIR = "/storage/connectome/haba6030/colorBlind_dataOct"

if SUBJECT_ID == 'P01':
    FMRIPREP_DIR = f"{FMRIPREP_BASE}/pilot/sub-01"
    FILE_PREFIX = "sub-01"
    DERIVATIVE_PREFIX = "sub-01"
    EVENT_DIR = f"{EVENT_DIR}/pilot/sub-01/func"
    LABEL2HUE_DEG = LABEL2HUE_DEG_PILOT  # Irregular spacing
else:
    FMRIPREP_DIR = f"{FMRIPREP_BASE}/sub-{SUBJECT_ID}"
    FILE_PREFIX = f"sub-{SUBJECT_ID}"
    DERIVATIVE_PREFIX = f"sub-{SUBJECT_ID}"
    EVENT_DIR = f"{EVENT_DIR}/sub-{SUBJECT_ID}/func"
    LABEL2HUE_DEG = LABEL2HUE_DEG_TEST  # Regular 45° spacing

# ============================================================================
# Lines 314-358: Setup Output Directory and Logging
# ============================================================================
from datetime import datetime

if TIMESTAMP_ARG:
    timestamp = TIMESTAMP_ARG
else:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

if SUBJECT_ID == 'P01':
    output_dir = Path(f"derivatives/{timestamp}/pilot/{DERIVATIVE_PREFIX}/fir_reconstruction_uni_hrf/zScore/{ROI_NAME}_universal_hrf")
else:
    output_dir = Path(f"derivatives/{timestamp}/{DERIVATIVE_PREFIX}/fir_reconstruction_uni_hrf/zScore/{ROI_NAME}_universal_hrf")
output_dir.mkdir(parents=True, exist_ok=True)

fig_dir = output_dir / "figures"
fig_dir.mkdir(exist_ok=True)

# Setup dual logging (both to file and stdout)
class DualLogger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, 'w', buffering=1)

    def write(self, message):
        self.terminal.write(message)
        self.terminal.flush()
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

    def close(self):
        self.log.close()

log_file = output_dir / "log.txt"
sys.stdout = DualLogger(log_file)
sys.stderr = sys.stdout

# ============================================================================
# Lines 375-400: Load ROI Mask (Direct code, NO function!)
# ============================================================================
if SUBJECT_ID == 'P01':
    roi_path = f"derivatives/pilot/{DERIVATIVE_PREFIX}/roi_pipeline_20251111_010954/{ROI_NAME}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"
else:
    roi_path = f"derivatives/{DERIVATIVE_PREFIX}/roi_pipeline/{ROI_NAME}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"

if not os.path.exists(roi_path):
    print(f"ERROR: ROI mask not found: {roi_path}")
    sys.exit(1)

print(f"[1/8] Loading ROI mask: {ROI_NAME}")
print(f"  Path: {roi_path}")
sys.stdout.flush()

roi_img = nib.load(roi_path)
masker = NiftiMasker(mask_img=roi_path, standardize=False)
masker.fit()

n_voxels = np.sum(roi_img.get_fdata() > 0)
print(f"  Number of voxels: {n_voxels}")
print()
sys.stdout.flush()
```

---

#### 5.1.3 After Initialization: FOR-LOOP Pipeline

**All remaining steps (data loading, GLM, HRF, z-scores, PCA, classification, reconstruction) are implemented with FOR-LOOPS directly in the main code flow.**

**See Section 4.2 for detailed FOR-LOOP implementations:**
- **4.2.3:** Load data (lines 405-459)
- **4.2.4:** FIR GLM (lines 460-542)
- **4.2.5:** Z-score extraction (lines 543-614)
- **4.2.6:** PCA (lines 763-1202)
- **4.2.7:** Classification (lines 1203-1318)
- **4.2.8:** Reconstruction (lines 1319-1465)
- **4.2.9:** Novel colors (lines 1466-1556)
- **4.2.10:** Visualization (lines 685-762, 1557-1789)

---

#### 5.1.4 Command-Line Usage

**Basic usage:**
```bash
python fir_reconstruction_zScore.py --subject 01 --roi V2
```

**With PCA:**
```bash
python fir_reconstruction_zScore.py --subject 01 --roi V2 --use-pca --n-components 6
```

**Pilot subject:**
```bash
python fir_reconstruction_zScore.py --subject P01 --roi V2 --use-pca --n-components 6
```

**With custom timestamp (for matching with other analyses):**
```bash
python fir_reconstruction_zScore.py --subject 01 --roi V2 --timestamp 20251117_021334
```

**Save z-maps for visualization:**
```bash
python fir_reconstruction_zScore.py --subject 01 --roi V2 --save-zmaps
```

---

#### 5.1.5 Key Design Decisions

**1. Why no `main()` function?**
- Sequential execution is clearer for linear pipeline
- Easier debugging with direct code flow
- Variables accessible throughout for inspection

**2. Why use `parse_args()` function?**
- Only part that needs function encapsulation
- Separates argument parsing from execution
- Allows for easy testing of argument parsing

**3. Why use FOR-LOOPS instead of helper functions?**
- More transparent for neuroscience pipeline
- Easier to modify individual steps
- Clear data flow between stages
- Better for debugging intermediate results

**4. Why dual logging?**
- Capture all output to log file
- Still show real-time progress in terminal
- Critical for SLURM batch jobs on cluster

---

#### 5.1.6 File Organization Summary

```
fir_reconstruction_zScore.py (1,814 lines)
│
├── Lines 1-40:    Imports and docstring
├── Lines 41-114:  Configuration constants
├── Lines 115-267: Helper functions (8 functions that DO exist)
├── Lines 268-283: parse_args() function
│
├── Lines 285:     ⭐ MAIN EXECUTION STARTS (args = parse_args())
├── Lines 286-373: Setup (paths, logging, output directory)
├── Lines 375-400: Load ROI mask
├── Lines 405-459: Load data (FOR-LOOP)
├── Lines 460-542: FIR GLM (FOR-LOOPS)
├── Lines 543-614: Z-score extraction (FOR-LOOPS)
├── Lines 685-762: Visualize HRF and z-maps
├── Lines 763-1202: PCA (FOR-LOOP)
├── Lines 1203-1318: Classification (FOR-LOOP)
├── Lines 1319-1465: Reconstruction (FOR-LOOPS)
├── Lines 1466-1556: Novel colors (FOR-LOOPS)
├── Lines 1557-1789: Visualize results
└── Lines 1790-1814: Print summary and cleanup
```

**Total: 1,814 lines of direct execution code (NO main function!)**

---

### Summary: Main Execution Structure

**What does NOT exist:**
- ❌ `main()` function
- ❌ `if __name__ == "__main__":` block
- ❌ Helper functions like `load_data()`, `fit_fir_glm()`, `extract_zscores_at_delay()`
- ❌ Any function-based pipeline structure

**What DOES exist:**
- ✅ `parse_args()` function (lines 268-283) - ONLY function for main flow
- ✅ 8 utility helper functions (lines 115-267) - for calculations, not pipeline steps
- ✅ Direct sequential execution starting at line 285
- ✅ FOR-LOOPS for all main pipeline steps
- ✅ `DualLogger` class for logging (lines 338-354)

**Key Point:** The entire pipeline runs as **direct sequential code** from line 285 to line 1814, with all major steps implemented using **FOR-LOOPS**, NOT separate functions.
