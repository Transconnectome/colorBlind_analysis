# MNI Registration Chain Diagnosis Report

**Subject:** sub-XX
**Run:** X
**Date:** YYYY-MM-DD
**Analyst:** [Name]

---

## 1. Executive Summary

**Overall Status:** ✅ PASS / ⚠️ PARTIAL / ❌ FAIL

**Primary Issue Identified:**
- [ ] T1w → MNI transformation
- [ ] BOLD → MNI transformation
- [ ] Grid/Affine consistency
- [ ] None (chain is normal)

**Recommended Action:**
[Brief recommendation]

---

## 2. Numerical Validation Results

### 2.1 Image Metadata

| Property | MNI Template | T1w(MNI) | BOLD(MNI) |
|----------|--------------|----------|-----------|
| Shape | (91, 109, 91) | | |
| Voxel Size | 2.0 × 2.0 × 2.0 mm | | |
| Data Type | float32 | | |

### 2.2 Spatial Comparison

#### T1w(MNI) vs Template

```
Affine match:      ✅ YES / ❌ NO
Shape match:       ✅ YES / ❌ NO
Voxel size match:  ✅ YES / ❌ NO

Max affine diff:   [value]
Mean affine diff:  [value]
```

#### BOLD(MNI) vs Template

```
Affine match:      ✅ YES / ❌ NO
Shape match:       ✅ YES / ❌ NO
Voxel size match:  ✅ YES / ❌ NO

Max affine diff:   [value]
Mean affine diff:  [value]
```

#### BOLD(MNI) vs T1w(MNI)

```
Affine match:      ✅ YES / ❌ NO
Shape match:       ✅ YES / ❌ NO
Voxel size match:  ✅ YES / ❌ NO

Max affine diff:   [value]
Mean affine diff:  [value]
```

---

## 3. Visual Inspection Results

### 3.1 Step A: T1w(MNI) ↔ MNI Template

**Command:**
```bash
fsleyes [template] [t1w_mni] -cm red -a 50
```

**Checklist:**
- [ ] Midline aligned
- [ ] Ventricles correctly positioned
- [ ] Occipital/cerebellar boundary correct
- [ ] Overall brain shape matches

**Notes:**
[Observations, screenshots, issues noted]

**Rating:** ✅ Excellent / ⚠️ Acceptable / ❌ Poor

---

### 3.2 Step B: BOLD(MNI) ↔ MNI Template

**Command:**
```bash
fsleyes [template] [bold_mni] -cm blue -a 50
```

**Checklist:**
- [ ] Overall brain position correct
- [ ] Occipital cortex properly aligned
- [ ] No severe distortion artifacts
- [ ] Coverage adequate for ROIs

**Notes:**
[Observations, screenshots, issues noted]

**Rating:** ✅ Excellent / ⚠️ Acceptable / ❌ Poor

---

### 3.3 Step C: BOLD(MNI) ↔ T1w(MNI)

**Command:**
```bash
fsleyes [t1w_mni] [bold_mni] -cm red -a 50
```

**Checklist:**
- [ ] Gray-white matter boundaries align
- [ ] No visible offset between images
- [ ] Resolution difference acceptable
- [ ] Mutual registration quality good

**Notes:**
[Observations, screenshots, issues noted]

**Rating:** ✅ Excellent / ⚠️ Acceptable / ❌ Poor

---

## 4. Diagnosis Interpretation

### 4.1 Decision Matrix

| T1w(MNI) | BOLD(MNI) | Mutual | Diagnosis |
|----------|-----------|--------|-----------|
| [✅/❌] | [✅/❌] | [✅/❌] | [See interpretation below] |

### 4.2 Identified Issues

**Primary Cause:**
[Based on decision matrix - T1w warp / BOLD registration / Grid mismatch / None]

**Supporting Evidence:**
1. [Evidence point 1]
2. [Evidence point 2]
3. [Evidence point 3]

**Affected Components:**
- [ ] T1w skull-stripping
- [ ] T1w → MNI normalization
- [ ] BOLD → T1w registration (BBR)
- [ ] Susceptibility distortion correction (SDC)
- [ ] Resolution/grid specification
- [ ] Other: [specify]

---

## 5. Root Cause Analysis

### 5.1 fMRIPrep Configuration Review

**Version:** [fMRIPrep version]

**Key Parameters:**
```bash
--output-spaces: [MNI152NLin2009cAsym:res-2 / other]
--use-syn-sdc: [yes/no]
--force-bbr: [yes/no]
--skull-strip-t1w: [auto/skip/force]
--dummy-scans: [N]
```

**Potential Issues:**
- [ ] Incorrect output-spaces specification
- [ ] SDC not applied (missing B0FieldIdentifier)
- [ ] BBR failure (insufficient contrast)
- [ ] Poor T1w quality

### 5.2 Input Data Quality

**T1w Quality:**
- [ ] Adequate SNR
- [ ] Minimal motion
- [ ] Full brain coverage
- [ ] No obvious artifacts

**BOLD Quality:**
- [ ] Adequate SNR
- [ ] Acceptable motion (FD < 0.5mm typical)
- [ ] Full occipital coverage
- [ ] SDC applied successfully

**Issues Found:**
[List any input data quality issues]

---

## 6. Recommended Solutions

### Immediate Actions

1. **[Action 1]**
   - Command: `[specific command]`
   - Expected outcome: [description]

2. **[Action 2]**
   - Command: `[specific command]`
   - Expected outcome: [description]

### Long-term Improvements

- [ ] Re-run fMRIPrep with corrected parameters
- [ ] Apply manual registration corrections
- [ ] Exclude subject from group analysis
- [ ] Use alternative normalization strategy
- [ ] Other: [specify]

---

## 7. Verification Steps

After implementing solutions:

- [ ] Re-run `diagnose_mni_chain.py`
- [ ] Confirm numerical metrics improve
- [ ] Visual inspection shows improvement
- [ ] ROI extraction produces valid data
- [ ] Baseline analysis runs successfully

**Expected Metrics After Fix:**
```
T1w affine match:  Target = YES
BOLD affine match: Target = YES
Mutual match:      Target = YES
```

---

## 8. Appendices

### A. File Paths

```bash
T1w_MNI:  [full path]
BOLD_MNI: [full path]
Template: [full path]
```

### B. Script Output

```
[Paste full output from diagnose_mni_chain.py]
```

### C. Screenshots

Location: [path to screenshots directory]

- Step_A_T1w_vs_Template_[sagittal/coronal/axial].png
- Step_B_BOLD_vs_Template_[sagittal/coronal/axial].png
- Step_C_BOLD_vs_T1w_[sagittal/coronal/axial].png

### D. Related Documents

- Previous diagnosis: [ALIGNMENT_DIAGNOSTICS_FINAL_REPORT.md]
- fMRIPrep logs: [path]
- Processing notes: [path]

---

## 9. Sign-off

**Diagnosis Completed By:** [Name]
**Date:** [YYYY-MM-DD]
**Approved By:** [Advisor/PI]
**Date:** [YYYY-MM-DD]

**Follow-up Required:** ✅ YES / ❌ NO
**Follow-up Date:** [if applicable]

---

## Notes

[Any additional observations, concerns, or recommendations]
