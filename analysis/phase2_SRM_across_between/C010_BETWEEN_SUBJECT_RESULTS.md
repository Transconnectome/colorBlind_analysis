# C010 Between-Subject SRM Results

**Date:** 2026-02-09
**Analysis:** HC vs CVD comparison using C010+Procrustes data
**Status:** Template (fill in after analysis completion)

---

## Executive Summary

**Research Question 1:** Are HC and CVD groups significantly different in color representation?
**Research Question 2:** Does Procrustes-averaged SRM outperform Raw-averaged SRM?

**Key Findings:**
- [To be filled after analysis]
- Winner method: [Raw SRM / Procrustes SRM / Mixed results]
- Strongest ROI for group differences: [V1/V2/V3/V4]

---

## Data Quality

### Input Data (C010+Procrustes)
- **Preprocessing:** C010 (2nd-level drift removal) + Procrustes alignment
- **RDM Reliability:** 0.496 ± 0.227 (validated)
- **Noise Ceiling:** 0.623 ± 0.253
- **Ceiling Utilization:** 83.7% (Excellent)
- **Subjects:** HC (n=7), CVD (n=3)

### Comparison to Previous Work
| Metric | Baseline32 | C010+Procrustes | Improvement |
|--------|-----------|-----------------|-------------|
| RDM Reliability | 0.042 ± 0.103 | 0.496 ± 0.227 | +1082% |
| Noise Ceiling | 0.298 ± 0.126 | 0.623 ± 0.253 | +109% |
| Ceiling Utilization | 41% | 83.7% | +42.7pp |

**Interpretation:** C010 data provides substantially higher quality input for SRM analysis.

---

## Results by ROI

### V1 (Primary Visual Cortex)

**SRM Configuration:** k=4 features

#### Raw-Averaged SRM
- **HC-to-HC disparity:** [mean ± std]
- **CVD-to-HC disparity:** [mean ± std]
- **HC-CVD separation:** [value]
- **Statistical test:** t=[value], p=[value], Cohen's d=[value]
- **Significant:** [Yes/No]

#### Procrustes-Averaged SRM
- **HC-to-HC disparity:** [mean ± std]
- **CVD-to-HC disparity:** [mean ± std]
- **HC-CVD separation:** [value]
- **Statistical test:** t=[value], p=[value], Cohen's d=[value]
- **Significant:** [Yes/No]

#### Comparison
- **Improvement:** [±X.XX%]
- **Winner:** [Raw / Procrustes]
- **Interpretation:** [V1 shows/does not show improvement with Procrustes averaging]

---

### V2 (Secondary Visual Cortex)

**SRM Configuration:** k=4 features

#### Raw-Averaged SRM
- **HC-to-HC disparity:** [mean ± std]
- **CVD-to-HC disparity:** [mean ± std]
- **HC-CVD separation:** [value]
- **Statistical test:** t=[value], p=[value], Cohen's d=[value]
- **Significant:** [Yes/No]

#### Procrustes-Averaged SRM
- **HC-to-HC disparity:** [mean ± std]
- **CVD-to-HC disparity:** [mean ± std]
- **HC-CVD separation:** [value]
- **Statistical test:** t=[value], p=[value], Cohen's d=[value]
- **Significant:** [Yes/No]

#### Comparison
- **Improvement:** [±X.XX%]
- **Winner:** [Raw / Procrustes]
- **Interpretation:** [Expected: V2 should show strong HC-CVD difference with high effect size]

---

### V3 (Mid-Level Visual Area)

**SRM Configuration:** k=3 features

#### Raw-Averaged SRM
- **HC-to-HC disparity:** [mean ± std]
- **CVD-to-HC disparity:** [mean ± std]
- **HC-CVD separation:** [value]
- **Statistical test:** t=[value], p=[value], Cohen's d=[value]
- **Significant:** [Yes/No]

#### Procrustes-Averaged SRM
- **HC-to-HC disparity:** [mean ± std]
- **CVD-to-HC disparity:** [mean ± std]
- **HC-CVD separation:** [value]
- **Statistical test:** t=[value], p=[value], Cohen's d=[value]
- **Significant:** [Yes/No]

#### Comparison
- **Improvement:** [±X.XX%]
- **Winner:** [Raw / Procrustes]
- **Interpretation:** [Expected: V3 should show moderate-strong HC-CVD difference]

---

### V4 (Color-Selective Area)

**SRM Configuration:** k=4 features

#### Raw-Averaged SRM
- **HC-to-HC disparity:** [mean ± std]
- **CVD-to-HC disparity:** [mean ± std]
- **HC-CVD separation:** [value]
- **Statistical test:** t=[value], p=[value], Cohen's d=[value]
- **Significant:** [Yes/No]

#### Procrustes-Averaged SRM
- **HC-to-HC disparity:** [mean ± std]
- **CVD-to-HC disparity:** [mean ± std]
- **HC-CVD separation:** [value]
- **Statistical test:** t=[value], p=[value], Cohen's d=[value]
- **Significant:** [Yes/No]

#### Comparison
- **Improvement:** [±X.XX%]
- **Winner:** [Raw / Procrustes]
- **Interpretation:** [V4 as color-selective area should show differences]

---

## Cross-ROI Summary

### Method Comparison (Raw vs Procrustes SRM)

| ROI | Raw HC-CVD Sep | Proc HC-CVD Sep | Improvement | Winner |
|-----|----------------|-----------------|-------------|--------|
| V1  | [value]        | [value]         | [±X.XX%]    | [R/P]  |
| V2  | [value]        | [value]         | [±X.XX%]    | [R/P]  |
| V3  | [value]        | [value]         | [±X.XX%]    | [R/P]  |
| V4  | [value]        | [value]         | [±X.XX%]    | [R/P]  |

**Overall Winner:** [Raw SRM / Procrustes SRM / Mixed]
**Average Improvement:** [±X.XX%]

### Statistical Significance

| ROI | Raw p-value | Proc p-value | Raw d | Proc d | Significant in Both? |
|-----|-------------|--------------|-------|--------|---------------------|
| V1  | [value]     | [value]      | [val] | [val]  | [Yes/No]           |
| V2  | [value]     | [value]      | [val] | [val]  | [Yes/No]           |
| V3  | [value]     | [value]      | [val] | [val]  | [Yes/No]           |
| V4  | [value]     | [value]      | [val] | [val]  | [Yes/No]           |

---

## Interpretation

### Research Question 1: HC vs CVD Differences

**Finding:** [Summary of whether HC-CVD differences were detected]

**Supporting Evidence:**
- ROIs with significant differences: [list]
- Effect sizes (Cohen's d): [range]
- Consistency with previous work: [comparison to Baseline32 SRM results]

**Biological Interpretation:**
- [How do color representations differ between HC and CVD?]
- [Which visual areas show strongest effects?]
- [Does this match expectations from V2/V3 being color-processing regions?]

### Research Question 2: Raw vs Procrustes SRM

**Finding:** [Which averaging method yielded better HC-CVD separation?]

**Supporting Evidence:**
- ROIs where Procrustes won: [list]
- ROIs where Raw won: [list]
- Average improvement: [value]

**Methodological Interpretation:**
- **Hypothesis confirmed/rejected:** [Procrustes-averaged data should improve SRM due to higher RDM reliability (0.496 vs 0.042)]
- **Mechanism:** [Why did/didn't Procrustes help? Better geometric alignment → cleaner shared response?]
- **Recommendation:** [Should future analyses use Procrustes averaging?]

### Comparison to Previous SRM Work

**Baseline32 SRM (previous analysis):**
- V2 Cohen's d: [previous value]
- V3 Cohen's d: [previous value]

**C010+Procrustes SRM (current analysis):**
- V2 Cohen's d: [current value] ([improvement/decline])
- V3 Cohen's d: [current value] ([improvement/decline])

**Interpretation:**
- [Did higher quality data (C010) lead to stronger/weaker group differences?]
- [Possible reasons for changes: better SNR, better alignment, more subjects, etc.]

---

## Clinical Implications

### Color Blindness Detection
- [Can fMRI-based color representation differences be used to identify CVD?]
- [Which ROIs are most diagnostic?]
- [How large are effect sizes (clinically meaningful)?]

### Individual Variability
- **HC-to-HC disparity:** [How consistent are HC subjects?]
- **CVD-to-CVD disparity:** [How consistent are CVD subjects?]
- [Implications for individual-level classification]

---

## Limitations

1. **Small CVD sample:** n=3 CVD subjects limits statistical power
2. **CVD-to-CVD disparity:** Limited pairs (n=3) for internal consistency
3. **SRM features (k):** Fixed k values (3-4) may not be optimal for all subjects
4. **HC subject exclusion:** sub-07 excluded (poor tSNR) in previous work - was it included here?
5. **Run averaging:** Beta-based SRM (averaged runs) loses temporal information

---

## Recommendations

### For Current Analysis
- [ ] Verify all 4 ROIs completed successfully
- [ ] Check for outliers in disparity distributions
- [ ] Validate that Procrustes improvement is consistent across subjects
- [ ] Generate and review all visualizations

### For Future Work
- [ ] Recruit more CVD subjects (n=3 is underpowered)
- [ ] Test time-series SRM (use all runs, not averages)
- [ ] Hyperparameter tuning for k (currently fixed per ROI)
- [ ] Cross-validation to assess stability
- [ ] Apply to color decoding (predict color from aligned space)

---

## Figures

### Key Visualizations (to be generated)

1. **Figure 1:** Dual pipeline comparison (Raw vs Procrustes SRM per ROI)
   - Location: `visualizations/{ROI}_dual_disparity_comparison.png`
   - Shows side-by-side HC-CVD disparities

2. **Figure 2:** 3-group comparison (HC-HC, CVD-HC, CVD-CVD)
   - Location: `visualizations/{ROI}_hc_cvd_boxplot.png`
   - Shows internal consistency within groups

3. **Figure 3:** Summary comparison across ROIs
   - Location: `visualizations/summary_raw_vs_procrustes.png`
   - Bar plot comparing raw vs procrustes methods

4. **Figure 4:** HC-CVD separation with significance
   - Location: `visualizations/summary_hc_cvd_separation.png`
   - Statistical significance markers and effect sizes

---

## Conclusions

**Main Finding 1 (HC vs CVD):**
- [Summary of group differences]

**Main Finding 2 (Method Comparison):**
- [Summary of Raw vs Procrustes SRM]

**Recommendations:**
- [Use Procrustes averaging? / Stick with raw averaging?]
- [Which ROIs to focus on for future analyses?]
- [Are HC-CVD differences robust enough for downstream applications?]

---

## Data Availability

**Results location:**
- Local: `analysis/validation/SRM/results/c010/TIMESTAMP/`
- Server: `/scratch/connectome/haba6030/colorBlind/derivatives/srm_c010_between_subject/TIMESTAMP/`

**Files:**
- JSON results: `{ROI}_{raw|procrustes}_srm_results.json`
- Comparisons: `{ROI}_dual_comparison.json`
- Visualizations: `visualizations/*.png`

---

**Document Status:** Template - To be completed after analysis
**Last Updated:** 2026-02-09
