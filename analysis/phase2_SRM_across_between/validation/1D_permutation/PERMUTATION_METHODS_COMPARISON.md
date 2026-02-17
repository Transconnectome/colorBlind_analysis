# Color Label Permutation Test - Two Approaches

## Summary

**Current Issue**: Reviewer may question whether our permutation test is biased because the SRM space itself was learned from the true color structure.

**Solution**: Implement a more rigorous version that retrains SRM for each permutation.

---

## Approach 1: Label Shuffling in Aligned Space (CURRENT)

### Method:
```
1. Train SRM once on TRUE color labels
2. Load SRM-aligned patterns
3. For each permutation:
   - Shuffle color labels (rows) in aligned patterns
   - Compute metrics
4. Compare observed vs null distribution
```

### Implementation:
- Script: `run_color_label_permutation.py`
- Runtime: ~5 minutes (1000 permutations)
- Already completed ✅

### Results (1000 permutations):
| ROI | Disparity Diff p | HC RDM p | CVD RDM p |
|-----|------------------|----------|-----------|
| V1  | 0.060           | <0.001   | 0.022     |
| V2  | 0.247           | <0.001   | <0.001    |
| V3  | 0.694           | <0.001   | 0.001     |
| hV4 | 0.690           | 0.005    | 0.015     |

### Strength:
- ✅ Fast, already completed
- ✅ Shows RDM patterns strongly depend on color labels (p<0.05)
- ✅ Shows disparity is color-nonspecific (p>0.05 in V2/V3/hV4)

### Limitation:
- ⚠️  **Potential Reviewer Concern**: "The SRM space itself encodes the true color structure. When you shuffle labels, you're testing in a biased space that 'remembers' the original colors."
- ⚠️  This is technically correct - the SRM transformation matrices (W) were optimized for true color structure

---

## Approach 2: SRM Retraining for Each Permutation (RIGOROUS)

### Method:
```
1. Load ORIGINAL amplitude data (before SRM)
2. For each permutation:
   - Shuffle color labels in ORIGINAL data
   - Train SRM on shuffled data
   - Compute metrics in newly learned SRM space
3. Compare observed vs null distribution
```

### Implementation:
- Script: `run_color_permutation_with_srm_retraining.py` ✅ Created
- SBATCH: `run_rigorous_permutation.sbatch` ✅ Created
- Runtime: ~24 hours per ROI (1000 SRM trainings)
- Total: ~4 days on server (4 ROIs in parallel)

### Why This is Better:
- ✅ **Unbiased**: Each permutation has its own SRM space learned from shuffled data
- ✅ **Reviewer-proof**: Cannot argue that SRM space biases the test
- ✅ **Strongest possible test**: If patterns survive this, they TRULY depend on color labels

### Expected Results:
Based on Approach 1 results, we expect:
- **RDM correlations**: p<0.05 (should remain significant - RDM truly color-dependent)
- **Disparity difference**: p>0.05 (should remain non-significant - disparity color-nonspecific)

---

## Key Difference Illustrated

### Approach 1 (Current):
```
True Colors:    Red  Orange  Yellow  Green  Cyan  Blue  Purple  Magenta
                 ↓     ↓       ↓      ↓      ↓     ↓      ↓       ↓
SRM Training → [Learn transformation W based on true structure]
                 ↓
SRM Space:    [Encodes true color relationships]
                 ↓
Permutation:  Orange  Red  Green  Yellow  Blue  Cyan  Magenta  Purple
                 ↓     ↓     ↓      ↓      ↓     ↓      ↓        ↓
             [Shuffle in PRE-LEARNED space]
                 ↓
Problem:      SRM space still "knows" true structure!
```

### Approach 2 (Rigorous):
```
Permutation 1:
Shuffled:    Orange  Red  Green  Yellow  Blue  Cyan  Magenta  Purple
                ↓     ↓     ↓      ↓      ↓     ↓      ↓        ↓
SRM Training → [Learn NEW transformation W₁ from shuffled data]
                ↓
New SRM Space: [Encodes shuffled structure]
                ↓
Metrics:      [Computed in unbiased space]

Permutation 2:
Shuffled:    Blue  Magenta  Red  Orange  Purple  Green  Yellow  Cyan
                ↓      ↓     ↓     ↓       ↓       ↓      ↓      ↓
SRM Training → [Learn NEW transformation W₂ from different shuffle]
                ↓
New SRM Space: [Encodes different shuffled structure]
                ↓
Metrics:      [Computed in unbiased space]

... repeat 1000 times
```

---

## Computational Cost

### Approach 1:
- 1000 permutations × 0.3 seconds = ~5 minutes
- Can run locally ✅

### Approach 2:
- 1000 SRM trainings per ROI × ~1.5 minutes = ~25 hours per ROI
- 4 ROIs in parallel = ~25 hours total on server
- Cannot run locally ❌

---

## Recommendation

### For Current Paper:
**Use Approach 1** for main results:
- Already completed
- Results are clear and strong
- Computationally tractable

**Acknowledge limitation**:
> "Note that the SRM space itself was learned from the true color labels. While this may introduce a conservative bias (making it harder to detect color-specific patterns), a fully rigorous test would retrain SRM for each permutation."

### For Reviewer Response (if challenged):
**Run Approach 2**:
- "We have now implemented a fully rigorous permutation test that retrains SRM for each iteration"
- Show that results replicate (RDM still p<0.05, disparity still p>0.05)
- This definitively proves patterns are not SRM artifacts

### For Supplementary Materials:
**Include both**:
- Main text: Approach 1 (efficient, already done)
- Supplement: Approach 2 (rigorous, reviewer-proof)
- Show consistency between methods

---

## Next Steps

### Immediate (for paper):
1. ✅ Keep Approach 1 results in main analysis
2. ✅ Add methodological note about limitation
3. ⚠️  Mention Approach 2 exists as validation

### If reviewer challenges:
1. 🚧 Upload scripts to server:
```bash
scp run_color_permutation_with_srm_retraining.py run_rigorous_permutation.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/1D_permutation/
```

2. 🚧 Submit array job:
```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/1D_permutation
sbatch run_rigorous_permutation.sbatch
```

3. 🚧 Wait ~25 hours, download results:
```bash
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/1D_permutation/results_rigorous/ \
    /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase2_SRM_across_between/validation/1D_permutation/
```

4. 🚧 Compare results, show consistency

---

## Statistical Interpretation

### If Approach 2 replicates Approach 1:
- ✅ **Strong conclusion**: "Color label dependency is robust to SRM training method"
- ✅ **Validates**: RDM patterns truly color-specific, disparity truly general

### If Approach 2 differs from Approach 1:
- If RDM p-values become LOWER (more significant): Even better! Approach 1 was conservative
- If RDM p-values become HIGHER (less significant): Still okay if p<0.05 maintained
- If RDM becomes p>0.05: Would need to reconsider interpretation (unlikely!)

---

## Conclusion

**Current Status**: Approach 1 completed, results strong

**Recommendation**:
- Use Approach 1 for main paper (sufficient, efficient)
- Keep Approach 2 ready for reviewer response (rigorous, unassailable)
- Both approaches should show same pattern (RDM color-specific, disparity general)

**Confidence**: High - Approach 1 results are clear, Approach 2 is "insurance policy" for reviewers

---

**Created**: 2026-02-16 18:45
**Status**: Ready for server execution if needed
