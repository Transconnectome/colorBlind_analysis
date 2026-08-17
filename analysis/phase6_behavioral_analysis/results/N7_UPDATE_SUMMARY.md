# HC Group Metrics Update — Full N=7 Pilot Cohort

**Date**: 2026-04-20
**Update**: Migrated pipeline to unified `data/behavior/` source with sub-XX IDs. HC N=5 → **N=7**. RSVP HC N=2 → **N=4**.

---

## 1. Data source migration

| Scope | Before | After |
|---|---|---|
| JND summary | hardcoded `HC1_JND`, `HC2_JND` + `data/{JHKim,JYPark,MJChoi}/` | `data/behavior/sub-{01..08}_jnd_ses1_no_filter_summary.csv` |
| JND trials | `data/{JHKim,JYPark,MJChoi}/jnd_ses1_no_filter_trials.csv` | `data/behavior/sub-{01..07}_jnd_ses1_no_filter_trials.csv` + sub-08 |
| RSVP | hardcoded per-color arrays for HC1/HC2/CVD | `data/behavior/sub-{01,03,06,07,08}_rsvp_8afc_ses1_run1.csv` |

Subject mapping (from RSVP `subj_id` column): sub-01=CDX003 (old HC1), sub-03=CDX005 (old JYPark/HC3), sub-06=CDX006, sub-07=CDX004 (old HC2), sub-08=CDX002 (CVD deutan).

---

## 2. HC Group Statistics (N=7)

`results/hc_group_metrics.json` + `results/jnd_summary.csv` regenerated.

| Pair | HC Mean (N=7) | SD | CVD | Ratio | Direction |
|---|---:|---:|---:|---:|:---:|
| red-orange | 0.1238 | 0.0719 | 0.0625 | 0.50 | **HYPER** |
| orange-yellow | 0.2781 | 0.1353 | 0.8400 | 3.02 | **HYPO** |
| yellow-green | 0.0895 | 0.0435 | 0.2775 | 3.10 | **HYPO** |
| green-blue | 0.0794 | 0.0321 | 0.0775 | 0.98 | borderline |
| yellow-purple | 0.0218 | 0.0061 | 0.0625 | 2.87 | **HYPO** |
| blue-purple | 0.1643 | 0.0925 | 0.1200 | 0.73 | **HYPER** |
| cyan-magenta | 0.0421 | 0.0165 | 0.0400 | 0.95 | borderline |
| red-cyan | 0.0336 | 0.0151 | 0.0150 | 0.45 | **HYPER** |

### Direction changes vs prior N=5

| Pair | N=5 ratio | N=5 direction | N=7 ratio | N=7 direction |
|---|---:|:---:|---:|:---:|
| red-orange | 0.53 | HYPER | 0.50 | HYPER |
| orange-yellow | 3.36 | HYPO | 3.02 | HYPO |
| yellow-green | 3.41 | HYPO | 3.10 | HYPO |
| green-blue | 0.99 | borderline | 0.98 | borderline |
| yellow-purple | 2.95 | HYPO | 2.87 | HYPO |
| **blue-purple** | **0.94** | **borderline** | **0.73** | **HYPER** |
| cyan-magenta | 1.11 | borderline | 0.95 | borderline |
| red-cyan | 0.50 | HYPER | 0.45 | HYPER |

Only **blue-purple** flipped (borderline → HYPER) as two new HCs (sub-04=0.173, sub-03=0.343) dominate the denominator while HC ratio stays comfortably below the HYPER threshold (0.85).

---

## 3. RSVP 8AFC (N=4 HC + sub-08)

RSVP file availability: sub-01, sub-03, sub-06, sub-07, sub-08 only. Sub-02, 04, 05 lack the RSVP run.

### Overall

| Metric | sub-01 | sub-03 | sub-06 | sub-07 | **HC mean (N=4)** | sub-08 (CVD) | Δ (CVD − HC) |
|---|---:|---:|---:|---:|---:|---:|---:|
| accuracy (%) | 100.0 | 95.3 | 96.9 | 96.9 | **97.27** | 81.25 | **−16.02** |
| mean RT correct (s) | 2.302 | 2.656 | 1.974 | 2.818 | **2.437** | 3.716 | **+1.279** |
| timeouts (rt ≤ 0) | 0 | 0 | 1 | 0 | 1 | 1 | — |

### Per-color accuracy

| Color | HC mean ± SEM (N=4) | sub-08 (CVD) | Δ | LOCO-vulnerable (upstream) |
|---|---:|---:|---:|:---:|
| red | 1.000 ± 0.000 | 1.000 | 0.000 | |
| orange | 1.000 ± 0.000 | 0.875 | −0.125 | ✓ |
| yellow | 0.938 ± 0.063 | 0.625 | −0.313 | ✓ |
| green | 0.938 ± 0.036 | 0.625 | −0.313 | |
| cyan | 0.969 ± 0.031 | 1.000 | +0.031 | ✓ |
| blue | 1.000 ± 0.000 | 1.000 | 0.000 | |
| purple | 0.938 ± 0.036 | 0.625 | −0.313 | ✓ |
| magenta | 1.000 ± 0.000 | 0.750 | −0.250 | |

CVD accuracy drops ≥0.25 on **yellow, green, purple, magenta**. Three of four LOCO-vulnerable colors (orange/yellow/purple) show behavioral RSVP drops; only cyan is LOCO-vulnerable without a behavioral drop (CVD=1.000).

---

## 4. Files changed

### Scripts (modified)
- `scripts/compute_hc_group_metrics.py` — rewritten to iterate `sub-01..07` + `sub-08` from `data/behavior/`; hardcoded dicts removed.
- `scripts/plot_per_participant.py` — `DATA_DIR` switched to `data/behavior/`; trial CSV path `<DATA_DIR>/<sub-XX>_jnd_ses1_no_filter_trials.csv`; HC color palette extended to 7 entries.
- `scripts/plot_behavioral_summary.py` — panel B now reads `rsvp_per_color.csv` for HC mean ± SEM (N=4) instead of HC2 inline; HC dot palette extended.
- `scripts/plot_concordance.py` — label annotations now reference sub-08 and pick up N=7 from JSON automatically (no inline N).
- `scripts/update_jnd_summary.py` — unchanged; columns auto-update.

### Scripts (created)
- `scripts/compute_rsvp_metrics.py` — aggregates RSVP from `sub-{01,03,06,07,08}_rsvp_8afc_ses1_run1.csv` into `results/rsvp_summary.csv` and `results/rsvp_per_color.csv`.

### Results (regenerated)
- `results/hc_group_metrics.json`
- `results/jnd_summary.csv` (columns: `pair, hc_group_mean, hc_group_std, hc_group_sem, n_hc, cvd_jnd_mean, ratio_cvd_hc_group, direction_hc_group, sub-01_jnd, …, sub-07_jnd`)
- `results/rsvp_summary.csv` (N=4 HC + sub-08 + HC group mean/SD + diff)
- `results/rsvp_per_color.csv` (HC mean ± SEM vs sub-08 per color)
- `figures/per_participant_jnd_profiles.png`, `per_participant_staircase.png`, `all_participants_comparison.png`, `behavioral_pilot_summary.png`, `concordance_analysis.png`

### Left intact (separate pass needed)
- `notion.md` — 42 legacy references (HC1/HC2/JHKim/JYPark/MJChoi) throughout §1–§5; edit deliberately.
- `results/cross_modal_concordance.json` — `hc_mean` / `direction_hc_mean` per-pair still reflect the old N=5 computation. Regenerate when cross-modal analysis is next rerun.
- `scripts/analysis_gradient_profile.py`, `scripts/analysis_srm_position_displacement.py` — already iterate `sub-01..08`; no behavioral-path change needed.
- `results/HC3_UPDATE_SUMMARY.md`, `cone_model_predictions.csv` — historical; reference `hc_mean` fields still valid insofar as N=3/5 at the time of writing.

---

## 5. Provenance

Generated by:
```
python scripts/compute_hc_group_metrics.py
python scripts/update_jnd_summary.py
python scripts/compute_rsvp_metrics.py
python scripts/plot_per_participant.py
python scripts/plot_behavioral_summary.py
python scripts/plot_concordance.py
```

Data commits: `e4a9874` (HC→sub-01/02 + sub-03/05/06 addition), `65c0a76` (behav_pilot→behavior directory rename + sub-04/sub-07 addition).
