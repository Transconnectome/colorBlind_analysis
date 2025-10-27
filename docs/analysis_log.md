# ColorBlind Analysis Progress Log

## Execution & Action Rules (MANDATORY)

All interactive runs and batch analyses for this repository MUST be executed on the project server and conda environment below. This is an operational requirement to guarantee reproducibility, correct filesystem paths, and access to pre-configured resources.

- Server: node2 (haba6030@node2)
- Conda environment: nilearn
- Activation command: `conda activate nilearn`

Before running any analysis script or notebook, verify the environment with:

```bash
hostname   # should show node2
echo $CONDA_DEFAULT_ENV   # should show 'nilearn'
which python   # should point to the conda env python
```

If any of these checks fail, stop and start a session on node2 and activate `nilearn` before proceeding.

---

## 2025-10-24

### Progress Timeline

#### 09:00 AM - Initial GLM Implementation
- Implemented FIR GLM based on B&H (2009)
- Set up basic pipeline structure in Python
- Verified GLM outputs against paper specifications

#### 11:00 AM - ROI Processing
- Added Wang atlas-based ROI extraction
- Implemented mask resampling to match functional resolution
- Fixed dimension mismatch issues (182x218x182 → 97x115x97)

#### 02:00 PM - Beta Map Extraction
- Modified ROI extraction to handle 4D beta maps
- Added shape validation for extracted responses
- Implemented color response matrix generation

### Technical Details

#### GLM Implementation
```python
# Key parameters
TR = 2.0  # seconds
n_scans = 288
hrf_model = 'glover'
```

#### ROI Processing
- Source dimensions: 182x218x182 (Wang atlas)
- Target dimensions: 97x115x97 (functional)
- Method: nilearn.image.resample_img

#### Beta Extraction
- Input: 4D beta maps (8 colors × 97×115×97 voxels)
- Output: 2D matrices (8 colors × n_voxels) per ROI
- ROIs: V1, V2, V3, hV4

### Current Status
- [x] GLM implementation complete
- [x] ROI resampling working
- [x] Beta extraction implemented
- [ ] Forward modeling pending
- [ ] Classification testing pending

### Next Steps
1. Implement forward modeling
2. Add cross-validation
3. Set up classification testing
4. Add visualization tools

### Issues & Solutions
1. Dimension mismatch
   - Issue: ROI masks at different resolution than functional data
   - Solution: Added explicit resampling step
   
2. Empty ROI masks
   - Issue: Some ROIs had no voxels after resampling
   - Solution: Added validation checks and warning messages

3. Beta map reshaping
   - Issue: Incorrect dimensionality in color response matrices
   - Solution: Implemented proper reshaping (colors × voxels)

## Previous Entries
(To be filled with past analysis steps)