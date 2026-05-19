# Processing Packages Used in Study

## From Abstract Methods Section

> "Preprocessing was performed using fMRIPrep, including field map-based distortion correction, motion correction, slice-timing correction, and spatial normalization to MNI space"

## Detailed Breakdown

### Primary Preprocessing: fMRIPrep
**fMRIPrep** (not in OHBM list, but uses multiple packages internally)
- Version: Likely v20.2.0 (from CLAUDE.md)
- Uses **FreeSurfer** for anatomical processing
- Uses **FSL** tools for functional processing
- Uses **AFNI** for some preprocessing steps

### Analysis Packages

1. **Python Libraries (not in list)**
   - **nilearn**: fMRI analysis, GLM, decoding
   - **scikit-learn**: Feature selection (ANOVA), classification (LDA), cross-validation
   - **nibabel**: NIfTI file handling
   - **numpy/pandas**: Data processing
   - **scipy**: Statistical functions

2. **Atlas**
   - Wang et al. (2015) probabilistic atlas
   - Likely converted/processed with AFNI or FSL tools

---

## OHBM List Options

From the provided list:
- ✅ **AFNI** - Potentially used via fMRIPrep
- ❌ Analyze - Not used
- ❌ Brain Voyager - Not used
- ✅ **Free Surfer** - Used by fMRIPrep for anatomical processing
- ✅ **FSL** - Used by fMRIPrep for functional processing
- ❌ LONI Pipeline - Not used
- ❌ SPM - Not used
- ✅ **Other** - Need to specify: fMRIPrep, nilearn, scikit-learn

---

## Recommended Selections (Check all that apply)

### Option A: Be Comprehensive
1. ✅ **Free Surfer** (via fMRIPrep)
2. ✅ **FSL** (via fMRIPrep)
3. ✅ **AFNI** (potentially via fMRIPrep)
4. ✅ **Other**: "fMRIPrep (primary preprocessing); Python: nilearn, scikit-learn"

**Pros**: Most accurate and complete
**Cons**: Many selections

### Option B: Primary Tools Only
1. ✅ **Free Surfer** (fMRIPrep dependency)
2. ✅ **FSL** (fMRIPrep dependency)
3. ✅ **Other**: "fMRIPrep (preprocessing); nilearn, scikit-learn (analysis)"

**Pros**: Clearer distinction between preprocessing and analysis
**Cons**: Omits AFNI

### Option C: Minimal (What users directly interacted with)
1. ✅ **Other**: "fMRIPrep (preprocessing); Python packages: nilearn, scikit-learn, nibabel (analysis)"

**Pros**: Most honest about what was directly used
**Cons**: Doesn't acknowledge underlying tools (FreeSurfer, FSL)

---

## Recommendation: Option B (Primary Tools)

### Selections:
1. ✅ **Free Surfer**
2. ✅ **FSL**
3. ✅ **Other**

### "Other" Explanation:
"fMRIPrep v20.2.0 (preprocessing); Python: nilearn (GLM, decoding), scikit-learn (feature selection, classification)"

**Rationale:**
- **FreeSurfer & FSL**: Core components of fMRIPrep, essential for understanding preprocessing
- **fMRIPrep**: Primary preprocessing tool, should be mentioned
- **nilearn & scikit-learn**: Essential for analysis pipeline (GLM, forward encoding, ANOVA, LDA)
- Clear separation: preprocessing (fMRIPrep/FreeSurfer/FSL) vs analysis (Python)
- Transparent and comprehensive

---

## Alternative "Other" Text Options

### Short version:
"fMRIPrep; nilearn; scikit-learn"

### Medium version (recommended):
"fMRIPrep v20.2.0 (preprocessing); Python: nilearn (GLM, decoding), scikit-learn (feature selection, classification)"

### Long version:
"fMRIPrep v20.2.0 for preprocessing (utilizes FreeSurfer and FSL); Python packages for analysis: nilearn (GLM estimation, decoding), scikit-learn (ANOVA feature selection, LDA classification), nibabel (NIfTI I/O)"

---

## Important Note

**fMRIPrep Architecture:**
```
fMRIPrep (wrapper)
├── FreeSurfer (anatomical)
├── FSL (functional)
└── AFNI (some steps)
```

Since fMRIPrep is a comprehensive wrapper that uses FreeSurfer and FSL as dependencies, it's appropriate to:
1. Check FreeSurfer ✓
2. Check FSL ✓
3. Mention fMRIPrep in "Other" ✓

This gives reviewers complete picture of preprocessing pipeline while highlighting the high-level tool (fMRIPrep) that orchestrated everything.
