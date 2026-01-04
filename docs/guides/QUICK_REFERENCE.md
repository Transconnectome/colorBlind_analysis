# 🎯 Quick Reference Card - QC Analysis

**Current Status**: Awaiting new fMRIPrep results
**Expected**: 2-3 hours from job submission
**Date**: 2026-01-03

---

## 📋 Current State (deoblique_v2)

```
✗ Dice: 0.376 (target: 0.85+)
✗ Pass rate: 0.0%
✗ ROI_ZERO: 45.4%
✗ COREG_POOR: 54.6%
```

---

## 🚀 When New Results Ready

### 1. Check Job Completed
```bash
ssh haba6030@node2
squeue -u haba6030  # Should be empty
tail logs/fmriprep_original_*.err  # Check for errors
```

### 2. Run QC
```bash
cd /scratch/connectome/haba6030/colorBlind
mkdir -p derivatives/QC_original_v3
for SUB in 01 02 03 04 05 06 07 08 09 10; do
    bash qc_runwise_improved.sh $SUB
done
```

### 3. Download Results
```bash
# On local
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis
mkdir -p derivatives/QC_new
scp "haba6030@node2:/scratch/.../derivatives/QC_original_v3/qc_runwise_sub-*.tsv" derivatives/QC_new/
```

### 4. Compare
```bash
python3 compare_fmriprep_versions.py "preps/qc_runwise_sub-*.tsv" "derivatives/QC_new/qc_runwise_sub-*.tsv"
```

---

## 🎯 Decision Tree

### Dice >= 0.85
```
✅ SOLVED!
→ Update CLAUDE.md with new fMRIPrep path
→ Start baseline analysis
```

### Dice 0.70-0.84
```
⚠️ PARTIAL
→ Analyze which subjects/runs fail
→ python visualize_qc.py derivatives/QC_new/qc_classified.tsv
→ Consider excluding bad runs
```

### Dice < 0.70
```
❌ INSUFFICIENT
→ Run transform diagnostic:
  bash check_transform_chain.sh 09 1  # Sub-09 = 100% ROI_ZERO
→ Visual inspection:
  ssh -X haba6030@node2
  fsleyes (check T1/BOLD alignment)
→ Check T1 mask ratio:
  python3 -c "import pandas as pd; df=pd.read_csv('derivatives/QC_new/qc_classified.tsv', sep='\t'); print(df.groupby('sub')['t1mask_vox','bmask_vox'].mean())"
```

---

## 📊 Key Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `compare_fmriprep_versions.py` | Before/after comparison | When new QC ready |
| `visualize_qc.py` | 9-panel diagnostic plot | For visual patterns |
| `check_transform_chain.sh` | Transform bug detection | If ROI_ZERO persists |
| `WHEN_NEW_FMRIPREP_READY.md` | Detailed step-by-step | Full procedure |
| `NEXT_ACTIONS.md` | Action plan with timeline | Strategic planning |
| `QC_CATASTROPHE_SUMMARY.md` | Current state analysis | Background context |

---

## 🔍 Critical Hypotheses to Test

### H1: fMRIPrep Complexity (60% prior)
- **Test**: Compare old (DOF 9, FreeSurfer) vs new (DOF 6, no FS)
- **Evidence if true**: New Dice >= 0.70
- **Action**: Use new settings

### H2: T1 Mask Over-extraction (30% prior)
- **Test**: Check Sub-05, 07 (high overlap, low Dice)
- **Evidence if true**: T1 mask covers >2× BOLD mask area
- **Action**: Custom brain masks or `--skull-strip-t1w skip`

### H3: Transform Inversion Bug (10% prior)
- **Test**: Run `check_transform_chain.sh 09 1`
- **Evidence if true**: TEST B produces voxels, TEST A produces 0
- **Action**: Fix `antsApplyTransforms` inversion flag

---

## 📈 Success Criteria

| Metric | Current | Target | Accept Threshold |
|--------|---------|--------|-----------------|
| Mean Dice | 0.376 | 0.90 | 0.80 |
| Pass rate | 0.0% | 100% | 80% |
| ROI_ZERO | 45.4% | 0% | <10% |

**Minimum acceptable**: 80% of runs with Dice >= 0.80

---

## ⚠️ Red Flags

If new results show:
- ❌ Sub-04 still NaN → Acquisition issue, permanent exclusion
- ❌ Sub-09/10 still 100% ROI_ZERO → Transform bug not fixed by settings
- ❌ All subjects Dice < 0.50 → Fundamental data/pipeline mismatch

---

## 💡 One-Liners

```bash
# Quick Dice check
grep -h "^" derivatives/QC_new/qc_*.tsv | awk -F'\t' 'NR>1{sum+=$7; n++} END{print sum/n}'

# Count passes
grep -h "^" derivatives/QC_new/qc_*.tsv | awk -F'\t' '$7>=0.80{n++} END{print n"/240"}'

# Find worst subject
grep -h "^" derivatives/QC_new/qc_*.tsv | awk -F'\t' 'NR>1{dice[$1]+=$7; n[$1]++} END{for(s in dice) print s, dice[s]/n[s]}' | sort -k2n | head -1

# ROI_ZERO subjects
grep -h "^" derivatives/QC_new/qc_*.tsv | awk -F'\t' '$10==0 {subs[$1]++} END{for(s in subs) if(subs[s]==24) print "Sub-"s": 100% ROI_ZERO"}'
```

---

**Next Check-in**: When fMRIPrep job completes (monitor with `squeue -u haba6030`)
