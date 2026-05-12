# Sub-08 6-way + Canonical Comparison

**Generated**: 2026-05-10
**Subject**: sub-08 (deutan)
**Purpose**: 한 폴더 내 직접 비교용. Canonical (§3 PASS reference)을 6-way 후보들과 나란히.

## File Index

| File | Filter | (β_s, β_c) | Forward map 식 | Status |
|---|---|---|---|---|
| `F0_canonical_38_-14_vfc.png` | Canonical (LOCO ρ argmax) | (38°, −14°) | vfc (h_base) | **§3 PASS** (2026-04-17) |
| `F1_V1V4avg_19_+3.5_phase3.png` | V1+V4 avg | (19°, +3.5°) | phase3 (CIELab) | No-op (V1 degenerate) |
| `F2_V4only_38_+7_phase3.png` | V4-only Cycle 10d | (38°, +7°) | phase3 (CIELab) | Chain confusion (β_c sign 반대) |
| `F3_crossROI_68_-38_phase3.png` | Cross-ROI Cycle 12 | (68°, −38°) | phase3 (CIELab) | **Best of 6** (3-way cool-ivory collapse) |
| `F4_cycle15opt2_68_-38_vfc.png` | Cycle 15 opt2 | (68°, −38°) | vfc (h_base) | Worst tier (5-way cyan collapse) |
| `F6_cycle14_58_-36_vfc.png` | Cycle 14 mwj+rdm | (58°, −36°) | vfc (h_base) | Worst tier (5-way cyan collapse) |

(F5 = Windows commercial filter; user-side screenshot, not in repo.)

## Critical Note

**F3와 F4는 nominal (β_s, β_c) 동일 (68°, −38°)이지만 forward map 식이 다름**:
- F3: phase3 식 = `dt = β_s·cos(θ_CIELab − 90°) + β_c·cos(θ_CIELab − θ_conf)` ← **fitting과 inconsistent**
- F4: vfc 식 = `h_base = machado_shifted_hue_at(0, cvd, θ); dt = β_s·cos(h_base − 90°) + β_c·cos(h_base − θ_conf)` ← **fitting과 일치**

같은 (β_s, β_c)에서 두 식의 pre-image 평균 64.5° 차이.

## Canonical Fit + Simulator (요약)

**Canonical (38°, −14°) source**: `results/fits/phase_a_2component/sub-08_V4_2component.json`

| 항 | Value |
|---|---:|
| L_fit (= 1·L_vuln + 0.5·L_rank + 0.2·L_rdm + 0.1·L_smooth) | 0.201 |
| Spearman ρ (vuln_sim vs vuln_cvd) | **0.881** |
| label_perm_p | **0.0036** |
| Δρ vs baseline (Δλ=0) | **+0.595** |

**Loss code**: `scripts/loco_distortion_fit.py:197-263` (`compute_fit_loss`)
**Forward map (2-component)**: `scripts/loco_distortion_fit.py:178-187` (`get_shifted_design('2component')`) — `vfc 식과 동일`

**Simulator chain**: CIELab → XYZ → Stockman LMS → opponent (rg=L−M, by=S−(L+M)/2) → hue angle. Standard color science (Hering opponent + Stockman 2° fundamentals + Machado 2009 cone shift). 검증 detail: `analysis/future_phase2_filter_optimization/FORWARD_MODEL_AUDIT.md`.

**Verdict**: vfc 식 + canonical loss + simulator 모두 표준 색과학 grounded. **시각화 신뢰 가능**.

## PASS 평가

| Filter | YG-C arc 보존 | 8-color 카테고리 | 추가 collapse | Verdict |
|---|---|---|---|---|
| F0 canonical | ✓ (c5/c6/c7 sky→dark sky→deep blue gradient) | ✓ | c2 orange→green, c8 magenta partial | **PASS** (color-local fails 인정) |
| F3 cross-ROI | ✓ (8-color distinct) | ✓ | **3-way cool-ivory collapse** (c5/ConfP−/sRGB C) | **부분 PASS** (식 일관성 미해결) |
| F1, F2, F4, F6 | × (collapse 또는 chain confusion) | △/× | 다중 collapse | FAIL |
