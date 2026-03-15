# Future Phase 1: Forward Model — Comprehensive Experiment Plan

> Last updated: 2026-03-14
> Status: Core pipeline complete. Entering **residual analysis + CVD prediction model** phase.
> Supersedes: 2026-03-11 version (smooth_tikh rejection / adaptive basis proposal)

---

## 0. Executive Summary

### 현재 위치

Forward encoding model `Y_s = W_s @ C(θ; K)` validated:
- **Encoder**: ridge_gcv confirmed (smooth_tikh rejected — §8)
- **Primary ROI**: hV4 (permutation p=0.026, FE-3)
- **Per-ROI optimal K**: V1→FE-2, V2→FE-3, V3→FE-8, hV4→FE-3
- **Adaptive basis**: Center optimization = no benefit (nested LOCO §4b). **K가 유일한 유의미한 모델 파라미터**
- **HC-CVD gap**: K-dependent (54–78% reduction) + axis-specific (cool/S-axis persists)
- **Cross-phase**: SRM prevalidation (V2 blue-purple p=0.042) ↔ FE LOCO (hV4 blue p=0.046) convergence

### Core Finding: Warm/Cool Axis Dissociation

| Axis | Colors | FE-6 HC-CVD Gap | FE-K HC-CVD Gap | Reduction | Interpretation |
|------|--------|:---------------:|:---------------:|:---------:|----------------|
| **Warm (L-M)** | red, orange, yellow, green | +0.118 | −0.060 | >100% (reversed) | Model-specification artifact |
| **Cool (S)** | cyan, blue, purple, magenta | +0.362 | +0.237 | 35% only | **Residual biology candidate** |

> Warm-color gap = FE-6 overparameterization 산물 (K correction으로 완전 해소).
> Cool-color gap = K optimization 후에도 65% 잔존 → S-axis distortion → Phase 2 filter target.

### 3가지 병렬 Track

| Track | 목적 | Priority | 예상 소요 |
|-------|------|:--------:|:---------:|
| **A. Residual Biology Report** | Model optimization 후 잔존하는 HC-CVD 차이의 체계적 특성화 | HIGH | 3–4일 |
| **B. CVD Prediction Model** | Channel shift / anisotropic basis 기반 personalized encoder | HIGH | 5–7일 |
| **C. Dimensionality & Organization** | RT-5 해결: K-sensitivity가 model selection인지 biology인지 | MEDIUM | 2–3일 |

---

## Track A: Residual Biology Report (3-Layer Framework)

### 목적

"Optimized-model residual biology" 문서화 — 모든 모델 최적화(encoder, K, center)를 소진한 후 남는 HC-CVD 차이. 이것이 Phase 2 filter 설계의 **입력 사양(input specification)**.

3개 Layer로 구조화:
- **Layer 1**: Basis-family selection & K sensitivity → 모델 자유도가 gap에 미치는 영향
- **Layer 2**: Per-color residual geometry → 어떤 색이, 어떤 방향으로 distorted인지
- **Layer 3**: Cross-phase convergence → 독립 파이프라인(SRM ↔ FE) 수렴 검증

---

### Layer 1: Basis-Family & K Sensitivity

#### Exp A1. FE-K MAE Retry (Phase 3 Cross-Check)

**질문**: Phase 3 hV4 HC-CVD MAE gap (FE-6: d=1.69, p=0.017)이 per-ROI optimal K에서도 유지되는가?

**방법**:
- LOCO with FE-K (V1=2, V2=3, V3=8, V4=3), Phase 3 MAE 메트릭
- FE-6 MAE gap vs FE-K MAE gap 비교
- HC paired t-test (FE-K vs FE-6)

**기대 결과**:
- hV4 gap: d ≈ 1.69 → 0.6–0.8 (voxel_corr 발견 d=1.36→0.63과 일치)
- V1 gap: near-zero (78% reduction과 일치)

**의미**: K-sensitivity가 voxel_corr 뿐 아니라 MAE에서도 재현됨을 확인. 결과가 메트릭 불변(metric-invariant)임을 보장.

**실행**:
```
위치:    analysis/phase3_decoder_comparing/model_comparison_validation/
Scripts: scripts/loco_fek_retry.py                     ← READY
SLURM:   run_loco_fek_retry.sbatch                     ← READY
분석:    scripts/analyze_loco_fek.py                    ← READY
결과:    results/loco_fek_retry/
```
```bash
# 서버 업로드 (하나의 scp)
scp analysis/phase3_decoder_comparing/model_comparison_validation/scripts/loco_fek_retry.py \
    analysis/phase3_decoder_comparing/model_comparison_validation/run_loco_fek_retry.sbatch \
    analysis/phase3_decoder_comparing/model_comparison_validation/scripts/analyze_loco_fek.py \
    haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/phase3_decoder_comparing/model_comparison_validation/

# 실행 (~30분)
ssh haba6030@node3 "cd /scratch/connectome/haba6030/colorBlind && \
    sbatch analysis/phase3_decoder_comparing/model_comparison_validation/run_loco_fek_retry.sbatch"

# 결과 다운로드 → 로컬 분석
scp -r haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/phase3_decoder_comparing/model_comparison_validation/results/loco_fek_retry \
    analysis/phase3_decoder_comparing/model_comparison_validation/results/
conda activate srm && python analysis/phase3_decoder_comparing/model_comparison_validation/scripts/analyze_loco_fek.py \
    --results_dir analysis/phase3_decoder_comparing/model_comparison_validation/results/loco_fek_retry
```

#### Exp A2. Basis Anisotropy Test

**질문**: 비균등 채널 배치(non-uniform spacing)가 CVD LOCO를 개선하는가?

**방법**:
- 3가지 basis 구성 per ROI:
  1. **Uniform FE-K** (현재): K 채널 균등 배치 (360°/K 간격)
  2. **Cool-dense**: [180°, 315°] 범위에 채널 밀집 배치 (CVD residual이 큰 영역)
  3. **Warm-dense**: [0°, 135°]에 밀집 (negative control — warm gap 이미 해소됨)
- LOCO 평가 + HC paired t-test (anisotropic vs uniform)

**기대 결과**:
- Cool-dense ≈ uniform (K가 유일한 meaningful DOF인 경우, nested LOCO와 일치)
- Cool-dense > uniform이면 → CVD가 cool-axis resolution으로부터 이득 → Phase 2 입력

**의미**: "채널을 **어디에** 놓느냐"가 중요한지 검증. "**몇 개** 놓느냐만 중요"(§4b 결론) vs "비균등 배분이 추가 이득 제공" 구분.

**실행**:
```
위치:    analysis/future_phase1_forward_model/
Script:  scripts/basis_anisotropy_test.py               ← TO CREATE
SLURM:   sbatch/run_basis_anisotropy.sbatch             ← TO CREATE
분석:    scripts/analyze_basis_anisotropy.py             ← TO CREATE
결과:    results/basis_anisotropy/
```

---

### Layer 2: Per-Color Residual Geometry

#### Exp A3. Signed Circular Bias Analysis

**질문**: CVD LOCO 오류가 대칭적(random)인가, 방향성(systematic distortion)이 있는가?

**방법**:
- 각 held-out color θ_test에 대해, LOCO 재구성에서 predicted angle θ̂ 계산
  - θ̂ = argmax corr(predicted_pattern, basis_template)
- Signed circular error: Δθ = θ̂ − θ_test (wrapped to [−180°, 180°])
  - 양수 Δθ = 시계방향 편향, 음수 = 반시계방향
- HC mean signed bias per color vs CVD individual profiles

**기대 결과**:
- HC: 대칭 오류 (color별 mean Δθ ≈ 0)
- CVD cool region: 체계적 편향 (예: blue → cyan 방향 끌림, 즉 반시계방향)
- sub-08/09: 일관된 방향성, sub-10: HC와 유사

**의미**: Phase 2 filter T_ψ의 **방향**을 결정. 단순 gain 조절이 아닌 **방향 보정(directional correction)**이 필요한지 확인. Direction + magnitude = filter specification.

**실행**:
```
위치:    analysis/future_phase1_forward_model/
Script:  scripts/signed_circular_bias.py                ← TO CREATE (로컬 실행 가능 — 기존 nested LOCO JSON 사용)
결과:    results/signed_bias/
```
> **서버 불필요**: 이미 다운로드된 per-subject nested LOCO JSON (`results/nested_adaptive/sub-*_V4_nested_adaptive.json`)에서 per-color prediction을 추출하여 로컬 계산.

#### Exp A4. 28-Pair Pairwise Residual Heatmap

**질문**: 8C2 = 28개 색 쌍 중 어디에서 HC-CVD pairwise distance 차이가 가장 큰가?

**방법**:
- 각 subject의 LOCO-predicted RDM (8×8) → 28 pairwise entries
- HC mean pairwise matrix vs 각 CVD subject
- Effect size (d) heatmap: 빨강 = HC >> CVD, 파랑 = CVD >> HC
- Key pair subsets overlay:
  - **L-M pairs**: red-green, red-orange, orange-green
  - **S-axis pairs**: blue-purple, blue-yellow, purple-yellow
  - **Cross-axis**: red-blue, orange-purple

**기대 결과**:
- S-axis pairs에서 |d| 최대 (per-color 분석과 일치)
- L-M pairs ≈ 0 (warm gap 이미 해소)
- Cross-axis pairs로 축 간 상호작용 확인

**의미**: FE LOCO geometry와 SRM prevalidation pairwise geometry를 직접 비교 가능한 형태로 변환. 두 독립 파이프라인의 **28-pair 수준** 수렴을 정량화. Phase 2에 어떤 pair distortion을 교정해야 하는지 직접 제공.

**실행**:
```
위치:    analysis/future_phase1_forward_model/
Script:  scripts/pairwise_residual_heatmap.py           ← TO CREATE (로컬 실행)
결과:    results/pairwise_residual/
```

#### Exp A5. Neighboring-Color Confusion Structure

**질문**: CVD LOCO 실패 시, 인접 색과 혼동하는가 아니면 비인접 색과도 혼동하는가?

**방법**:
- 각 held-out color에 대해 나머지 7색과의 voxel_corr를 rank
- Confusion probability matrix (8×8): 각 행 = target color, 각 열 = 혼동 대상
- HC vs CVD 비교: 혼동 구조의 차이

**기대 결과**:
- HC: predominantly nearest-neighbor errors (±45° = 인접 색)
- CVD cool: 비인접 혼동 발생 (예: blue를 green/yellow과 혼동 = 축 압축 증거)

**의미**: 혼동 구조가 color space distortion의 **위상(topology)**을 드러냄. 비인접 혼동이 많으면 filter는 **remapping** 필요 (단순 scaling이 아님).

**실행**:
```
위치:    analysis/future_phase1_forward_model/
Script:  scripts/confusion_structure.py                 ← TO CREATE (로컬 실행)
결과:    results/confusion_structure/
```

---

### Layer 3: Cross-Phase Convergence

#### Exp A6. SRM ↔ FE 28-Pair Correlation

**질문**: SRM pairwise distances (Phase 2)와 FE LOCO pairwise distances (Phase F1)가 subject별로 얼마나 상관하는가?

**방법**:
- SRM prevalidation: 28 crossnobis pairwise distances per CVD subject per ROI
  - 소스: `future_phase2_filter_optimization/pre_validation/results/crossnobis_pairs/`
- FE LOCO: 28 pairwise voxel_corr 차이 per subject per ROI
  - 소스: `future_phase1_forward_model/results/nested_adaptive/`
- Spearman correlation: 두 28-element vectors 간
- 기존 부분 결과: crossnobis-SRM r=0.33–0.70

**기대 결과**:
- hV4에서 r > 0.5 (두 파이프라인 모두 유의한 효과)
- V1/V2에서 약한 상관 (FE LOCO 자체가 permutation fail)

**의미**: 높은 cross-pipeline 상관은 **두 방법이 동일한 기저 구조를 측정**함을 확인. SRM-derived filter target을 FE-based Phase 2 pipeline에서 사용하는 것을 정당화.

**실행**:
```
위치:    analysis/future_phase1_forward_model/
Script:  scripts/cross_phase_correlation.py             ← TO CREATE (로컬 실행)
입력:    future_phase2_filter_optimization/pre_validation/results/ + results/nested_adaptive/
결과:    results/cross_phase/
```

---

## Track B: CVD Prediction Model (Channel Shift)

### 목적

현재 encoder는 **group-uniform FE basis** (모든 subject에 동일 K, 동일 간격)를 사용. CVD에 suboptimal:

1. CVD의 S-axis distortion → cool channel이 다른 tuning 필요
2. CVD는 **더 적거나 다르게 배치된** 채널이 이득일 수 있음
3. sub-10 (compensated)은 sub-08/09와 다른 처리가 필요

Track B는 각 CVD subject의 representational geometry에 적응하는 **personalized encoder**를 개발.

**핵심 아이디어 — Channel Shift**:
기존 적응 기저 최적화(§4a-4b)에서 **center 자유 최적화**는 overfitting으로 실패.
대신 **저차원 파라메트릭 왜곡(low-DOF parametric warping)**으로 접근:
```
centers_shifted = centers_uniform + Δ(θ)
```
여기서 Δ(θ)는 2개 파라미터로 제어되는 smooth 함수 → nested CV에서 overfitting 위험 최소화.

---

#### Exp B1. Subject-Specific K Selection (Data-Driven)

**질문**: 각 개별 subject의 optimal K는 무엇인가? (group-level이 아닌 individual)

**방법**:
- Per subject: inner LOCO-CV across K ∈ {2, 3, 4, 5, 6, 8, 10, 12}
- K* = argmax(inner_LOCO_voxel_corr)
- HC vs CVD K* 분포 비교 (Welch t-test + Crawford-Howell per CVD)

**기대 결과**:
- HC K* ≈ 3–4 (group-level optimal과 일치)
- CVD K* ≈ 2–3 (더 낮은 K → 적은 자유도 → distorted space에 better fit)
- sub-10 (compensated) K* → HC에 가까움

**의미**: CVD가 체계적으로 더 낮은 K*를 선택하면, **genuine dimensionality reduction** 증거 (단순 model selection artifact가 아님). 이 결과는 Track C (dimensionality analysis)와 삼각측량(triangulation).

**실행**:
```
위치:    analysis/future_phase1_forward_model/
Script:  scripts/subject_k_selection.py                 ← TO CREATE
SLURM:   sbatch/run_subject_k.sbatch                    ← TO CREATE
결과:    results/subject_k/
서버 예상: ~45분 (10 subjects × 4 ROIs × 8 K values)
```

---

#### Exp B2. Anisotropic Basis — Parametric Channel Shift

**질문**: 저차원 파라메트릭 채널 이동(channel shift)이 CVD encoding을 개선하는가?

**방법**:
- **Parametric channel shift model** (2 자유 파라미터):
  ```python
  def shift_centers(centers_uniform, a, b):
      """
      centers_uniform: (K,) 균등 배치 [0, 360/K, 2*360/K, ...]
      a: L-M ↔ S tradeoff (sin 2θ 계수)
      b: warm-cool asymmetry (cos 2θ 계수)
      returns: (K,) shifted centers
      """
      theta_rad = np.deg2rad(centers_uniform)
      delta = a * np.sin(2 * theta_rad) + b * np.cos(2 * theta_rad)
      return (centers_uniform + np.rad2deg(delta)) % 360
  ```
- (a, b) 최적화: 7-fold inner LOCO-CV (nested, §4b 패턴 재사용)
  - outer fold: 1색 hold-out
  - inner: 나머지 7색으로 (a, b) grid search → best → outer 평가
- 고정 K per ROI (group-level optimal)

**기대 결과**:
- HC: (a, b) ≈ (0, 0) — 균등 배치 optimal
- CVD sub-08/09: significant nonzero — cool-dense 방향 shift
- CVD sub-10: (a, b) ≈ HC (compensated profile)

**의미**:
1. Full center optimization(6–8 자유 파라미터)이 overfitting한 반면, 2-parameter 모델은 **nested CV에서 검증 가능**
2. (a, b) 파라미터가 **cone-opponent axis distortion에 직접 매핑**: a = L-M vs S tradeoff, b = warm-cool asymmetry
3. **Phase 2 연결**: (a, b)는 filter T_ψ의 초기값(initialization) 후보. CVD type(deutan/protan)에서 (a, b) 예측 가능하면 **closed-form filter** 도출:
   ```
   T_ψ(θ) = θ + a × sin(2θ) + b × cos(2θ)
   ```

**실행**:
```
위치:    analysis/future_phase1_forward_model/
Script:  scripts/fit_anisotropic_basis.py               ← TO CREATE
SLURM:   sbatch/run_anisotropic.sbatch                  ← TO CREATE
분석:    scripts/analyze_anisotropic.py                  ← TO CREATE
결과:    results/anisotropic_basis/
서버 예상: ~60분 (10 subjects × 4 ROIs × grid search)
```

---

#### Exp B3. Hierarchical FE (HC Prior + CVD Deviation)

**질문**: HC group prior로 CVD encoding을 정규화(regularize)할 수 있는가?

**방법**:
```
W_CVD = W̄_HC + ΔW
minimize ||Y_CVD - (W̄_HC + ΔW) @ C||² + λ × ||ΔW||²_F
```
- Step 1: HC group mean encoding weights W̄_HC 계산 (7 HC subjects, per-ROI optimal K)
- Step 2: 각 CVD subject에 대해 ΔW = W_CVD − W̄_HC를 ridge penalty로 fit
  - λ → ∞: CVD = pure HC model (CVD-specific geometry 무시)
  - λ → 0: CVD = standard ridge_gcv (prior 없이 자유 fitting)
- Step 3: λ를 inner LOCO-CV로 cross-validate

**기대 결과**:
- 중간 λ*에서 CVD LOCO 개선 (양 극단보다 나음)
- sub-10 (compensated): λ* 큼 (HC model이 잘 작동)
- sub-08/09: λ* 작음 (더 큰 deviation 필요)

**의미**:
1. CVD에 W를 scratch에서 fit하면 high variance (6 runs만으로). HC group을 **informative prior**로 활용하면 bias-variance tradeoff 개선
2. §9e에서 prior-based models이 실패했지만, 그때는 **SRM prior** 사용 (LOCO와 incompatible). 여기서는 **Procrustes-space HC mean** → 호환성 보장
3. Exp B2와 **직교**: B2는 basis (C) 변형, B3는 weights (W) 정규화. 독립적으로 또는 결합하여 사용 가능

**실행**:
```
위치:    analysis/future_phase1_forward_model/
Script:  scripts/fit_hierarchical_fe.py                 ← TO CREATE
SLURM:   sbatch/run_hierarchical.sbatch                 ← TO CREATE
분석:    scripts/analyze_hierarchical.py                 ← TO CREATE
결과:    results/hierarchical_fe/
서버 예상: ~45분
```

---

### Track B 평가 프레임워크 (5축)

Track B의 3개 모델(B1, B2, B3)을 아래 5개 축으로 동일 평가:

| 축 | 메트릭 | 구현 | 관련 실험 |
|----|--------|------|-----------|
| 1. 전체 정확도 | LOCO voxel_corr, MAE | 표준 LOCO pipeline | B1/B2/B3 각각 |
| 2. 원형 방향성 편향 | 색별 signed angular error | Exp A3 확장 | B2 (shift가 bias 감소?) |
| 3. 인접 혼동 구조 | Confusion probability matrix (8×8) | Exp A5 확장 | B3 (prior가 topology 보존?) |
| 4. 쌍별 잔차 기하 | 28-pair RDM Spearman | Exp A4 확장 | B2 + B3 모두 |
| 5. 기저-가족 비교 | Fixed FE-K vs B1 vs B2 vs B3 | HC paired t-test; CVD Crawford-Howell | 전체 비교 |

---

## Track C: Dimensionality & Population Organization

### 목적

RT-5 해결: CVD의 K-sensitivity가 **genuine dimensionality reduction (biology)**인지 **bias-variance tradeoff (model selection artifact)**인지 구분.

---

#### Exp C1. Eigenspectrum Decay Analysis

**질문**: CVD subjects가 더 가파른 eigenvalue decay를 보이는가? (fewer effective dimensions)

**방법**: Pospisil & Pillow (2024) broken power law: λᵢ = c × i^(−α)
- α_early (modes 1–10) vs α_late (modes 10–50) per subject per ROI
- HC vs CVD 비교: Welch t-test for α

**기대 결과**:

| Scenario | α_CVD vs α_HC | 해석 | Phase 2 함의 |
|----------|:-------------:|------|:------------:|
| **Biological** | α_CVD > α_HC | Genuine dimensionality reduction | Filter = lower-dim space |
| **Methodological** | α_CVD ≈ α_HC | Bias-variance tradeoff only | Filter = same space, 다른 tuning |

**실행**:
```
위치:    analysis/future_phase1_forward_model/
Script:  scripts/dimensionality/analyze_eigenspectrum_decay.py   ← READY
SLURM:   sbatch/run_dimensionality.sbatch (combined with C2)    ← READY
결과:    results/dimensionality/eigenspectrum/
```

#### Exp C2. MEME Dimensionality Estimator

**질문**: Unbiased effective dimensionality k*가 HC vs CVD에서 다른가?

**방법**: Marchenko-Pastur corrected eigenmoment matching
- Sample eigenvalues의 high-dimensional bias를 보정
- Rank k* = noise floor 이상 eigenvalues 수
- 검증: k*와 manual SRM k (V1=4, V2=4, V3=3, hV4=3) 및 FE optimal K 비교

**기대 결과**:
- k*_CVD < k*_HC → genuine (biology) → Track B에서 CVD-specific K 사용 정당화
- k*_CVD ≈ k*_HC → methodological → K-sensitivity는 bias-variance이지 retinal deficit이 아님

**실행**:
```
위치:    analysis/future_phase1_forward_model/
Script:  scripts/dimensionality/fit_meme_eigenspectrum.py       ← READY
SLURM:   sbatch/run_dimensionality.sbatch (C1과 순차 실행)      ← READY
결과:    results/dimensionality/meme/
```

#### Exp C3. Voxel Color Preference Mapping (Bannert Validation)

**질문**: CVD의 dimensionality reduction이 voxel-level reorganization으로 나타나는가?

**방법**: Bannert & Bartels (2025) KDE + softmax preference mapping
- 각 voxel: preferred color = max response across 8 colors
- Preference distribution: uniform(12.5%)로부터의 % deviation
- HC vs CVD 비교: 색별 preference 차이 검정

**기대 결과**:

| Scenario | Preference Distribution | 해석 | Phase 2 함의 |
|----------|:-----------------------:|------|:------------:|
| **No reorganization** | HC ≈ CVD | Stimulus-level distortion only | T_ψ(θ)만 필요 |
| **Reorganization** | Shifted peaks | Cortical plasticity | T_ψ(θ) + voxel remapping V |

**실행**:
```
위치:    analysis/future_phase1_forward_model/
Script:  scripts/population_organization/map_voxel_color_preference.py  ← READY
SLURM:   sbatch/run_voxel_preference.sbatch                            ← READY
결과:    results/population_organization/voxel_preference/
```

---

## Execution Timeline

### Phase 1: Server Jobs (Day 1–2) — 병렬 가능

| Job | 위치 | Node | 예상 시간 | 상태 |
|-----|------|:----:|:---------:|:----:|
| Exp A1 (FE-K MAE retry) | `phase3_decoder_comparing/model_comparison_validation/` | node2 | ~30분 | READY |
| Exp C1+C2 (Dimensionality) | `future_phase1_forward_model/` | node2 | ~20분 | READY |
| Exp C3 (Population org) | `future_phase1_forward_model/` | node2 | ~15분 | READY |

3개 job 동시 제출 가능 (node2 독립 실행).

```bash
# 1. 서버 업로드 — 3개 위치
# (a) FE-K MAE retry
scp analysis/phase3_decoder_comparing/model_comparison_validation/scripts/loco_fek_retry.py \
    analysis/phase3_decoder_comparing/model_comparison_validation/run_loco_fek_retry.sbatch \
    analysis/phase3_decoder_comparing/model_comparison_validation/scripts/analyze_loco_fek.py \
    haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation/

# (b) Dimensionality + Population org (이미 scripts/ 와 sbatch/ 에 존재하는 경우 해당 디렉토리만)
scp -r analysis/future_phase1_forward_model/scripts/dimensionality \
       analysis/future_phase1_forward_model/scripts/population_organization \
       analysis/future_phase1_forward_model/sbatch \
    haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model/

# 2. 병렬 제출
ssh haba6030@node3 << 'EOF'
cd /scratch/connectome/haba6030/colorBlind
sbatch analysis/phase2_decoder_comparing/model_comparison_validation/run_loco_fek_retry.sbatch
sbatch analysis/future_phase1_forward_model/sbatch/run_dimensionality.sbatch
sbatch analysis/future_phase1_forward_model/sbatch/run_voxel_preference.sbatch
EOF
```

### Phase 2: Local Analysis (Day 2–3) — 서버 불필요

| Analysis | 입력 (이미 로컬에 있음) | 결과 |
|----------|------------------------|------|
| Exp A3 (Signed bias) | `results/nested_adaptive/sub-*_V4_nested_adaptive.json` | `results/signed_bias/` |
| Exp A4 (28-pair heatmap) | `results/nested_adaptive/` + `results/validation/` | `results/pairwise_residual/` |
| Exp A5 (Confusion) | `results/nested_adaptive/` | `results/confusion_structure/` |
| Exp A6 (Cross-phase) | `results/nested_adaptive/` + `future_phase2_filter_optimization/pre_validation/results/` | `results/cross_phase/` |

> 모두 기존 다운로드된 nested LOCO JSON과 SRM prevalidation 결과 사용. `conda activate srm && python scripts/xxx.py`

### Phase 3: CVD Prediction Model (Day 3–7) — Server + Local

| Job | Node | 예상 시간 | Dependencies |
|-----|:----:|:---------:|:------------|
| Exp B1 (Subject-specific K) | node2 | ~45분 | None |
| Exp B2 (Anisotropic basis) | node2 | ~60분 | None |
| Exp B3 (Hierarchical FE) | node2 | ~45분 | None |
| Exp A2 (Basis anisotropy) | node2 | ~30분 | None |
| 5축 비교 분석 | local | ~1시간 | B1–B3 결과 |

B1, B2, B3, A2 모두 독립적 → 동시 제출 가능.

### Phase 4: Documentation & Gate (Day 7–8)

| Task | 설명 |
|------|------|
| RESULTS.md 업데이트 | Sections 4d–4g (새 실험 결과) |
| notion.md 미러링 | Korean 반영 |
| METHODS_RESULTS_SUMMARY 업데이트 | 전체 findings 통합 (현재 2026-03-09로 stale) |
| Phase 2 Gate Decision | GO/NO-GO (전체 evidence 기반) |

---

## Phase 2 Filter Design Handoff

### Filter T_ψ에 필요한 입력 (Track A + B에서 도출)

| Input | Source Experiment | Status |
|-------|:-----------------:|:------:|
| **Target color range** | §4c: θ ∈ [180°, 315°] (cool/S-axis) | DONE |
| **Distortion direction** | Exp A3 (signed circular bias) | TODO |
| **Pairwise geometry target** | Exp A4 + A6 (28-pair + cross-phase) | TODO |
| **Per-subject optimal K** | Exp B1 (subject-specific K) | TODO |
| **Channel shift parameters (a, b)** | Exp B2 (anisotropic basis) | TODO |
| **HC group prior W̄** | Exp B3 (hierarchical FE) | TODO |
| **Dimensionality** | Exp C1 + C2 (eigenspectrum + MEME) | TODO |
| **Voxel organization** | Exp C3 (Bannert validation) | TODO |

### Filter Architecture (Phase 2 PLAN.md)

```
T_ψ: θ → θ' = θ + ψ(θ)
where ψ(θ) = Σ_k [a_k sin(kθ) + b_k cos(kθ)]   (Fourier parameterization)
```

**Evaluation objective**:
```
minimize  E_θ [|| W_HC @ C(T_ψ(θ)) − Y_CVD(θ) ||²]
subject to  ||ψ||² < ε   (small correction)
```

**Connection**: Track B의 channel shift (a, b)는 ψ의 **1차 Fourier 초항** → 자연스러운 initialization.

---

## File Inventory

### 실행 가능 (READY)

| File | 위치 | 용도 |
|------|------|------|
| `loco_fek_retry.py` | `phase3_.../model_comparison_validation/scripts/` | Exp A1 |
| `run_loco_fek_retry.sbatch` | `phase3_.../model_comparison_validation/` | Exp A1 |
| `analyze_loco_fek.py` | `phase3_.../model_comparison_validation/scripts/` | Exp A1 분석 |
| `analyze_eigenspectrum_decay.py` | `future_phase1_.../scripts/dimensionality/` | Exp C1 |
| `fit_meme_eigenspectrum.py` | `future_phase1_.../scripts/dimensionality/` | Exp C2 |
| `run_dimensionality.sbatch` | `future_phase1_.../sbatch/` | Exp C1+C2 |
| `map_voxel_color_preference.py` | `future_phase1_.../scripts/population_organization/` | Exp C3 |
| `run_voxel_preference.sbatch` | `future_phase1_.../sbatch/` | Exp C3 |

### 생성 필요 (TO CREATE)

| File | 위치 (all `future_phase1_forward_model/`) | Track | Priority |
|------|------|:-----:|:--------:|
| `scripts/signed_circular_bias.py` | 로컬 실행 | A3 | HIGH |
| `scripts/pairwise_residual_heatmap.py` | 로컬 실행 | A4 | HIGH |
| `scripts/confusion_structure.py` | 로컬 실행 | A5 | HIGH |
| `scripts/cross_phase_correlation.py` | 로컬 실행 | A6 | MEDIUM |
| `scripts/basis_anisotropy_test.py` | 서버 실행 | A2 | MEDIUM |
| `scripts/subject_k_selection.py` | 서버 실행 | B1 | HIGH |
| `scripts/fit_anisotropic_basis.py` | 서버 실행 | B2 | HIGH |
| `scripts/fit_hierarchical_fe.py` | 서버 실행 | B3 | MEDIUM |
| `scripts/analyze_*.py` (각 실험용) | 로컬 실행 | — | 서버 결과 후 |
| `sbatch/run_*.sbatch` (서버 job용) | 서버 | — | scripts과 동시 |

---

## Decision Gates

### Gate 1: Track A 완료 후 (Residual Analysis)

**질문**: Residual HC-CVD gap이 Phase 2 filter 설계에 충분히 특성화되었는가?

**기준**:
- [ ] Cool colors에 대한 signed bias 방향 식별 (Exp A3)
- [ ] 28-pair geometry가 SRM prevalidation과 수렴 (r > 0.4) (Exp A6)
- [ ] 최소 2/3 CVD subjects가 일관된 cool-axis distortion pattern (Exp A4)

### Gate 2: Track B 완료 후 (CVD Prediction Model)

**질문**: Personalized model이 CVD LOCO를 개선하는가?

**기준**:
- [ ] Track B 모델 중 최소 1개가 CVD hV4 LOCO 개선 (Crawford-Howell p < 0.10 for any subject)
- [ ] 개선이 cool colors에서 specifically 발생 (전체만이 아닌)
- [ ] HC performance 유지 또는 개선 (HC에 cost 없음)

### Gate 3: Phase 2 GO/NO-GO (전체 Track 완료 후)

| Condition | Threshold | Status |
|-----------|-----------|:------:|
| hV4 HC encoder validated | perm p < 0.05 | MET (p=0.026) |
| S-axis distortion characterized | Direction + magnitude | Gate 1 |
| CVD prediction model available | Any B1/B2/B3 improvement | Gate 2 |
| Dimensionality resolved | RT-5 answered | Track C |

**GO**: Gate 1 + 3 충족 시. Gate 2는 desirable but not blocking.
**NO-GO**: Gate 1 실패 (일관된 residual pattern 없음) → FE pipeline 재검토.

---

## Key Statistics Reference (현재 확정)

### hV4 FE-3 Per-Color LOCO (§4c)

| Color | θ | HC M | CVD M | d | p |
|-------|-----|:----:|:-----:|:---:|:---:|
| red | 0° | +0.353 | +0.310 | +0.18 | 0.81 |
| orange | 45° | +0.246 | +0.502 | −0.94 | 0.22 |
| yellow | 90° | +0.135 | +0.213 | −0.24 | 0.70 |
| green | 135° | +0.107 | +0.055 | +0.13 | 0.85 |
| cyan | 180° | −0.008 | +0.157 | −0.35 | 0.66 |
| **blue** | **225°** | **+0.349** | **+0.025** | **+1.37** | **0.046*** |
| purple | 270° | +0.283 | −0.124 | +1.54 | 0.060 |
| magenta | 315° | +0.171 | −0.211 | +1.19 | 0.127 |

### HC-CVD Gap by K (§4b)

| ROI | FE-6 d (p) | FE-K d (p) | Reduction |
|-----|:----------:|:----------:|:---------:|
| V1 | 2.01 (0.021) | 0.44 (0.581) | −78% |
| V2 | 2.25 (0.022) | 1.80 (0.067) | −20% |
| V3 | 0.17 (0.819) | 0.18 (0.843) | — |
| hV4 | 1.36 (0.169) | 0.63 (0.342) | −54% |

### CVD Individual Profiles (§4c, hV4 FE-3)

| Subject | Type | Warm Mean | Cool Mean |
|---------|------|:---------:|:---------:|
| sub-08 | deutan | +0.227 | −0.058 |
| sub-09 | protan | +0.340 | −0.197 |
| sub-10 | deutan | +0.244 | +0.140 |
| HC mean | — | +0.210 | +0.199 |

### Cross-Phase Convergence (§4c)

| Finding | SRM (Phase 2) | FE (Phase F1) |
|---------|---------------|---------------|
| Significant group pair | V2 blue-purple p=0.042 | hV4 blue p=0.046 |
| Deficit pattern | green-blue compression (all 3 CVD) | blue/purple lowest CVD LOCO |
| Compensation | sub-10 HC-like crossnobis | sub-10 positive cool LOCO |

---

## Appendix: Research Question Mapping

| SRQ | Question | Track |
|-----|----------|:-----:|
| SRQ3 | Forward encoding model로 held-out color response 예측 가능한가? | §5–7 (DONE) |
| SRQ3a | HC와 CVD 간 prediction 차이는? | §4b–4c (DONE) + Track A (residual) + Track B (model) |
| SRQ4 | Stimulus-space filter가 CVD prediction을 개선하는가? | Phase 2 (BLOCKED on Track A handoff) |

> **SRQ3**: 답변 완료 (hV4 YES, V1/V2 NO).
> **SRQ3a**: 부분 답변 (K-dependent + axis-specific). Track A–B가 완전한 답변을 제공.
> **SRQ4**: Track A의 filter input specification + Track B의 channel shift가 Phase 2 설계의 기반.
