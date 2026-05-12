# A1 Diagnostic Verdict — W-fixed (LOCO + unshifted training)

This file compares two LOCO simulators that differ ONLY in how the cone shift δθ enters the ridge weights W during training:

- `wretrained` (shift_at_both): W is retrained at every (β_s, β_c) using the SHIFTED design C(θ+δθ) on 7 non-k colors; held-out prediction also uses the shifted design.
- `wfixed` (shift_at_test_only / A1): W_k is trained ONCE per (subject × held-out color) on the UNSHIFTED design C_orig of the 7 non-k colors; only the held-out test design C_shifted(θ_k+δθ_k) is shifted at every (β_s, β_c).

Loss family is held FIXED across simulators: same 4-term L_fit (`1·L_vuln + 0.5·L_rank + 0.2·L_rdm + 0.1·L_smooth`), same NORM, same ΔRDM reference (single-W trained on all 8 colors with C_orig). The only thing that changes between landscapes is the vuln_sim computation that feeds L_vuln and L_rank.

HC pool used: **sub-01..07 (n=7)** — same as the existing 4-term cache to enable like-for-like comparison. The task brief mentioned sub-01..06 but this would have differed from the cached wretrained reference and confounded simulator-vs-pool differences.

## Per-subject verdicts

### sub-08 (V4)

- wretrained argmin: (β_s=10, β_c=-32), norm=33.5°, ρ=0.833, L_fit=0.2170
- wfixed     argmin: (β_s=6, β_c=-48), norm=48.4°, ρ=0.762, L_fit=0.2483
- Δ(β_s, β_c) = (-4°, -16°), Δnorm = +14.8°
- Max σ(vuln_sim): wretrained=0.264, wfixed=0.155, Δ=-0.109
- Baseline ρ(β=0): wretrained=0.286, wfixed=0.286
- **Verdict: moderate_sensitivity** — Intermediate → result is sensitive to the simulator choice; report as caveat.

### sub-09 (V4)

- wretrained argmin: (β_s=30, β_c=+46), norm=54.9°, ρ=0.500, L_fit=0.2840
- wfixed     argmin: (β_s=46, β_c=+48), norm=66.5°, ρ=0.214, L_fit=0.3574
- Δ(β_s, β_c) = (+16°, +2°), Δnorm = +11.6°
- Max σ(vuln_sim): wretrained=0.264, wfixed=0.155, Δ=-0.109
- Baseline ρ(β=0): wretrained=-0.333, wfixed=-0.333
- **Verdict: moderate_sensitivity** — Intermediate → result is sensitive to the simulator choice; report as caveat.

### sub-10 (V4)

- wretrained argmin: (β_s=20, β_c=-42), norm=46.5°, ρ=0.405, L_fit=0.2175
- wfixed     argmin: (β_s=6, β_c=-48), norm=48.4°, ρ=0.024, L_fit=0.3181
- Δ(β_s, β_c) = (-14°, -6°), Δnorm = +1.9°
- Max σ(vuln_sim): wretrained=0.264, wfixed=0.155, Δ=-0.109
- Baseline ρ(β=0): wretrained=-0.476, wfixed=-0.476
- **Verdict: moderate_sensitivity** — Intermediate → result is sensitive to the simulator choice; report as caveat.

## Framing

This diagnostic test asks whether the canonical Phase 2 (β_s, β_c) point estimate is sensitive to the choice of LOCO simulator family. It does NOT introduce a new selection rule, specificity test, or filter criterion. Verdicts above are descriptive: they characterise how the same (loss, grid, HC pool, ΔRDM reference) responds when only the vuln_sim simulator changes.

