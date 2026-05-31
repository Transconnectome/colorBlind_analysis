# Redteam 최종 종합 — 2026-05-28

문서 수정 없음. Exp 1–9 결과 통합. Closure 본문 권장 수정 명시.

---

## 1. 비판별 최종 verdict

| # | 원안 severity | Exp 후 verdict | 핵심 수정 사유 |
|---|---|---|---|
| 1 | Fatal | **Mixed — candidate별로 다름** | Round 4 (JND-aware) 에서 (6, −42) 는 식별성 통과, (38, −10) / (2, +24) 는 fail 지속 |
| 2 | Fatal until resolved | **Resolved** | Active 경로 frozen 사용 없음 (archive 완료); provenance section 추가만 권장 |
| 3 | Severe | **Moderate** | Sub-08 PCA 92% majority concordance; sub-09 PCA pipeline metric 최우수; mechanism interpretation 만 atom-conditional |
| 4 | Severe | **Mixed** | (38, −10) 은 Step 4-only emergence + Round 4 fail; *동시에* γ_ALL behav-only saturation 의 neural-resolved 해. 두 framing 다 사실 |
| 5 | Fatal framing | 변동 없음 | 어휘 retract 필수 |

## 2. Candidate별 재분류 (가장 중요한 결론)

| Candidate | Step 3 단독 rank | Step 4 emergence? | Round 4 식별성 | Atom robust? | 최종 분류 |
|---|---:|---|---|---|---|
| **S08-βc-dom (6, −42)** | top-3 (LOCO-off) | No (Step 3 baseline) | **PASS** (sign 100%, ±10° 100%) | PCA·SRM-cos·SRM-dis 모두 β_s 양·β_c 음 quadrant | **Primary identifiable candidate** ✓ |
| S08-βs-dom (38, −10) | 16/22 (LOCO-off) | Yes (cycle6b new_candidates) | FAIL (Round 4 sign 0%) | PCA β_s magnitude dependent | Step 4-emergent descriptive fit only |
| S09-βc-rot (2, +24) | 1/4 (LOCO-off) | No | FAIL (Round 4 sign 40%) | PCA outlier vs SRM family on combo | PCA-atom-conditional descriptive fit |

→ **(6, −42) 는 closure 의 진짜 winner**. 식별성 통과 + Step 3 자연 emergence + cross-atom mechanism class robust.

## 3. 실험별 핵심 발견 1-2 줄 정리

### Exp 1 — A13 forward audit
- **수치 차이 거대** (S08-βs-dom: cos(raw, frozen)=−0.65, 8-vec sign-match 2/8)
- **활성 코드 경로에 frozen 사용 없음** — Phase B v6 fit / Round 3 / 시각화 모두 raw forward
- 비판 #2 **resolved** by archiving

### Exp 2 — Round 3 noise-floor excess test (JND-blind)
- 3 candidate 모두 β_c 축 GT 방향 식별 fail
- S08-βs-dom: GT=−10, recovered +26 (부호 반대); fit ±10° hit = 0%, null ±10° hit = 42%
- S09-βc-rot: GT=+24, recovered −10 (부호 반대); MW p=0.56 (null 과 통계적 구별 안 됨)

### Exp 3 — Sub-09 PCA vs SRM disagreement (single combo)
- γALL+RDMV1 combo: PCA 88% 가 (2, +24); SRM-cos 79% 가 (32, 0); SRM-dis 97% 가 (32, 0)
- 2 SRM family 가 같은 attractor 로 수렴 → PCA 가 single combo 에서 outlier

### Exp 4 — Step 4 (38, −10) rescue audit
- `cycle6b_extended_composite_sub-08.json` 자체가 `new_candidates_keys` 에 (38, −10) 명시
- Step 3 단독 ranking 에서는 46위/71 (전체) 또는 16위/22 (LOCO-off)
- Step 4 의 12/47 scheme (γ_focal≥2 AND γ_all=1) 에서만 surface

### Exp 5 — PCA vs SRM full-pipeline comparison
- **Sub-08**: 어느 atom 도 모든 metric 에서 우월하지 않음 (PCA: IQR best; SRM-cos: test_loss best; SRM-dis: bdy best)
- **Sub-09**: PCA 가 모든 metric 에서 최우수 (test_loss −1.54 vs −0.85; IQR 0.71 vs 0.91; bdy 0% vs 13%) → **PCA canonical 선택의 객관적 정당화 근거 존재**
- Sub-08 βc-dom (6, −42): PCA·SRM-cos 거의 일치, SRM-dis 는 magnitude 절반 (−24) but **same quadrant**

### Exp 6 — LOCO-excluded + behav-only baseline
- **LOCO 제외 시** sub-08 top-1 = γOY+RDMV2 (6, −42) test_loss=−2.36
- (38, −10) 은 LOCO-off ranking 에서도 16/22 → Step 3 단독 metric 으로 underperform
- **Behav-only γ_ALL**: (β_s=+50, β_c=−36) bdy=70% saturated; +RDM_V1 추가 시 β_c=−36 → −10 으로 +26 shift, bdy=70% → 0%
- 즉 (38, −10) 은 **γ_ALL behav-only grid-saturation 의 neural-resolved endpoint** — Step 4 rescue 면서 동시에 자연스러운 stability minimum

### Exp 7 — Round 4 JND-aware identifiability (★ 가장 결정적)
- **S08-βc-dom (6, −42)**: Round 3 fail → Round 4 **PASS** (sign 100%, ±10° 100%, recovery −48±4)
- S08-βs-dom (38, −10): Round 4 도 fail (β_c +14, 부호 반대)
- S09-βc-rot (2, +24): Round 4 도 marginal fail (β_c −6, 부호 반대, 40% within ±10°)
- Null GT 에서 β_s positive bias (+18~+41) 여전 → β_s 축 만의 procedure-level bias 는 존재

### Exp 8 — Sub-08 cross-atom global concordance
- 36 cells × 3 atoms: **3-way quadrant agreement 75% (27/36)**
- PCA 가 majority quadrant 에 포함되는 비율 **92% (33/36)** — *PCA 는 sub-08 global outlier 아님*
- test_loss rank correlation: PCA vs SRM-cos ρ=0.68, PCA vs SRM-dis ρ=0.57 — moderate-strong
- Sub-08 에서 PCA 가 *outlier* 인 cell 은 2/36 (γALL+RDMV3, γ_+RDMV2)

### Exp 9 — Stimulus-space filter convergence
- 3 candidate 의 **pre-image (역필터) δθ 벡터** 가 매우 다름
- S08-βs-dom vs S08-βc-dom: pre-image cosine = **−0.18** (거의 반대), sign-match 4/8, max|Δfilter|=67°
- S08-βs-dom vs S09-βc-rot: cos +0.52
- S08-βc-dom vs S09-βc-rot: cos +0.66
- **함의**: sub-08 두 candidate 는 stimulus-space 에서 *완전히 다른 필터* → Phase 3 행동 실험으로 *구별 가능*. 즉 tiebreaker plan 이 작동할 수 있음.

## 4. Closure 본문 수정 권장 (3 단계)

### 단계 1: 가장 중요한 reframe — (6, −42) 를 primary 로 promote

현재 closure §5.1 은 sub-08 의 두 candidate (38, −10) 과 (6, −42) 를 *parallel reporting*. Exp 7 결과를 반영하면:

**개정 권장 표현**:
> "Sub-08 has two descriptive fits at distinct mechanism types. **The (β_s=6, β_c=−42) cortical confusion-axis candidate (βc-dom) is identifiability-validated**: under JND-aware multi-point recovery (Round 4, Exp 7), the candidate's β_c GT is recovered with sign-match 100% and ±10°-precision 100% (n=30 outer resamples). **The (β_s=38, β_c=−10) S-cone-shift-dominant candidate (βs-dom) is a Step 4 raw-weight emergence and does not pass JND-aware identifiability** (β_c recovered with opposite sign in both Round 3 and Round 4). We therefore report βs-dom as a *neural-stabilized descriptive endpoint of the γ_ALL behavioral signal*, not as an identified mechanism. Pre-image vectors differ in stimulus space (cosine −0.18), so Phase 3 can discriminate the two filter forms behaviorally."

### 단계 2: Sub-09 mechanism atom-conditional disclosure

현재 closure §A.6 의 L9 권고 strengthen:

**개정 권장 표현**:
> "Sub-09's βc-rot candidate (β_s=2, β_c=+24) is **PCA-RDM atom-conditional**. SRM-cosine and SRM-disparity atom families both converge on (β_s=32, β_c=0) for the same combo. Whilst PCA-RDM yields lower test_loss (−1.54 vs −0.85) and smaller IQR (0.71 vs 0.91) on the sub-09 pipeline — supporting PCA as the canonical atom for this subject — the mechanism interpretation (cortical confusion-axis rotation primary) is **not robust to atom choice**. JND-aware Round 4 identifiability for sub-09 βc-rot fails (β_c sign 40%, ±10°-precision 40%), so we report the candidate as a *plausible descriptive fit under PCA-RDM atom, requiring behavioral validation*."

### 단계 3: 어휘 retract + provenance section

- 본문 전체 "filter form" → "candidate descriptive parameterization at the fit point"
- Methods 에 한 줄 추가: "All Phase B v6 fits, Round 3/4 identifiability checks, and final stimulus synthesis use `scripts/two_comp.py:forward_2comp` (raw nominal-θ). The `forward_models/two_component.py` (frozen H_BASE) variant has been archived (2026-05-19) and is not part of the closure pipeline."

## 5. 사용자 결정이 필요한 항목

1. **(6, −42) 를 sub-08 primary 로 promote, (38, −10) 을 descriptive endpoint 로 강등** 에 동의하시는지? Closure 가 현재는 parallel reporting 인데 Round 4 결과는 (6, −42) 우선을 시사.

2. **Sub-09 의 SRM (32, 0) 을 alternative descriptive fit 으로 본문에 보고할 것인지**? PCA 가 pipeline metric 우수하므로 canonical 선택 정당화 가능하나, mechanism interpretation 의 atom-dependence 는 disclose 필요.

3. **Round 4 JND-aware identifiability 검증을 closure §5.2 에 official 추가** 할지 (현재는 Round 3 만 보고). 이 추가 만으로 비판 #1 의 fatal severity 가 (6, −42) 한정 mixed 로 격하 가능.

4. **Phase 3 자극을 (38, −10) vs (6, −42) tiebreaker design 으로 진행** 할지? Exp 9 결과로 두 filter 가 stimulus-space 에서 cos=−0.18 으로 강하게 distinguishable 함을 확인. 이 디자인이면 단일 행동 실험으로 *두 가설을 모두 falsifiable*.

---

## 6. Files (이번 redteam audit 전체)

| File | Role |
|---|---|
| `2026-05-28.md` | 원래 redteam report (5 criticisms) |
| `2026-05-28_experiments.md` | Exp 1-4 결과 + 비판 갱신 |
| `2026-05-28_final_synthesis.md` | 본 문서 (Exp 1-9 통합) |
| `exp1_a13_forward_audit.{py,json}` | Forward 함수 audit |
| `exp2_round3_excess_test.{py,json}` | Round 3 noise-floor excess test |
| `exp3_sub09_atom_disagreement.{py,json}` | Sub-09 PCA vs SRM single combo |
| `exp4_step4_rescue_audit.{py,json}` | Step 4 (38, −10) rescue |
| `exp5_atom_pipeline_compare.{py,json}` | PCA vs SRM full-pipeline (sub-08 + sub-09) |
| `exp6_loco_excluded_behav_only.{py,json}` | LOCO 제외 + behav-only vs neural |
| `exp7_round4_jnd_aware.{py,json}` | Round 4 JND-aware identifiability |
| `exp8_sub08_cross_atom_global.{py,json}` | Sub-08 cross-atom quadrant concordance |
| `exp9_stimulus_space_convergence.{py,json}` | Stimulus-space filter pre-image convergence |
