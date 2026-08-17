# Supplementary 개정 — 완료 기록 및 잔여

> rev.4 · 2026-08-07 마감 기준.
> rev.1–rev.3의 계획 목록은 전부 소진되었으므로 **완료 기록 + 잔여**로 대체한다.
> 정본 = `docs/PAPER/REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md`.
> 디코더 조사 = `DECODER_AUDIT_2026-08-07.md`.

---

## 1. 부록 최종 구성 (S1–S21, 본문 서술 순)

> **2026-08-17 정정.** 이 표는 S1–S19 로 적혀 있었으나 실제 파일은 **S1–S21** 이다. 이후 `S11. Alignment Robustness for the Within-Subject Readouts` 와 `S15. Session-1 Hue-Discrimination Thresholds` 두 절이 삽입되었고, 그 결과 구 S11 이하가 전부 밀렸다. 아래 표는 `Supplementary/supplementary.tex` 의 실제 heading 을 그대로 옮긴 것이다.

단일 파일 `Supplementary/supplementary.tex`. `main.tex`가 `\section{Supplementary Methods}` 아래에 `\input` 한다.

| # | 섹션 (실제 heading) | 구 표 번호 |
|---|---|---|
| S1 | Confound Regression and Temporal Filtering | S1 |
| S2 | Uncorrected acquisition artifacts (§ 안에 `Motion sensitivity analysis` 문단 포함) | S2 |
| S3 | Image Orientation Initialization | S3 |
| S4 | Quality Control | S4 |
| S5 | Mean Activation Analysis | S5 |
| S6 | Dimensionality Selection (K-Selection) | S6 |
| S7 | Generalized Cross-Validation for Ridge Regression | S7 |
| S8 | Cross-Validation Procedures | S8 |
| S9 | Evaluation Metrics | S9 |
| S10 | Comparison with alternative decoders | S10 |
| **S11** | **Alignment Robustness for the Within-Subject Readouts** | **신설 — 구 표에 없음** |
| S12 | Leave-One-Out Consistent Disparity Estimation | S11 |
| S13 | Validity of the geometric comparison | S12 |
| S14 | Alignment-independent checks on the disparity measure | S13 |
| **S15** | **Session-1 Hue-Discrimination Thresholds** | **신설 — 구 표에 없음** |
| S16 | Comparison with Retinal-Family Distortion Models | S14 |
| S17 | HC leave-one-out magnitude-anchor distribution | S15 |
| S18 | Identifiability checks | S16 |
| S19 | Filter-evaluation session: design and comparator | S17 |
| S20 | Statistical Analysis | S18 |
| S21 | Effect Sizes for Single-Case Comparisons | S19 |

**본문 참조 재검증 (2026-08-17, 17건 전수)** — `Results/results_v4.tex`, `Methods/methods_v2.tex`, `Supplementary/supplementary.tex` 의 `\S S…` 를 전부 뽑아 문맥과 실제 절 제목을 대조했다. **17/17 정상.** 참조는 이미 신 번호를 쓰고 있었고, stale 한 것은 이 표뿐이었다. 원고 수정 불요.

| 위치 | 참조 | 대조 결과 |
|---|---|---|
| results:29 | S11 | SRM 정렬 공간 재현 → `Alignment Robustness` ✔ |
| results:31, methods:189 | S21 | 단일사례 효과크기 → `Effect Sizes` ✔ |
| results:88 | S15 | 8쌍 임계값 → `Session-1 Hue-Discrimination Thresholds` ✔ |
| results:140, 142 | S18 | 식별성·6개 사전지정 검정 → `Identifiability checks` ✔ |
| results:190, 212, 235 | S19 | 2차 세션·run-matched → `Filter-evaluation session` ✔ |
| methods:76 ×2 | S1 | confound regression 미적용·FD → `Confound Regression` ✔ |
| methods:76 | S2 | 움직임 회귀 재산출 → S2 내 `Motion sensitivity analysis` 문단 ✔ |
| methods:149 | S10 | 대체 디코더 5종 → `Comparison with alternative decoders` ✔ |
| methods:152 | S7 | GCV → `Generalized Cross-Validation` ✔ |
| methods:200 | S12 | disparity 두 추정 → `Leave-One-Out Consistent Disparity` ✔ |
| methods:203 | S5 | 전체 반응 크기 → `Mean Activation Analysis` ✔ |
| supp:909 | S11 | within-subject readout 대비 → `Alignment Robustness` ✔ |

**주의 — 신설 절 번호.** `REVISION_PLAN_PRESUBMISSION_2026-08-10.md` H 항목은 β_c 부호 강건성을 "§S16 신설"로 적었으나 S16 은 이미 `Comparison with Retinal-Family Distortion Models` 이다. **신설 번호는 S22 여야 한다.**

---

## 2. 신설 4건

| 섹션 | 근거 | 비고 |
|---|---|---|
| **S2** 움직임·미보정 아티팩트 | 정본 §S17 | 민감도 arm = 움직임 회귀(재샘플링 0회) + 순환이동 대조 |
| **S10** 대체 디코더 비교 | `TODO_decoder_comparison.md` | `methods_v2.tex:149`의 `Appendix~A` 오지시 해소 |
| **S12** 기하 비교의 타당성 | 정본 §S18 | 동결 투영 순열. 35셀 BH-FDR 산출 |
| **S13** 정렬 독립 삼각검증 | `TODO_supplementary_additions.md` S-B | **sub-10 제외 n=9로 재산출** |

---

## 3. 사실관계 정정 (전부 원산출물 대조)

| 항목 | 기존 | 정정 |
|---|---|---|
| 자극 기하 4곳 | `10°`, `3.0°`, `7.8°` | 실행 코드가 `units='pix'` → **500 px / 96 px / 260 px / 100 px / 240 px** |
| 교차 일반화 모델 | forward encoding | 실제로는 LDA → **FE로 재산출** |
| 교차 일반화 표본 | 21 vs 14 pairs | **28 vs 8 subject × ROI cells** (sub-10 제외) |
| 교차 일반화 p | 0.668 | **0.052**, r_rb = 0.46 |
| hV4 단일사례 검정 | Crawford–Howell p=0.142 | 실제로는 Mann–Whitney → **진짜 CH로 재산출**, d_cc = −0.95, p = .407 |
| 색 특이성 유의 셀 수 | 15 (정본 산문) | **16** (JSON 직접 계수) |
| 추정량 정책 | all-HC primary, LOSO는 sensitivity | **all-HC = 파이프라인 공간, LOSO = 추론 검정** |
| GCV 적용 범위 | 미기재 | **encoding 전용**임을 S7 첫 문장에 명시 |
| S1 모션 서술 | "estimated via rigid-body realignment" | 추정만 하고 **보정·회귀 모두 미적용** |

---

## 4. 정본 반영

R1–R5, M1–M5 적용 완료. R6는 Figure 4에서 ΔRDM 패널 제거 + 캡션 재작성으로 완료.

**Figure 4** = `fig3_geometry_r6`. disparity 전용 단일 패널, 별표는 **LOSO 기준**(sub-09 V1만 `*`), 캡션에서 결론 문장과 p값 제거.

> 파이프라인 그림(`fig3_workflow`) box 2에 ΔRDM 히트맵을 넣는 것은 **선택 사항으로 종결**. box 2가 이미 `Representational ΔRDM direction (L_RDM)`을 항목으로 명시하고 시각적으로 포화 상태다. 에셋은 `Figures/fig3_assets/box2_delta_rdm_r6.{pdf,png,svg}`에 보관.

---

## 5. 형식

| # | 항목 | 결과 |
|---|---|---|
| F1 | Supplementary 그림 번호 | 각 float **내부**에서 재정의. apa6 `man`은 전 float을 문서 끝으로 미루므로 섹션 경계 재정의는 본문 그림까지 오염시킨다 |
| F3 | `alvaro2022`, `gomezrobledo2018` | 이미 등록되어 있었음 |
| F4 | Back matter | CRediT·이해관계·감사·데이터 가용성 4절을 `\todo{}` 공란으로 삽입 |
| F5 | 섹션 계층 | S 번호 전부 `\subsection*`, 하위 제목 7개는 `\paragraph` |
| F6 | 지표 명칭 | `eight-way classification accuracy`로 8곳 통일 |
| — | F2 (미인용 앵커) | 사용자 결정으로 **폐기** |

S10(구 SRM residuals)은 내용이 전부 중복이라 삭제하고, 직교 제약의 기하적 귀결 한 문장만 Methods §SRM으로 흡수했다.

---

## 6. 폐기

`TODO_HLLM.md`(행동 통계 상세), `TODO_robustness_supplement.md`(forward-model 강건성). 조건부 항목으로 분류 후 폐기. 파일은 그대로 둔다.

---

## 7. 잔여

| # | 항목 | 시점 |
|---|---|---|
| 1 | **F4 back matter 기입** | 제출 직전 |
| 2 | **데이터 공개 방침 결정** — 저장소 기탁(OSF/OpenNeuro) 대 요청 시 제공. Methods 문장과 Data availability 절을 함께 고쳐야 한다 | 제출 전 |
| 3 | `DECODER_AUDIT` §10의 코드측 정리 3건 (`METHODS_phase2b_decoders.md` 출처 표기, `loro_baseline.py` docstring, `loco_ensemble/` stale 키) | 코드 공개 전 |

`repro/MAP.md` E1.2·E1.3 정정은 2026-08-07 완료.
