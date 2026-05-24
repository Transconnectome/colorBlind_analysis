# S7 (B) — Per (Δλ source, subject, ROI) loss-choice stability

For each cell × Δλ source, we extract the 8 R+C g\* values across the 8 loss targets and quantify spread.

**Thresholds**: tight SD≤0.20, acceptable SD≤0.40, loose SD>0.40. Boundary: g≤0.05 or g≥2.95. Interior: g∈[0.5, 2.8].

## Main table (12 rows = 4 cells × 3 Δλ sources)

| subject | ROI | Δλ source | Δλ (nm) | SD(g) | range(g) | boundary | stable | verdict |
|---|---|---|---:|---:|---:|---:|---:|---|
| sub-08 | V1 | DPS_lit | 6.0 | 0.722 | 2.250 | 1 | 7/8 | loose |
| sub-08 | V1 | Boehm_mid | 8.0 | 0.922 | 2.200 | 2 | 6/8 | loose |
| sub-08 | V1 | JND_Lamb | 6.5 | 0.712 | 2.250 | 1 | 7/8 | loose |
| sub-08 | V4 | DPS_lit | 6.0 | 0.509 | 1.200 | 0 | 8/8 | loose |
| sub-08 | V4 | Boehm_mid | 8.0 | 0.943 | 2.150 | 1 | 5/8 | loose |
| sub-08 | V4 | JND_Lamb | 6.5 | 1.083 | 2.250 | 4 | 4/8 | loose |
| sub-09 | V1 | DPS_lit | 10.0 | 0.310 | 1.000 | 2 | 6/8 | acceptable |
| sub-09 | V1 | Boehm_low | 3.0 | 1.005 | 3.000 | 5 | 3/8 | loose |
| sub-09 | V1 | JND_Lamb | 1.5 | 0.719 | 2.200 | 4 | 4/8 | loose |
| sub-09 | V4 | DPS_lit | 10.0 | 0.814 | 2.100 | 0 | 8/8 | loose |
| sub-09 | V4 | Boehm_low | 3.0 | 1.346 | 3.000 | 5 | 1/8 | loose |
| sub-09 | V4 | JND_Lamb | 1.5 | 1.392 | 3.000 | 7 | 1/8 | loose |

## Most loss-stable Δλ per cell

Selection: lowest SD wins; tie-break by higher stable_count then lower boundary_count.

| subject | ROI | best Δλ source | Δλ (nm) | SD | stable | boundary | verdict |
|---|---|---|---:|---:|---:|---:|---|
| sub-08 | V1 | JND_Lamb | 6.5 | 0.712 | 7/8 | 1 | loose |
| sub-08 | V4 | DPS_lit | 6.0 | 0.509 | 8/8 | 0 | loose |
| sub-09 | V1 | DPS_lit | 10.0 | 0.310 | 6/8 | 2 | acceptable |
| sub-09 | V4 | DPS_lit | 10.0 | 0.814 | 8/8 | 0 | loose |

## Per-cell g\* matrices (rows = loss, columns = Δλ source)

### sub-08 V1

| loss | DPS_lit (6.0nm) | Boehm_mid (8.0nm) | JND_Lamb (6.5nm) |
|---|---|---|---|
| L1_behav_alpha | 2.00 | 2.00 | 2.00 |
| L2_behav_gamma | 2.25 | 2.20 | 2.25 |
| L3_LOCO | 0.00 | 0.00 | 0.00 |
| L4_RDM_corr | 2.15 | 2.10 | 2.05 |
| L5_behav_composite | 2.20 | 2.15 | 2.20 |
| L6_neural_composite | 2.15 | 0.00 | 2.05 |
| L7_all_equal | 2.20 | 2.15 | 2.15 |
| L8_modality_5050 | 2.25 | 2.15 | 2.25 |

### sub-08 V4

| loss | DPS_lit (6.0nm) | Boehm_mid (8.0nm) | JND_Lamb (6.5nm) |
|---|---|---|---|
| L1_behav_alpha | 2.00 | 2.00 | 2.00 |
| L2_behav_gamma | 2.25 | 2.20 | 2.25 |
| L3_LOCO | 1.10 | 0.05 | 0.00 |
| L4_RDM_corr | 1.25 | 0.30 | 0.00 |
| L5_behav_composite | 2.20 | 2.15 | 2.20 |
| L6_neural_composite | 1.15 | 0.25 | 0.00 |
| L7_all_equal | 2.25 | 2.15 | 2.20 |
| L8_modality_5050 | 2.30 | 2.20 | 0.00 |

### sub-09 V1

| loss | DPS_lit (10.0nm) | Boehm_low (3.0nm) | JND_Lamb (1.5nm) |
|---|---|---|---|
| L1_behav_alpha | 2.00 | 2.00 | 2.00 |
| L2_behav_gamma | 2.60 | 3.00 | 3.00 |
| L3_LOCO | 3.00 | 1.40 | 0.80 |
| L4_RDM_corr | 2.30 | 0.00 | 2.45 |
| L5_behav_composite | 2.60 | 3.00 | 3.00 |
| L6_neural_composite | 3.00 | 2.25 | 2.45 |
| L7_all_equal | 2.55 | 3.00 | 3.00 |
| L8_modality_5050 | 2.60 | 3.00 | 3.00 |

### sub-09 V4

| loss | DPS_lit (10.0nm) | Boehm_low (3.0nm) | JND_Lamb (1.5nm) |
|---|---|---|---|
| L1_behav_alpha | 2.00 | 2.00 | 2.00 |
| L2_behav_gamma | 2.60 | 3.00 | 3.00 |
| L3_LOCO | 0.50 | 0.00 | 0.00 |
| L4_RDM_corr | 1.05 | 0.15 | 0.00 |
| L5_behav_composite | 2.60 | 3.00 | 3.00 |
| L6_neural_composite | 1.05 | 0.15 | 0.00 |
| L7_all_equal | 2.55 | 3.00 | 3.00 |
| L8_modality_5050 | 2.60 | 3.00 | 3.00 |
