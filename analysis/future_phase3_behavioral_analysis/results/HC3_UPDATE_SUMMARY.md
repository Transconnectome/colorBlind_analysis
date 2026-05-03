# HC Group Metrics Update — JYPark (HC3) Included

**Date**: 2026-03-24
**Update**: Added HC3 (JYPark) to HC group statistics (N=3)

---

## Summary of Changes

### 1. HC Group Statistics (N=3)
All HC group metrics now computed from **HC1 + HC2 + HC3**:
- **HC Group Mean**: Average of all 3 HC subjects
- **HC Group SD**: Sample standard deviation (ddof=1)
- **HC Group SEM**: SD / √3

### 2. Direction Classification Changes
**3 pairs changed classification** when using HC Group Mean vs HC1:

| Pair | HC1 Direction | HC Group Direction | Reason |
|------|---------------|-------------------|---------|
| **green-blue** | HYPER | **borderline** | Ratio 1.03 (near unity) |
| **blue-purple** | HYPER | **HYPO** | Ratio 1.17 (>1.15 threshold) |
| **cyan-magenta** | HYPER | **HYPO** | Ratio 1.29 (>1.15 threshold) |

### 3. HC Group Mean Values

| Pair | HC1 | HC2 | HC3 | **HC Mean** | **HC SD** | CVD | **Ratio** | **Direction** |
|------|-----|-----|-----|-------------|-----------|-----|-----------|---------------|
| red-orange | 0.235 | 0.018 | 0.057 | **0.103** | 0.116 | 0.062 | **0.60** | **HYPER** |
| orange-yellow | 0.443 | 0.064 | 0.167 | **0.225** | 0.196 | 0.840 | **3.74** | **HYPO** |
| yellow-green | 0.103 | 0.018 | 0.054 | **0.058** | 0.043 | 0.278 | **4.76** | **HYPO** |
| green-blue | 0.103 | 0.020 | 0.102 | **0.075** | 0.048 | 0.077 | **1.03** | **borderline** |
| yellow-purple | 0.025 | 0.015 | 0.018 | **0.019** | 0.005 | 0.062 | **3.23** | **HYPO** |
| blue-purple | 0.165 | 0.040 | 0.103 | **0.103** | 0.063 | 0.120 | **1.17** | **HYPO** |
| cyan-magenta | 0.048 | 0.015 | 0.030 | **0.031** | 0.017 | 0.040 | **1.29** | **HYPO** |
| red-cyan | 0.048 | 0.015 | 0.015 | **0.026** | 0.019 | 0.015 | **0.58** | **HYPER** |

---

## Key Findings

### HC3 (JYPark) Characteristics
- **Profile**: Intermediate between HC1 and HC2
- **Most similar to HC2**: 6/8 pairs closer to HC2 than HC1
- **Highest sensitivity**: orange-yellow (0.167), green-blue (0.102), blue-purple (0.103)
- **Lowest sensitivity**: red-cyan (0.015), yellow-purple (0.018)

### HC Group Stability
- **High variability pairs**: red-orange (SD=0.116), orange-yellow (SD=0.196)
- **Low variability pairs**: yellow-purple (SD=0.005), cyan-magenta (SD=0.017)
- **Coefficient of variation range**: 0.27 (yellow-purple) to 1.12 (red-orange)

### CVD vs HC Group (sub-08 deutan)
- **Clear HYPO (ratio >1.15)**: 5 pairs
  - orange-yellow (3.74×)
  - yellow-green (4.76×)
  - yellow-purple (3.23×)
  - blue-purple (1.17×)
  - cyan-magenta (1.29×)

- **Clear HYPER (ratio <0.85)**: 2 pairs
  - red-orange (0.60×)
  - red-cyan (0.58×)

- **Borderline**: 1 pair
  - green-blue (1.03×)

---

## Impact on Analysis

### Panel A (JND Comparison)
- Now shows **5 bars per pair**: HC1, HC2, HC3, HC Mean (with SEM error bars), CVD
- HC Mean provides more robust baseline than single HC1
- Error bars show HC group variability (ranges from 0.005 to 0.196)

### Panel C (SRM z vs JND Ratio)
- JND ratios now computed as **CVD / HC Group Mean** (not HC1)
- Concordance recomputed with updated directions
- **Impact**: borderline pairs excluded from concordance calculation

### Statistical Power
- N=3 HC subjects provides:
  - More robust group statistics
  - Better representation of normal variation
  - Foundation for future group-level comparisons

---

## Files Updated

1. **`hc_group_metrics.json`** — Central data source (NEW)
   - Contains all HC individual values, group stats, ratios, directions

2. **`jnd_summary.csv`** — Updated with HC3 columns
   - Added: hc3_jnd_mean, hc_group_mean, hc_group_std, hc_group_sem
   - Added: direction_hc_group (in addition to direction_hc1)

3. **`plot_behavioral_summary.py`** — Updated to use JSON data
   - Loads hc_group_metrics.json instead of hardcoded values
   - Panel A: 5 bars (HC1, HC2, HC3, HC Mean, CVD)
   - Panel C: Uses HC group mean for ratios

4. **`behavioral_pilot_summary.png`** — Regenerated figure

---

## Next Steps

### Immediate
- [ ] Update other analysis scripts (plot_concordance.py, etc.) to use JSON
- [ ] Update notion.md documentation to reflect N=3
- [ ] Regenerate all related figures with HC3 data

### Future
- [ ] Collect additional HC subjects (target N=5-7)
- [ ] Perform formal statistical comparisons (HC vs CVD)
- [ ] Update RSVP analysis if HC3 RSVP data available

---

## Usage

### For analysis scripts:
```python
import json
from pathlib import Path

# Load HC group metrics
with open("results/hc_group_metrics.json", 'r') as f:
    hc_metrics = json.load(f)

# Access data for a specific pair
pair = "orange-yellow"
hc_mean = hc_metrics[pair]['hc_mean']
hc_sem = hc_metrics[pair]['hc_sem']
cvd = hc_metrics[pair]['cvd']
ratio = hc_metrics[pair]['ratio']
direction = hc_metrics[pair]['direction_hc_group']
```

### Regenerate metrics:
```bash
python scripts/compute_hc_group_metrics.py
python scripts/update_jnd_summary.py
python scripts/plot_behavioral_summary.py
```

---

**Status**: ✓ Complete
**Verified**: JSON, CSV, and figure all consistent
**Backward Compatible**: Original HC1-based directions preserved as `direction_hc1`
