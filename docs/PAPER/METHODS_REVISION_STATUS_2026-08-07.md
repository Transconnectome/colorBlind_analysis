# Methods 문단별 개정 현황 (2026-08-07)

> 진행 방식: 문단 단위로 **코드 대조 → 수정안 제안 → 확인 → 반영 → 컴파일 검증**.
> 서술 제약: 문장 길이 억제, 삽입구 최소화(특히 `:` `;`), academic vocabulary,
> rigorous verbs, direct expressions, American spelling, **부정 표현 최소화**.
> 지배 문서: [`REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md`](REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md)
> 규칙 스캔 결과: [`revision_report_2026-08-07_methods.md`](revision_report_2026-08-07_methods.md)

**현재 빌드**: `exit 0` · fatal 0 · undefined 0 · BibTeX warning 0 · 83 pages

---

## 1. 완료 문단 — Methods 전 절 대조 완료

### 1a. 전반부 (서술·보고 요건 중심)

| 행 | 절 | 주요 변경 | 상태 |
|---|---|---|---|
| 16 | 개관 | First/Second/Finally 유지, ΔRDM 제거, Fig 1C 인용으로 그림 순서 역전 해소 | ✅ |
| 37 | Participants | SNUIRB 기관명·헬싱키·연령범위(20–27), 아형 판정 방법 | ✅ |
| 44 | 자극 | `isoluminant` 제거, BOLDscreen 32 UHD + 공장보정, 픽셀 단위 선언 | ✅ |
| 46, 48 | 과제 | 두 문단 분할, 버튼박스, 500 px 원반 | ✅ |
| 55 | 심리물리 도입 | 실시 환경 신설 (Liquid Retina XDR, Apple XDR preset, 실내조명) | ✅ |
| 58 | JND 절차 | 좌우 동시 제시·자기조절 시간·catch trial 부재 | ✅ |
| 60 | 색쌍 선정 | 축 기반 서술(S-cone 축 = yellow–purple), 사전지정 진술 | ✅ |
| 67 | 8AFC | 시행 흐름·격자·옵션 재배열·timeout·64시행 | ✅ |
| 74 | MRI 획득 | **FA 75°→70° 정정**, **코일 64채널 정정**, MPRAGE·GRAPPA 2·PE R→L·48 mm 슬랩·필드맵 | ✅ |
| 76 | 전처리 | FSL 6.0.5.1 / FreeSurfer 7.2.0, MNI 정식명칭, SDC 미적용, FD 꼬리 16.2% | ✅ |
| 106 | ROI 정의 | 중복 허용 정책 명시 | ✅ |
| 119 | GLM | 2단계 FIR + HRF 유도 명시 | ✅ |
| 126 | Procrustes | 8×8 색공간 회전임을 명시 (복셀 정체성 불변) | ✅ |
| 133 | SRM | k 선정 3지표 랭킹 절차 | ✅ |

### 1b. 후반부 (코드 대조 중심 — 2026-08-07 신규)

| 행 | 절 | 코드 대조로 정정한 것 | 근거 파일 |
|---|---|---|---|
| 146–152 | Forward encoding | GCV α가 **복셀별이 아니라 스칼라 1개** | `utils_forward_model.py:445` |
| 172–189 | Two decoding schemes | LORO/LOCO 직접 서술, **hV4 primary 정당화 신설**, **chance 3/8 → 0.25**, `Hedges' d` → $d_{cc}$ | `decode_hue`, `loco_canonical.py:103` |
| 196–202 | Representational geometry | disparity 전용화(ΔRDM 이관), **fold 평균 비대칭** 신설, §S7 포인터 | `rerun_loo_consistent.py:92,287` |
| 226–246 | Candidate models | R+C 부정표현 해소, 2-comp의 **Results 순환 인용 제거** | `two_comp.py:45-48` |
| 256–263 | $L_\gamma$ | **rank discordance → 표준화 제곱오차**, $\hat\gamma = \bar\gamma_{\rm HC}(d_{\rm phys}/d_{\rm perc})$ 신설, γ_subtype 후보쌍 정정 | `s10b_v6_pca_rdm.py:74-119` |
| 266–279 | ΔRDM / $L_{\rm RDM}$ | ΔRDM 도입 §손실로 이관, **식의 `/2` 제거**, **45° 스냅** 명시 | `s10b_v6_pca_rdm.py:186-195` |
| 282–289 | $L_{\rm LOCO}$ | **HC-trained W → CVD 자체 W**, **MSE → `mean(1-ρ)`** | `neural_loss.py:87-149` |
| 292 | Composite loss | **신설** — 격자 z-표준화 후 합산 ÷ $\sqrt{n_a}$ | `s10b_v6_pca_rdm.py:242,605` |
| 305–313 | Parameter selection | Gate 1 **양방향** 확정, **collapse guard** 신설, 순위 기준 2개 명시 | `s10a_precondition.py:209`, `CLAUDE.md §2.5` |
| 323–334 | Identifiability | 두괄식 4소문단, **`trial labels` → `color labels`**, **`full pipeline` → grid search**, AR(1) 노이즈, `donor` 제거 | `param_recovery_voxel.py`, `null_label_permutation.py` |
| 341–343 | Stimulus-space filter | **`1e-3°` → `xtol=1e-9`**, ±60° 탐색, **역상 미보장 + 전방대입 검증** | `exp2_compute_preimage.py:30-60` |
| 350–354 | Filter evaluation | forward-tuning **Spearman → Pearson**, 대상을 예측/실측 복셀 패턴으로 정정 | `exp2_hc_likeness.py:53-98` |
| 361 | Reproducibility | sklearn **유지** + `pedregosa2011` 인용, **시드 42/31337/27182** | 전수 grep |

### 1c. 부록 · 타 섹션

| | 상태 |
|---|---|
| S1 | ✅ 필드맵 문단 (취득·`IntendedFor`·미소비·R→L 왜곡 잔존) |
| **S17 / S18** | ✅ 통합 `Supplementary/supplementary.tex`로 이관, 구 파일 `Supplementary/archive/`(gitignore) |
| §S6 | ✅ **sklearn `RidgeCV` 허위 귀속 삭제** → SVD 자체 구현 + 실제 α 격자 |
| §S1 | ✅ `hedges1985` 인용 이동 (Hedges' g 실사용 위치) |
| `tab:loco_decoders` | ✅ **디코더별 chance 분리** (연속 0.25 / 8-라벨 0.375) |
| Results | ✅ chance 파급 4곳, **`results_v4.tex:220` 주장 역전 처리** |
| Discussion 한계 | ✅ 아노말로스코프·휘도 미측정 문장, **LOCO 미선정 → 지표 정의 논증** 재작성 |
| Figures | ✅ `fig2_loro_loco`, `fig8_filter_eval`, `figS16_adjacc_saturation` 재생성 |
| bibliography | ✅ `walther2016` 신규 등록, `pedregosa2011` 복원, DOI 5건 정정 |

용어 일괄 교체 `behavioral` → `psychophysical` 29곳 ✅

---

## 2. 미결

### U-A. 용어 일관성 3건 (Serious) — **신규**

개정 과정에서 유입된 불일치. [리포트 §4.1](revision_report_2026-08-07_methods.md) 참조.

| 용어 | 현재 | 조치 |
|---|---|---|
| `control participant` 3건 | Methods만. 나머지 원고는 `HC` | → `HC participant` |
| `region` 12건 vs `ROI` 6건 | Results는 `ROI` 17건 | → `ROI` 통일 |
| `per-subject filter` 1건 | Results·Discussion은 `individualized filter` | → `individualized filter` |

### U-B. §23 "No results in Methods" 2건 (Serious, 의도적)

| 위치 | 내용 | 판단 필요 |
|---|---|---|
| L279 | PCA↔SRM 일치도 $r = 0.77$–$0.89$ (계획 M5) | 유지 / Results / §S |
| L343 | 역상 8/8이 $10^{-3}$° 이내 | 유지 / §S |

둘 다 **방법 선택의 정당화**여서 이관 시 근거가 소실된다. 유지 권고.

### U-C. 긴 문장 2건 (Minor)

L253 (36어, em-dash 2 + 세미콜론), L266 (42어). 분할 지점은 리포트 §1.5.

### U-D. disparity fold 평균 비대칭 — 반영 완료

CVD는 7-fold 평균, HC는 fold당 1값. Crawford–Howell 분모 팽창 → 상측 검정 보수적.
`methods_v2.tex:200`에 반영됨.

---

## 3. 디페이싱 및 정합 안정성 — 검정 완료 (2026-08-07)

2차 세션 T1w가 디페이싱되지 않은 불일치가 무해한지 검정했다.
**절차** (SLURM job 164976, 31분, FreeSurfer 7.2.0 + FSL `bet2`): 2차 T1w 원본과 `mri_deface`
처리본 각각에 `bet2` → `mri_coreg --regheader` 를 돌려 BOLD→T1w 변환(LTA)을 비교.

**결과 1 — 디페이싱으로 인한 이동**

| | 평균 | 중앙값 | p95 | 최대 |
|---|---|---|---|---|
| sub-08 | 1.95 mm | 1.91 | 3.25 | 3.93 |
| sub-09 | 9.43 mm | 9.43 | 15.82 | 20.83 |

LTA 가 `LINEAR_VOX_TO_VOX` 이고 T1w 복셀이 비등방($1.0 \times 0.5 \times 0.5$ mm)이므로,
BOLD 볼륨(96×96×24) 격자를 통과시킨 뒤 축별 복셀 크기를 곱해 mm 로 환산했다.

**결과 2 — 런 간 변동성 (기준자)**

| | 런 수 | 평균 | 범위 |
|---|---|---|---|
| sub-08 1차 | 6 | 1.78 mm | 0.44–3.65 |
| sub-08 2차 | 8 | 4.18 mm | 0.71–9.83 |
| sub-09 1차 | 6 | 0.93 mm | 0.24–1.60 |
| sub-09 2차 | 8 | 3.02 mm | 0.53–9.05 |

**판정** — 디페이싱 이동량 / 런간 변동 = sub-08 **0.5배**, sub-09 **3.1배**.
디페이싱이 특별히 정합을 깨뜨리는 것이 아니라, 이 자료의 BOLD→T1w 정합 자체가 1–4 mm 규모로
잡음이 있다. 24슬라이스 후두엽 BOLD 를 전뇌 T1w 에 MI 로 맞추는 문제라 비용면이 얕고 다봉성이다.
`mri_coreg` 최종 파라미터에서 sub-09 는 x축 회전이 $+5.75^\circ$(원본) 대 $-1.29^\circ$(디페이싱)로
갈린다. 둘 다 그럴듯한 소량 회전이므로 서로 다른 국소 최적해에 안착한 것이다.

**권고 — 분석 입력을 디페이싱하지 않는다.** 공유용 사본에만 적용한다.
(앞서 권고한 "제자리 디페이싱"은 이 위험을 과소평가한 것이었고, 검정 결과로 철회했다.)

---

## 4. 정정한 사실 오류 누계

### 4a. 전반부 (보고 요건)

| 항목 | 기존 | 정정 | 근거 |
|---|---|---|---|
| 플립각 | $75^\circ$ | $70^\circ$ | SNUBIC 스캔로그 |
| 코일 | BioMatrix 3T coils | 64-channel head coil | 동일 |
| SDC | 미언급 | 미적용 명시 | 파이프라인에 `fugue`/`topup` 0건 |
| §S17 참조 | HMC 재샘플링 arm | 움직임 회귀 arm | HMC arm 신뢰도 붕괴 |
| `isoluminant` | 3곳 | 전부 제거 | $L^*$ 정합은 표준 관찰자 기준 |
| `Ishihara post-hoc` | 8AFC 문단 | 삭제 | 검색 0건 |
| BIDS 변환 | ezBIDS 단일 | 1차 ezBIDS / 2차 dcm2bids 3.2.0 | JSON 프로베넌스 |

### 4b. 후반부 (코드 대조)

| 항목 | 성격 | Results 파급 |
|---|---|---|
| adjacent accuracy chance `3/8` → `0.25` | 귀무값 오류 | **주장 1건 역전** + 그림 3개 |
| GCV α `per voxel` → 스칼라 | 추정 절차 | 없음 |
| §S6 sklearn 귀속 | 허위 귀속 | 없음 |
| `Hedges' d` → $d_{cc}$ | 효과크기 정체 | 없음 |
| `L_RDM` `/2` | 코드 불일치 | 없음 (z-정규화가 소거) |
| ΔRDM 45° 스냅 / composite z-표준화 | 미기재 | 없음 |
| `L_γ` 손실 형태 + 예측 모형 | **손실 정의 오류** | 없음 |
| `L_LOCO` W 출처 + 손실 형태 | **손실 정의 오류** | 없음 |
| Gate 1 `signed d` → `abs(d)` | 규칙 진술 | 없음 |
| collapse guard / 순위 기준 | 미기재 | 없음 |
| `trial labels`, `full pipeline` | 검정 절차 | 없음 |
| Brent 허용오차 / 역상 미보장 | 수치 절차 | 없음 |
| forward-tuning Spearman → Pearson | 지표 정의 | 없음 |
| seed 42 단일 → 3종 | 재현성 | 없음 |
| `walther2016` 미등록 | 서지 | 없음 |

**C010 오해 정정** — `preprocess_tests.md:36-45`의 C-플래그 3비트는 (고역통과, 1차 drift, 2차 drift)다.
`C010 = 1차 drift 회귀자만`이며 HMC/STC/SDC와 무관하다.

---

## 5. 다음

1. **U-A 용어 3건 일괄 치환** (기계적, 위험 낮음)
2. **U-B 2건 사용자 판정**
3. **Results 전수 대조** — Methods와 같은 방식으로 `results_v4.tex`를 코드 대조. chance 정정이
   이미 파급됐으므로 나머지 수치의 출처 확인이 남음
4. Naive-reader check (abstract + intro) — 전체 원고 대상 `/revise-draft` 시 실행
