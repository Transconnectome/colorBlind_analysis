# 디코더 비교 감사 기록 — 2026-08-07

> 부록 S10(Comparison with alternative decoders) 작성 과정에서 커밋된 산출물을 전수 대조한 결과.
> **이 문서의 모든 수치는 `.json`에서 직접 읽었다.** 요약 마크다운은 근거로 쓰지 않았다.
> 대조 결과 기존 계획 문서 두 건이 사실과 달랐으므로, 같은 조사를 반복하지 않도록 남긴다.

---

## 0. 무엇이 어디에 반영되었나

| 확인 사항 | 반영 위치 |
|---|---|
| 6개 디코더 LORO·LOCO 표 | 부록 **S10**, Table S7·S8 |
| 판독 provenance, 제외 계열, K 복원 | S10 헤더 주석 |
| nested 정렬 대조 | 부록 **S8** (Cross-validation procedures) 말미 |
| 교차피험자 일반화 정정 | 본문 `results_v4.tex:31`, 부록 **S19** |
| `Appendix~A` 오지시 해소 | `methods_v2.tex:149` → `Supplementary~\S S10` |

---

## 1. 실제 모델 목록 — 계획 문서 두 건이 서로 달랐고 둘 다 부정확

디스크의 `config.json`과 결과 트리에 존재하는 모델 키는 다음이 전부다.

- **LORO** (`results/loro/{raw,procrustes,srm}/`): `LDA`, `Ridge`, `KernelRidge`, `SVM`, `MLP`, `ForwardEncoding`
- **LOCO** (`results/loco_srm/`): 위 6종 + `HybridMLP`, `HybridSVR`
- **LOCO** (`results/loco/{raw,procrustes,srm}/`): 6종. `srm` 결과가 `loco_srm/`과 공유 모델에 대해 비트 단위 일치

**`TODO_decoder_comparison.md`가 기각 4종으로 적은 `PopVec` / `RidgeEnc` / `GaussML` / `RidgeReg`는 모델 키로 존재하지 않는다.** 실제 이름은 `FE_PopVec` 등이고, **디코더가 아니라 forward encoding의 readout 변형**이다. 수치는 `analysis/METHODS_phase2b_decoders.md`(마크다운)에만 있고 **커밋된 `.json`/`.csv`가 없다.** 따라서 부록에 수치를 실을 수 없다.

---

## 2. 채택 모델은 분류에서 1위가 아니다

LORO 8-way exact accuracy, SRM 공간, HC 평균 (n=7). 출처 `results/loro/srm/sub-{01..09}_performance_raw.json`, `results.srm.{ROI}.{model}[fold].acc_exact`의 6 fold 평균.

| ROI | LDA | SVM | ForwardEncoding |
|---|---|---|---|
| V1 | **0.878** | 0.777 | 0.542 |
| V2 | **0.830** | 0.759 | 0.545 |
| V3 | **0.726** | 0.631 | 0.449 |
| hV4 | **0.658** | 0.598 | 0.423 |

**방어는 보간에서 이루어진다.** LOCO adjacent accuracy, chance = 3/8 = 0.375. hV4에서 forward encoding만 chance를 넘는다.

| hV4 | HC 평균 |
|---|---|
| **ForwardEncoding** | **0.470** |
| LDA | 0.280 |
| SVM | 0.253 |
| MLP | 0.250 (상수) |
| Ridge / KernelRidge | 0.000 |

근거는 모형 형태다. 6채널 튜닝 표상은 학습에서 본 적 없는 색을 평가할 수 있고, 7개 라벨로 학습한 분류기는 여덟 번째 색에 대응하는 출력 단위가 없다.

→ **"forward encoding이 6모델 비교의 승자"로 쓰면 표에 반박당한다.** S10은 분류·보간을 분리해 서술한다.

---

## 3. 신뢰할 수 없는 행 2종

- `KernelRidge` — LOCO adjacent accuracy가 전 피험자·전 ROI·전 정렬에서 **정확히 0.000**
- `MLP` — SRM 공간 LOCO에서 **정확히 chance 값**(V1·V2 0.375, V3·hV4 0.250)이고 피험자 간 SD = 0. 상수 예측의 서명

표에는 남기되 경쟁 점수로 서술하지 않는다(선택적 보고 회피).

---

## 4. correlation readout은 이 비교의 결과가 아니다

| 사건 | 시점 | 근거 |
|---|---|---|
| `argmax(correlation(...))` 코드 존재 | 2026-01-27 | commit `b3ce74d` |
| 분석 계획에 명시 (`plans_decoder.md`) | 2026-02-17 | commit `1634142`, "Model 6: Forward Encoding Model (from phase1)" |
| LOCO 실행 | 2026-02-22 | config timestamp |
| LORO 실행 | 2026-02-26 | 〃 |
| `FE_PopVec` 등 대안 readout 등장 | 2026-02-23 | commit `cc6eba2` |

**정확한 서술** — Phase-1 forward model에서 물려받아 이후 검증했다. "비교해서 선택했다"가 아니다. `methods_v2.tex:149`를 그렇게 고쳤다.

한계: 사전등록 문서는 없다. `plans_decoder.md`는 이후에도 편집된 내부 문서이므로, 확정된 것은 "2026-02-17 시점에 그 줄이 있었다"까지다.

---

## 5. ⚠️ 판독 구현이 두 갈래다

| 파일 | 판독 방식 |
|---|---|
| `future_phase1_forward_model/scripts/loco_canonical.py:104` | 360-hue FE basis에서 디코드 후 `round(pv/45)` = 최근접 자극 hue |
| `phase3_decoder_comparing/.../loro_baseline.py:428-429` | 360-hue를 거치지 않고 **8개 템플릿에 직접 argmax** |

45° 간격에서 "최근접 자극 hue 할당"과 "±22.5° 빈"은 정의상 같은 연산이므로 `methods_v2.tex:149`와 부록 S9의 서술은 정합한다. 그러나 **두 구현이 일반적으로 동일한 결과를 내지는 않는다** — 360-hue 상관 프로파일의 argmax가 속한 빈이 8-템플릿 상관의 최댓값과 항상 일치하지는 않기 때문이다.

논문 수치는 `loco_canonical.py` 경로에서 나오고, S10의 디코더 비교표만 `loro_baseline.py` 경로다. **S10을 인용할 때 이 차이를 잊지 말 것.**

---

## 6. 기타 확인 사항

- **`dim_k`가 모든 phase-3 config에서 `null`이다.** SRM을 적합하지 않고 미리 계산된 `amplitudes_srm.npy`를 로드하기 때문. K는 배열 shape에서 복원했다 — V1 4, V2 4, V3 3, hV4 3
- **데이터셋 토큰은 C010** — 모든 config의 `dataset_name`, `baseline_dir`이 `full_dataset_C010`
- **앙상블 3종은 폐기됨** — commit `3ec8e51`, `a825a7d` (2026-02-26). `loco_ensemble/`의 config 헤더에 `FE_Ensemble`이 남아 있으나 results 트리에는 없다(stale 헤더)
- **`HybridMLP`/`HybridSVR`은 LOCO에서만 실행** — LORO 결과가 없어 두 표를 나란히 놓을 수 없다
- **sub-07 hV4의 16복셀 문제는 전파되지 않는다** — SRM 투영 후 K=3이라 well-posed. 전 파일에서 NaN 0건
- **`loro_baseline.py` docstring이 8모델을 나열하나 LORO는 6모델만 실행** — docstring이 stale, config가 정본

---

## 7. nested Procrustes 대조 (부록 S8 근거)

**존재한다.** `analysis/phase3_decoder_comparing/results/nested_procrustes/`, `results/focused_nested/`. 구동 `scripts/run_nested_procrustes.sbatch`, 구현 `loro_baseline.py:131-170` (`procrustes_nested_fold`).

LORO acc_exact, 10 피험자, V1–hV4 pooled.

| 모델 | 고정 run-1 | nested | Δ |
|---|---|---|---|
| **ForwardEncoding** | 0.5448 | 0.5781 | **+3.3 pp** |
| LDA | 0.7583 | 0.8432 | +8.5 pp |
| SVM | 0.6849 | 0.8625 | +17.8 pp |
| KernelRidge | 0.3318 | 0.5130 | +18.1 pp |

**두 가지 단서.**

1. "essentially unchanged"는 **FE에만** 성립한다. 논문의 LORO 종점이 FE이므로 범위 한정은 자연스럽다.
2. `procrustes_nested_fold`가 회전 재추정과 **동시에** 정렬 표적을 run-1에서 학습 run 평균으로 바꾼다(`loro_baseline.py:157`). 따라서 nesting만 격리한 대조가 아니다. 전 모델이 상승한 이유도 아마 이것이다.

**누출 논증은 여전히 성립한다.** 누출이 canonical 값을 부풀렸다면 nested가 더 낮아야 하는데 방향이 반대다. S8은 이 범위로 서술한다.

---

## 8. 교차피험자 일반화 — 논문 서술 3건 정정

출처 `results/loro/srm/validation/cross_subject_generalization.json`, 생성 `scripts/validation_tests.py:477-676`.

| 항목 | 기존 논문 서술 | 실제 |
|---|---|---|
| 모델 | forward encoding | **LDA**였다. FE는 U=228.5, p=0.076으로 값도 방향도 다름 |
| 표본 | 21 vs 14 **pairs** | **28 vs 12 subject × ROI cells.** HC 7 LOSO fold × 4 ROI = 28, CVD 3 × 4 ROI = 12 |
| p | 0.668 | LDA + sub-10 포함일 때만 나오는 값 |

**sub-10을 제외하고 ForwardEncoding으로 재산출한 값** (셀 순서는 `validation_tests.py:519, 605`가 ROI 바깥·CVD 안쪽 루프임을 확인해 확정):

| 구성 | HC→HC | HC→CVD | U | p | r_rb |
|---|---|---|---|---|---|
| FE, n=8 (sub-10 제외) | 0.526 | 0.432 | 163.5 | **.052** | +0.46 |
| LDA, n=8 (참고) | 0.635 | 0.641 | 113.5 | .970 | +0.01 |

→ **"no HC–CVD difference"는 성립하지 않는다.** 본문은 이 검정을 "차이없음"의 근거에서 빼고, 대신 (a) 피험자 내 above-chance, (b) 개별 LORO Crawford–Howell(8검정 전부 p ≥ .095), (c) HC 학습 모델의 CVD 전이가 chance 초과(평균 0.432, `t(7)=6.51, p<.001`)로 재구성했다.

### hV4 "single-case test" p = 0.142

**Crawford–Howell이 아니었다.** hV4 LORO LDA 정확도에 대한 Mann–Whitney(HC n=7 대 CVD n=2)다. `docs/PAPER/Figures/fig2_notes.md:22-24`가 명시한다. `docs/PAPER/repro/MAP.md:12`가 이를 Crawford–Howell로 잘못 매핑해 두었다 — **MAP.md 정정 필요.**

실제 Crawford–Howell(ForwardEncoding, 양측, df=6)로 재산출한 값을 논문에 실었다.

| ROI | HC 평균±SD | sub-08 d_cc (p) | sub-09 d_cc (p) |
|---|---|---|---|
| V1 | 0.542±0.106 | +0.59 (.600) | +0.79 (.488) |
| V2 | 0.545±0.077 | −1.11 (.337) | −1.38 (.243) |
| V3 | 0.449±0.065 | −1.15 (.323) | −2.12 (.095) |
| hV4 | 0.423±0.072 | −0.95 (.407) | −0.95 (.407) |

**주의** — 유의에 도달한 것은 없으나 `|d_cc|`가 최대 2.12다. "차이없음"으로 강하게 쓰면 검정력 부족을 유의성 부재로 바꿔 읽는 것이 된다. 본문은 유의성만 진술한다.

---

## 9. 커밋된 수치가 없는 항목 (인용 금지)

- `FE_PopVec` / `FE_RidgeEnc` / `FE_GaussML` / `FE_RidgeReg` 비교 수치 — `METHODS_phase2b_decoders.md`에만 존재
- Mann–Whitney "21 vs 14 pairs" — 어떤 파일에도 없다. 전사 오류로 판단
- Crawford–Howell p = 0.142 — 어떤 파일에도 없다. 위와 동일

---

## 10. 후속 정리 대상

- [ ] `docs/PAPER/repro/MAP.md:12` — p=0.142를 Crawford–Howell로 매핑한 항목 정정
- [ ] `analysis/METHODS_phase2b_decoders.md` — 커밋된 산출물이 없는 수치가 인용 가능한 것처럼 보이는 구조. 출처 없음 표기 필요
- [ ] `loro_baseline.py` docstring의 stale 모델 목록
- [ ] `loco_ensemble/` config 헤더의 stale `FE_Ensemble` 키
