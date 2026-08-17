# PPT 슬라이드 — Forward → Neural mimicry → Inverse → Filter

**Purpose**: 한 슬라이드로 "기존 색 → CVD 변환 → 신경반응 모방 → 역함수 → 색 역변환" 전 과정을 설명.
**Strategy**: 새 그림을 그리지 않는다 — 기존 `BEST_4col_sub-08_V4_LOCO_canonical_bs38_bcm14.png`의 4-column 자체가 forward/inverse pipeline의 시각적 증거다. 위에 PowerPoint shape(화살표·박스·수식)을 overlay 한다.

**Companion docs**:
- `mathematical_basis.md` §1–§9 (수식 정의)
- `claude_in_ppt_prompts.md` (Slide 1: 3 모델 비교)
- `BEST_summary.json` (피험자별 파라미터, loss 가중치 1.0/0.5/0.2/0.1)

---

## 1. 핵심 수식 (3 줄)

기존 색 $c$ 의 hue angle $\theta_{\text{base}}(c)$ ∈ {0°, 45°, ..., 315°}.

### (1) Forward — CVD가 지각하는 색 (cortical 2-component, BEST model)

$$
\boxed{\;
\delta\theta_{\text{2C}}(c;\,\beta_s,\beta_c)
= \beta_s\cos\!\bigl(\theta_{\text{base}}(c) - 90°\bigr)
+ \beta_c\cos\!\bigl(\theta_{\text{base}}(c) - \theta_{\text{conf}}\bigr)
\;}
$$

$$
\theta_{\text{CVD}}(c) = \bigl[\theta_{\text{base}}(c) + \delta\theta_{\text{2C}}(c)\bigr] \bmod 360°
$$

| 피험자 | $\theta_{\text{conf}}$ | $\beta_s$ | $\beta_c$ |
|---|---|---|---|
| sub-08 (deutan) | 150° | 38° | −14° |
| sub-09 (protan) | 16° | 6° | −22° |

### (2) Neural mimicry — fMRI fit (HC pool로 학습한 encoder)

$$
\hat{Y}(c) = W \cdot \phi\!\bigl(\theta_{\text{CVD}}(c)\bigr),\qquad
W = \mathrm{ridge\_gcv}(X_{\text{HC}}, \phi(\theta_{\text{HC}}))
$$

- $\phi(\theta)$: 360-channel forward-encoded color basis (FE-K)
- $W$: HC 피험자별로 학습된 voxel weights
- LOCO 검증: $\rho(\hat{Y}, X_{\text{CVD}})$ per color = "vulnerability" 벡터
- **Loss** (BEST fit selection):
  $$L_{\text{fit}} = 1.0\cdot L_{\text{vuln}} + 0.5\cdot L_{\text{rank}} + 0.2\cdot L_{\text{rdm}} + 0.1\cdot L_{\text{smooth}}$$

### (3) Inverse — 보정 필터 (pre-image)

$$
\boxed{\;
\theta^*(c) = f^{-1}_{2C}\bigl(\theta_{\text{base}}(c)\bigr)
\quad\text{s.t.}\quad
f_{2C}\bigl(\theta^*(c)\bigr) = \theta_{\text{base}}(c)
\;}
$$

즉, **CVD가 $\theta^*$ 자극을 받았을 때 지각하는 hue가 정확히 원래 $\theta_{\text{base}}$가 되도록** 자극을 미리 회전. 풀이는 1-DOF root-finding (Brent / bisection), **8/8 colors exact** (sub-08·09 모두).

### Round-trip 항등식 (validation)

$$
f_{2C}(\theta^*(c)) \equiv \theta_{\text{base}}(c) \quad \text{for all } c \in \{c_1,\ldots,c_8\}
$$

---

## 2. 4-column 그림 = pipeline 그 자체

`results/BEST_4col_sub-08_V4_LOCO_canonical_bs38_bcm14.png`의 4 column은 다음 4 stage에 1:1 대응:

| Column | Stage | 수식 |
|---|---|---|
| **Original** | $c$ — 원본 자극 | $\theta_{\text{base}}(c)$ |
| **CVD perceives** | $f_{2C}(c)$ — CVD가 보는 색 (no filter) | $\theta_{\text{CVD}} = \theta_{\text{base}} + \delta\theta_{2C}$ |
| **Filtered (pre-image)** | $f^{-1}_{2C}(c) = \theta^*$ — 보정된 자극 | $\theta^*$ s.t. $f_{2C}(\theta^*)=\theta_{\text{base}}$ |
| **CVD(Filtered)** | $f_{2C}(\theta^*)$ — CVD가 필터된 자극을 본 결과 | $\approx \theta_{\text{base}}$ (round-trip) |

Column 4 ≈ Column 1 가 곧 **filter가 작동한다는 증거**.

---

## 3. 슬라이드 레이아웃 (Claude-in-PowerPoint prompt)

```
Create slide titled
"Forward and Inverse: From CVD Perception to Corrective Filter"
with subtitle "2-component cortical model + exact pre-image (8/8 colors)".

Layout: a single referenced image (centered, ~62% of slide width) with four
horizontal arrows above the image connecting the four columns, plus a small
equation card on the right (~28% width) and one footer takeaway.

REFERENCED IMAGE (insert verbatim, do not regenerate):
  /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization/results/BEST_4col_sub-08_V4_LOCO_canonical_bs38_bcm14.png

ARROW BAND (across the top of the image, between column headers):
  Column 1 → Column 2:  curved arrow labeled  "Forward map  f_2C  (CVD distortion)"
  Column 2 → Column 3:  curved arrow labeled  "Inverse  f_2C^{-1}  (pre-image)"
  Column 3 → Column 4:  curved arrow labeled  "Forward again  (round-trip test)"
  Column 4 ⇢ Column 1:  thin dashed arrow labeled  "≈ identity (8/8 exact)"

EQUATION CARD (right of image, top to bottom):
  Title: "Three equations"
  (1) Forward (CVD distortion):
      δθ(c) = β_s·cos(θ_base − 90°) + β_c·cos(θ_base − θ_conf)
      θ_CVD = θ_base + δθ  (mod 360°)
  (2) Pre-image filter:
      θ*(c) = f_2C^{-1}(θ_base(c))     →  solved by 1-D root finding
  (3) Round-trip identity:
      f_2C(θ*(c)) = θ_base(c)            →  8/8 exact, both subjects

  Below the equations, a small parameter table:
      sub-08 deutan:  θ_conf=150°, (β_s, β_c) = (38°, −14°)
      sub-09 protan:  θ_conf= 16°, (β_s, β_c) = (6°, −22°)

FOOTER TAKEAWAY (italic green):
  "Column 4 reproducing Column 1 is the filter's empirical signature —
   the corrective stimulus, once viewed through CVD, is perceived as the original."

Style: academic, 16:9, sans-serif, minimal chrome, single blue accent (#1f4e79).
Body ≥14pt; equations in serif monospace 11pt. Do NOT generate new image; use
only the referenced PNG path verbatim. Do not move or crop the image content.
```

---

## 4. 옵션: 한 슬라이드 더 ("Neural mimicry layer")

색 자체의 인지가 아니라 **신경반응 측면**의 모방을 강조하고 싶다면 보조 슬라이드를 추가:

```
Title: "How the model knows what CVD perceives — fMRI encoder layer"
Subtitle: "ridge_gcv encoder trained on HC pool; LOCO-validated"

Body layout (3 horizontal blocks):
  Block 1 — "Encoder fit"
    For each HC subject s ∈ {01,...,07}:
      W_s = ridge_gcv(X_s, φ(θ_HC))
    X_s ∈ ℝ^(48 × n_voxels)  (6 runs × 8 colors)
    φ(·): 360-channel FE basis

  Block 2 — "Forward through CVD distortion"
    Given candidate (β_s, β_c):
      θ' = θ + β_s·cos(θ − 90°) + β_c·cos(θ − θ_conf)
      Ŷ_s(c) = W_s · φ(θ'(c))

  Block 3 — "Vulnerability and fit"
    vuln(c) = ρ_voxel(Ŷ_HC-pool(c), X_CVD(c))        ← LOCO over colors
    L_fit  = 1.0·L_vuln + 0.5·L_rank + 0.2·L_rdm + 0.1·L_smooth
    BEST (β_s, β_c) = argmin over a 26 × 51 grid

Footer takeaway (italic green):
  "The encoder makes the CVD-fit objective: 'find the cortical distortion that
   reproduces the CVD voxel pattern as well as HC encoders reproduce their own.'
   The pre-image then inverts that distortion in stimulus space."
```

---

## 5. 메모

- 새 figure 생성 비추천 — 4-column이 이미 forward/inverse를 동시에 보여주므로 시각적 효율이 최대.
- AI schematic (channel C, presentation/claude_in_ppt_prompts_meeting.md convention)도 가능하나, 데이터-기반 4-column보다 정보 손실.
- 보조 figure가 필요하면 `scripts/regen_fig4_hybrid_paper.py` 또는 `scripts/visualization/figs_slide5_rc_panels.py` 참조 (실데이터 기반).
- 수식 표기는 `mathematical_basis.md` §1, §5', §6과 일치 — 회의 시 같은 noratation 사용.
