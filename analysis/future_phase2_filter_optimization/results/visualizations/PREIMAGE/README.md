# Pre-image visualizations — 3 fit-losses × 2 subjects

All figures use the **2-component forward model** with (β_s, β_c) from each fit-loss argmin.

| File | Setting | sub-08 (β_s, β_c) | sub-09 (β_s, β_c) |
|---|---|---|---|
| `canonical_sub-XX.png` | Canonical L_fit  (hV4 LOCO ρ argmax — sub-08 §3 PASS source) | (38°, -14°) | (6°, -22°) |
| `cycle14_sub-XX.png` | Cycle 14  (2·L_mwJ(V4) + 1·L_rdm(V1) + 0.2·Tikh) | (58°, -36°) | (44°, +54°) |
| `cycle15_sub-XX.png` | Cycle 15 opt2  (2·L_mwJ(V4) + 1·(1−ρ_LOCO_V1) + 0.2·Tikh) | (68°, -38°) | (44°, +54°) |

## Column legend
1. Original — stimulus θ on the L*=75, C*=40 ring
2. CVD perceives — forward pass at θ
3. Filtered — pre-image θ_pre such that CVD(θ_pre) ≈ θ
4. CVD(Filtered) — acid test (should match Col 1 if invertible)
