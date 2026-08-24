# U2 — β_c 부호 강건성: 실행 전 확정 문서

**확정일**: 2026-08-10 · **상태**: 실행 전 확정. **결과를 본 뒤에는 이 문서를 고치지 않는다.**

> 선행: `analysis/phase0_preprocessing/HMC_REANALYSIS_PRESPEC.md §6` 이 이 확인을 "재산출 후
> 최우선 확인 항목" 으로 이미 지정했다. 새 post-hoc 분석이 아니라 **그때 미실시로 남은 항목의
> 이행**이다. `docs/PAPER/REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md §4` 표의 U2.

---

## 1. 질문

**하나뿐이다.**

> 움직임 회귀 arm 의 신경 추정치로 왜곡 모형을 다시 적합해도
> **deutan $\hat\beta_c < 0$, protan $\hat\beta_c > 0$** 라는 participant-specific direction 이 유지되는가?

## 2. 왜 이것이 필요한가

논문의 sensitivity chain 이 한 칸 짧다.

```
geometry robustness  ──✔ 검증됨 (§S2 disparity 3 arm, §S13 색 특이성 3 arm, §S2 LOCO 3 arm)
        ↓
fitted distortion β  ──✘ 전처리 축 미검증        ← 여기
        ↓
production filter    ──  β 에서 해석적으로 유도
```

현행 원고가 주장하는 $\hat\beta_c$ 안정성은 **HC 재표집**과 **LOO 재적합**에 대한 것이다
(`results_v4.tex:111-112`, `discussion_v3.tex:44`). 전처리에 대한 주장은 없다. 신경 종점은
전부 3 arm 을 통과했는데 **그 종점에서 유도되는 생산 파라미터만 통과하지 않은** 상태이므로,
리뷰어가 물을 자리가 그대로 남아 있다.

## 3. 기준값 (배포본)

| 참가자 | 선정 조합 | $(\hat\beta_s, \hat\beta_c)$ | combo index |
|---|---|---|---|
| sub-08 deutan | $\gamma_{\rm OY} + L_{\rm RDM}^{(V2)}$ (`γOY\|RDMV2\|noLOCO`) | $(6^\circ, -42^\circ)$ | **15** / 71 |
| sub-09 protan | $\gamma_{\rm all} + L_{\rm RDM}^{(V1)}$ (`γALL\|RDMV1\|noLOCO`) | $(2^\circ, +24^\circ)$ | **9** / 11 |

## 4. 고정 사항 — 바꾸는 것은 amplitude root 하나

| 항목 | 값 |
|---|---|
| **바꾸는 것** | `COLORBLIND_AMP_ROOT` → `…/visualization/full_dataset_C010_motreg` |
| loss 조합 | **위 표의 선정 조합만.** 재탐색 금지 |
| 격자 | `BS_GRID` × `BC_GRID` (β_s 0–50° 26점 × β_c −50–50° 51점, 2°) |
| PCA | `K_PCA = 6` |
| resample | `N_RESAMPLES = 300`, `RNG_SEED = 42`, `SUBSET_SIZE = 5` |
| FE basis | `ROI_K` 전 ROI 6 (FE-6 uniform) |
| 심리물리 원자 $\gamma$ | 행동 데이터이므로 **전처리와 무관, 불변** |

**따라서 움직이는 것은 $L_{\rm RDM}$ 하나다.** 이 검사는 "신경항만 바꿨을 때 argmin 이 어디로
가는가" 로 해석된다.

**하지 않는 것**

- 조합 전수 탐색 재실행 (= selection-rule reformulation, `CLAUDE.md` Policy 위반)
- gate 재적용, ROI 재선정, 격자 변경
- 배포 필터 변경 — 세션 2 촬영이 이미 끝났으므로 **변경 불가**

## 5. 실행

```bash
conda activate srm
cd analysis/phase5_filter_optimization
export COLORBLIND_AMP_ROOT=$PWD/../phase1_procrustes_decoding/results/visualization/full_dataset_C010_motreg
python scripts/s10b_v6_pca_rdm.py --subject sub-08 --combo-start 15 --combo-end 16
python scripts/s10b_v6_pca_rdm.py --subject sub-09 --combo-start 9  --combo-end 10
```

출력: `results/s10_inclusion/s10b_v6_pca_rdm_results_sub-0{8,9}_c{15-16,09-10}.json`
(canonical 결과 파일은 접미사가 달라 덮이지 않는다.)

`scripts/neural_loss.py` 에 `COLORBLIND_AMP_ROOT` env override 를 추가했다. 기본값은 발표
경로 그대로이므로 기존 재현 경로는 불변이다.

## 6. 판정 규칙 (실행 전 확정)

**주 판정 = $\hat\beta_c$ 의 부호.** 크기는 판정에 쓰지 않는다 (2성분 모형은 12/12 절대복구
실패로 이미 descriptive embedding 으로 제한되어 있다).

| 결과 | 결론 | 원고 처리 |
|---|---|---|
| **A.** deutan $-$ / protan $+$ 유지 | motion robustness 가 filter-generation chain 까지 이어진다 | §S16 에 한 문장 추가 |
| **B.** deutan 만 유지 | 현행 identifiability 결과와 정합 (protan 은 이미 basis-dependent). deutan 강, protan 모호 | Discussion 의 protan ambiguity 문장을 **전처리 축까지 확장** |
| **C.** 둘 다 크게 변함 | 부호 대비의 전처리 강건성을 **주장하지 않는다** | `robust individualized distortion estimate` 류 표현 금지. `descriptive embedding derived from the primary estimates` 로 제한 |

**어느 분기에서도 불변인 것**: 배포 필터 파라미터, 그리고 provenance 서술("파라미터는 세션 1
데이터에서 추정되어 세션 2 이전에 동결되었다"). 동결 시점이 검증 세션보다 앞선다는 성질은
전처리를 바꿔도 유지된다.

**두 arm 의 값을 나란히 보고한다. 유리한 쪽만 싣지 않는다.**

## 7. 제안 원고 — 분기 A 인 경우 (§S16)

> Refitting the same loss combination on the motion-regression arm, with every other
> element of the procedure held fixed, returned $(\hat\beta_s, \hat\beta_c) = (\cdot,\cdot)$
> for the deutan participant and $(\cdot,\cdot)$ for the protan participant. The sign of
> $\hat\beta_c$, which carries the contrast between the two fits, is preserved. The
> psychophysical atoms do not depend on preprocessing, so the neural term is the only
> component that differs between the two arms.

분기 B·C 의 문안은 결과를 본 뒤 이 문서가 아니라 `REVISION_PLAN_PRESUBMISSION_2026-08-10.md`
§9 에 작성한다.
