# SD4H_draft_v6.1.tex — Closure-Alignment Revision Plan

- **Date**: 2026-06-01
- **Purpose**: `SD4H_draft_v6.1.tex` 를 `analysis/phase5_filter_optimization/PIPELINE_2_CLOSURE.md` (2026-06-01) 에 정렬. SD4H@ICML reviewer (Rating 3 Accept / Confidence 2) 피드백 동시 반영.
- **Status**: 방향 확정 (DIRECTION LOCKED) — .tex 편집은 미실행. 다음 세션에서 §"실행 체크리스트" 순서로 진행.
- **User decisions (this session)**:
  1. Fit scope = **γ+RDM 그대로** (closure 후보와 정확히 일치; neural-only 대신 선택 → §0.1 circularity disclosure 의무 발생)
  2. 증거 프레임 = **descriptive-only reframe 동의** (bold `p_perm` 헤드라인 제거)
  3. 이 문서까지만 (제안 저장), 편집은 별도 지시 시

---

## 0. 핵심 진단 — "숫자 불일치"가 아니라 연쇄(cascade) 불일치

v6.1 드래프트는 closure 이전 상태. loss 하나를 바꾸면 모델 선정 → 증거 체계 → 생리 해석이 **순차적으로** 따라 움직인다. 부분 교체 시 내적 모순 발생.

```
[loss 변경]  →  [모델 선정 flip]  →  [증거 프레임 flip]  →  [생리 해석 제거]
 composite     R+C/Machado →         8! perm 유의 →          Δλ/g 절대값 해석
 z-score+      2-Component           descriptive-only        → mechanism class만
 PCA-RDM       (R+C는 "구조적 부적합   (null battery 0/3
 categorical    reference"로 강등)     dual-pass)
```

### 검증된 canary (편집 전 전체 숫자 재검증 필요의 증거)
- 드래프트 §3.2 (L243): Sub-09 2-Component = **(β_s=6, β_c=−22)**
- 실제 `results/s10_inclusion/s10b_v6_pca_rdm_results_sub-09.json` (cell `γALL|RDMV1|noLOCO`, model `2comp`): **(β_s=2, β_c=+24)**, IQR (0,0) deterministic
- → 부호까지 반대인 stale 값. 드래프트 숫자 전반이 closure 이전이라는 증거.

---

## 1. 입장은 안 바뀐다 — 드래프트 prose 가 이탈해 있었다 (중요 framing)

프로젝트의 문서화된 입장은 줄곧 **descriptive + 행동검증 대기**였다. reframe 은 *입장 변경*이 아니라 드래프트 prose 를 그 입장으로 *정렬*하는 것.

근거:
- `phase5_filter_optimization/CLAUDE.md §0`: "Specificity claim은 selection criterion이 아니다 … descriptive reporting으로만 … p-value/FPR claim은 보류" (Cycle 9~13 확정)
- `§0.1` (2026-05-16): paper 에 P2a/P1 primary endpoint 보고 금지, "별도 수집된 behavioral test … TO BE COLLECTED" 가 유일한 paper-reportable validation
- closure L587: "selection rule 변경 없음 ('specificity 는 selection criterion 아님' 정책 유지)"
- closure L707: "Phase 3 행동 실험이 sole verification path"

**드래프트 prose 의 이탈 지점** (제거 대상):
- Table 1 의 bold `p_perm = 0.005** / 0.018*`
- §3.1 "predicts … **significantly** above the exact 8! null"
- §2.4 "A valid model **must reach significance (p < 0.05)**" ← significance 를 *선정 게이트*로 격상, §0 와 정면 충돌
- Fig 2 caption "achieve **statistically significant** prediction"

**Characterization**: "더 강한 주장에서 retreat" 가 **아니라** "처음부터 견지한 descriptive 입장으로 prose 정렬". 논문 서사도 더 방어적 — circularity·noise-floor 를 알기에 descriptive 로 보고하고 별도 행동검증을 verification path 로 설계했다는 rigor 서사.

---

## 2. 반드시 바꿔야 하는 것 (프로젝트 §0 정책상 비협상)

### 2.1 모델 선정 flip — 가장 노출된 줄은 Sub-09
- 드래프트 L220–222: "purely retinal model is **sufficient** … g=0 at optimum" (Sub-09 Machado 1-DOF)
- Closure (RQ1, §5.1): Sub-09 는 **cortical** βc-rot (2, +24); R+C 는 **saturate** (g=2.95, bdy=41%) = retinal **부적합**
- → 출판될 주장의 **정반대 inversion**. 최우선 수정.
- Sub-08: R+C(primary) → 2-Component **두 parallel 후보** (βs-dom (+38,−10) γ_all+RDM_V1, βc-dom (+6,−42) γ_OY+RDM_V2). R+C 는 RQ1 대로 "구조적 DOF 부족 → reference only" 강등.

### 2.2 eq:rc (L163–168) 내부 모순
- 드래프트 식: `o' = o_0 + (1+g)(o_Δλ−o_0)`, g=0 순수 Machado, g=−1 완전보상. 본문은 **g=+2.25** 보고 → 드래프트 식대로면 3.25× 증폭.
- Closure 식 (model table): `δθ_RC = (2−g)·δθ_Machado`, g=1 무보상, g=2 완전보상 → g=2.25 면 −0.25× **반전**. **같은 숫자, 정반대 물리.**
- → Closure 파라미터화로 교체 + 재유도.

### 2.3 eq:loss (L182–186) 교체 ← "loss 변경"의 핵심
- 현재: `L = L_vuln + 0.5 L_rank + 0.2 L_rdm + 0.1 L_smooth`
- Closure canonical (`s10b_v6_pca_rdm.py`): **z-score grid-relative composite** ( γ JND-z² atoms + **45° categorical PCA-RDM atom** + LOCO ). 선정 = HC subset resample (N=300) 의 `test_loss_median` ASC + strict 7-fold LOO (`s17_hc_loo.py`).
  - composite: `z_sum = Σ zscore_grid(atom_grids); comp = z_sum / sqrt(n_atoms); fit_param = argmin(comp)`
  - RDM atom: per-HC mean pattern → PCA top-K=6 → 8×8 correlation RDM; forward 는 `p_i = round(perceived[i]/45) % 8` 45° lookup; loss = `1 − cos(ΔRDM_sim, ΔRDM_obs)`

### 2.4 증거 프레임 flip — "유의성" → "식별가능성 특성화"
- 제거: bold `p_perm` 헤드라인 (8! label perm). closure 에 대응하는 깨끗한 p값 **없음**.
- 대체 (closure null battery):
  - Exp17 averaged-surface loss depth: REAL CVD 2.1×/3.9×/5.5× deeper than synthetic HC null → **signal 존재**
  - Exp18C Method C: GT=(0,+24) **exact recovery** → categorical identifiability
  - Test 1 param recovery: f10° < 0.30 **FAIL** (3/3) → 절대 magnitude 식별 불가
  - Test 2a (0,0): f10°_origin = 0/140 → pipeline noise floor **~20°/25°** per axis
  - Test 2c label-perm: **0/3 pass** (p=0.17–0.87)
  - Exp22: 1/3 single-source marginal (S08-βc-dom Bonferroni p=0.0149)
- 결론: **descriptive-only, mechanism class (부호 quadrant) 만 robust, 절대 magnitude 식별 불가, 행동검증이 adjudicator.** "증거 없음" 아님.

### 2.5 생리학적 절대값 해석 제거
- L221/L370 "Δλ=13.5nm matches moderate protanomaly", L226 "g reflects amplification" → closure L528/L588 금지, L346 g-vs-literature 비교 부정.
- Appendix 의 "physiological ranges" 방어 기둥 → closure 실제 근거 (Exp17 loss-depth, Exp18C, sign-quadrant robustness) 로 교체.

---

## 3. γ+RDM 선택의 선결 조건 — §0.1 circularity disclosure (필수)

closure 후보의 γ 는 **per-pair JND** (color-naming P2a/P1 과 다른 행동 측정). §0.1 의 circularity 금지는 본래 P2a/P1 대상.

- **OK 조건**: γ(JND) 는 *fit 입력*, validation 은 *별도 수집될 Phase 3 discrimination* (다른 데이터) → 비순환. 단 논문이 같은 JND 로 "fit 이 행동 distortion 을 **예측**한다" 주장 시 **즉시 circular**.
- **필수 disclosure** (Methods 에 명시): "fit 에 behavioral JND 가 입력으로 포함됨; JND-in-fit 을 validation 근거로 재사용하지 않음. 비순환 검증 부담은 neural RDM atom + Phase 3 가 진다."
- B 선택의 가격표 (neural-only A 였다면 불필요했던 의무).

---

## 4. 리뷰어 지적 → closure 자산 매핑 (정렬하며 잃지 말 것)

| 리뷰어 weakness/suggestion | closure 자산 / 대응 |
|---|---|
| **Reproducibility** (key impl details: interpolation error 계산, alignment 절차) | closure Step 1–3 spec + `s10b_v6_pca_rdm.py` file:line → **Methods 에 algorithm box 추가**. 가장 직접적 응답. |
| **Sample N=3** | Theme B 프레이밍 + 정직하게 "**N=2 fit-recovered + 1 null (Sub-10)**", "3 successes" 아님 |
| **ML-accessibility** | LOCO = leave-one-**class**-out (표현 manifold 연속성 probe) vs LORO = 표준 CV; inverse inference = pre-image. (closure 미지원 — 순수 프레이밍) |

리뷰어가 칭찬한 contribution (distortion framing, individual-level, IVP novelty, low-dim inference) 은 reframe 후에도 모두 유지 — IVP 가 γ+RDM 에서 LOCO atom 으로 살아있음.

---

## 5. 섹션별 구체 edit 타깃

| 위치 | 현재 | 수정 |
|---|---|---|
| Abstract (L65–74) | "retinal+cortical converge on detection, diverge on correction" | best retinal model 이 structurally inadequate; mechanism-class robust, magnitude non-identifiable; behavioral validation adjudicates |
| Table 1 (L205–217) | Sub-08 R+C / Sub-09 Machado | Sub-08 2-Comp ×2 (βs-dom + βc-dom) / Sub-09 2-Comp βc-rot (2,+24); R+C 는 "insufficiency reference" 행 |
| §3.1 본문 (L219–230) | Machado/R+C 서사 + Δλ 생리 매칭 | 2-Component 서사 + descriptive percentile |
| §3.2 (L243) | Sub-09 (6, **−22**) ← stale/오부호 | **(2, +24)** (검증 완료) |
| §3.2 (L244) | "comparable fit quality" R+C vs 2-comp | RQ1 대로 "R+C 구조적 부적합" — 더 강한 주장 |
| eq:rc (L163–168) | (1+g) 파라미터화 | closure `(2−g)·δθ_Machado` |
| eq:loss (L182–186) | L_vuln+0.5 rank+0.2 rdm+0.1 smooth | z-score composite + 45° categorical PCA-RDM + test_loss_median 선정 |
| §2.4 (L178–189) | 8! perm 유의 게이트 ("must reach significance") | composite/test_loss 선정 + null battery 요약 (significance 게이트 제거) |
| Methods (신규) | — | algorithm box (Step 1–3 spec, reproducibility 응답) + γ-in-fit circularity disclosure 1줄 |
| Appendix HC specificity (§A.2) | FPR 표 (15/21 sig) | closure 4-test battery 로 업그레이드 |
| §2.1 (L126–128) | "3 CVD" | "N=2 fit-recovered + 1 null" 명시 |
| Conclusion (L274) | "converge on detection but diverge on correction" | descriptive reframe 정렬 |

---

## 6. 실행 체크리스트 (다음 세션 — 편집 지시 시 이 순서)

1. **모든 숫자 결과 JSON 에서 재검증** (Sub-09 (2,+24) 확인 완료; Sub-08 βs-dom·βc-dom, R+C g값, test_loss/IQR, mode share 등 나머지 — `results/s10_inclusion/s10b_v6_pca_rdm_results_sub-08.json`, `sub-09.json`)
2. eq:rc → closure `(2−g)·δθ_Machado` 재유도
3. eq:loss → z-score composite + 45° categorical PCA-RDM + test_loss_median 선정
4. Table 1 / §3.1 / §3.2 → 2-Component 중심 재작성 (Sub-08 두 parallel, Sub-09 cortical βc-rot, R+C reference)
5. §2.4 + Appendix → 8! perm 게이트를 4-test null battery 로 교체 (reproducibility 응답)
6. γ-in-fit circularity disclosure 1줄 삽입 (§3 선결 조건)
7. Sample 서술 → "N=2 fit-recovered + 1 null"
8. ML-accessibility 패스 (LOCO=leave-one-class-out vs LORO, inverse=pre-image)
9. Abstract/Conclusion reframe

---

## 7. 참조 파일

| 파일 | 역할 |
|---|---|
| `analysis/phase5_filter_optimization/PIPELINE_2_CLOSURE.md` | ground truth — 5-step pipeline, final candidates, limitations, null battery |
| `analysis/phase5_filter_optimization/closure.md` | 4-test verification 요약 (user-facing) |
| `analysis/phase5_filter_optimization/CLAUDE.md` §0, §0.1 | descriptive-only / specificity-not-criterion / circularity 정책 |
| `results/s10_inclusion/s10b_v6_pca_rdm_results_{sub-08,sub-09}.json` | Phase B v6 PCA canonical fit 출력 (숫자 재검증 소스) |
| `scripts/s10b_v6_pca_rdm.py` | canonical fitter (algorithm box 소스) |
| `scripts/s17_hc_loo.py` | strict 7-fold HC LOO |
| `results/redteam/exp17*, exp18*, exp22*, param_recovery*, null_*` | null battery 증거 |
