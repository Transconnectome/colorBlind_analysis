# Methods 문단별 개정 현황 (2026-08-07)

> 진행 방식: 문단 단위로 수정안 제안 → 확인 → 반영 → 컴파일 검증.
> 서술 제약: 문장 길이 억제, 삽입구 최소화(특히 `:` `;`), academic vocabulary,
> rigorous verbs, direct expressions, American spelling.
> 기하·움직임 관련 결정은 [`REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md`](REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md)가 지배 문서.

---

## 1. 완료 문단

| 행 | 절 | 주요 변경 | 상태 |
|---|---|---|---|
| 16 | 개관 | First/Second/Finally 유지, ΔRDM 제거(§1a), Fig 1C 인용으로 **그림 순서 역전 해소**, 약어 선정의 전 사용 제거 | ✅ |
| 37 | Participants | SNUIRB 기관명·헬싱키·시력·연령범위(20--27), 아형 판정 방법 명시, 세미콜론 제거 | ✅ |
| 44 | 자극 | `isoluminant` 제거, BOLDscreen 32 UHD + 공장보정 명시, **픽셀 단위 보고 선언** | ✅ |
| 46, 48 | 과제 | 두 문단 분할, 50어절 문장 해소, 버튼박스, 500 px 원반 | ✅ |
| 55 | 심리물리 도입 | em-dash 삽입구 해소, **실시 환경 신설**(Liquid Retina XDR, Apple XDR preset, 실내조명) | ✅ |
| 58 | JND 절차 | 좌우 동시 제시·크기·자기조절 시간·`post-warmup` 정의·**catch trial 부재 명시** | ✅ |
| 60 | 색쌍 선정 | `hypothesized` 제거 → **축 기반 서술**(S-cone 축 = yellow--purple), 사전지정 진술, γ 디스플레이 불변 문장 | ✅ |
| 67 | 8AFC | 3문장 → 시행 흐름·격자·**옵션 매 시행 재배열**·timeout·64시행. `Ishihara post-hoc` 문장 삭제(어디에도 보고 안 됨) | ✅ |
| 74 | MRI 획득 | 전면 개정. **FA 75°→70° 정정**, **코일 64채널 정정**, MPRAGE 파라미터, GRAPPA 2 / no multiband / PE R→L, 48 mm 슬랩, 필드맵 취득 명시 | ✅ |
| 76 | 전처리 | FSL 6.0.5.1 / FreeSurfer 7.2.0, MNI 정식명칭 병기, **SDC 미적용 추가**, FD 꼬리(16.2%), §S17 참조 교체 | ⚠️ 첫 문장 미확정 |

**부록**

| | 상태 |
|---|---|
| S1 | ✅ 필드맵 문단 추가 (취득·`IntendedFor`·미소비·R→L 왜곡 잔존) |
| **S17 신설** | ✅ `Supplementary/S17_uncorrected_artifacts.tex`, `main.tex` 포함(56쪽) |
| Discussion Limitations | ✅ 아노말로스코프 문장, 휘도 미측정 문장 |

용어 일괄 교체 `behavioral` → `psychophysical` 29곳 ✅ (라벨 `sec:methods:psychophysical`로 함께 변경)

컴파일: `exit 0`, fatal 0, 미정의 참조 0.

---

## 2. 미결

### U-A. 76행 첫 문장 — BIDS 변환 (**blocking**)

**현재 본문이 사실과 다르다.**
> Data were converted to BIDS format and defaced with ezBIDS.

JSON 프로베넌스에서 확인한 실제 경로:

| 세션 | ConversionSoftware | Dcm2bidsVersion | 디페이싱 |
|---|---|---|---|
| 1차 (2025-10) | dcm2niix v1.0.20240202 | 없음 → **ezBIDS** | ✅ 얼굴영역 비영 0.07--0.11 |
| **2차 (2026-06)** | dcm2niix v1.0.20260416 | **3.2.0** → **dcm2bids** | ❌ 비영 0.78--0.79 |

**두 피험자 모두** 2차는 dcm2bids다. `bids_2nd/tmp_dcm2bids/`에 sub-09만 남은 것은 작업 잔여물.

**초안**
> Data from the first session were converted to BIDS format with the ezBIDS web service \cite{levitas2024}, accessed in October 2025. The second session was converted with dcm2bids 3.2.0 in June 2026. Both routes used \texttt{dcm2niix} for DICOM conversion.

**디페이싱 문장은 처리 결정 후 확정한다.** §3 참조.

### U-B. dcm2bids 인용 미등록

`bibliography.bib`에 항목 없음. Zenodo DOI 인용이 표준이나 **DOI 확인 필요**.

### U-C. 단위 일관성 — 해소됨

44행이 `Stimulus size is reported in display pixels throughout`를 선언하고, 46행(500 px)·58행(96 px 반경, 260 px 간격, $1024 \times 768$ 창)이 모두 픽셀이다. 60행의 `$180^\circ$`는 **색상각**이므로 시각(視角)과 무관, 유지.

### U-D. ezBIDS 접근 시점

1차 2025년 10월, 2차 2026년 6월. 웹 서비스이므로 버전 없이 접근 시점만 기재.

---

## 3. 디페이싱 및 정합 안정성 — 검정 완료 (2026-08-07)

2차 세션 T1w 2개가 디페이싱되지 않았다(§2 U-A). 이 불일치가 무해한지 검정했다.

**절차** (SLURM job 164976, 31분, FreeSurfer 7.2.0 + FSL `bet2`)
2차 T1w 원본과 `mri_deface` 처리본 각각에 `bet2` → `mri_coreg --regheader` 를 돌려
BOLD→T1w 변환(LTA)을 비교했다. 두 arm 은 동일 도구·동일 BOLD 기준 볼륨을 쓴다.

**결과 1 — 디페이싱으로 인한 이동**

| | 평균 | 중앙값 | p95 | 최대 |
|---|---|---|---|---|
| sub-08 | 1.95 mm | 1.91 | 3.25 | 3.93 |
| sub-09 | 9.43 mm | 9.43 | 15.82 | 20.83 |

LTA 는 `LINEAR_VOX_TO_VOX` 이고 T1w 복셀이 비등방($1.0 \times 0.5 \times 0.5$ mm)이므로,
BOLD 볼륨(96×96×24) 내부 격자를 통과시킨 뒤 축별 복셀 크기를 곱해 mm 로 환산했다.

**결과 2 — 런 간 변동성 (기준자)**

같은 피험자·같은 세션·같은 T1w 에서 런마다 독립 산출된 변환의 쌍별 평균 변위.
이론상 동일해야 하는 값이다.

| | 런 수 | 평균 | 범위 |
|---|---|---|---|
| sub-08 1차 | 6 | 1.78 mm | 0.44–3.65 |
| sub-08 2차 | 8 | 4.18 mm | 0.71–9.83 |
| sub-09 1차 | 6 | 0.93 mm | 0.24–1.60 |
| sub-09 2차 | 8 | 3.02 mm | 0.53–9.05 |

**판정** — 디페이싱 이동량 / 런간 변동 = sub-08 **0.5배**, sub-09 **3.1배**.
sub-09 의 9.43 mm 는 관측된 런간 범위 최댓값(9.05 mm) 언저리다.

**디페이싱이 특별히 정합을 깨뜨리는 것이 아니라, 이 자료의 BOLD→T1w 정합 자체가
1–4 mm 규모로 잡음이 있다.** 24슬라이스 후두엽 BOLD 를 전뇌 T1w 에 MI 로 맞추는
문제라 비용면이 얕고 다봉성이다. `mri_coreg` 최종 파라미터에서 sub-09 는 x축 회전이
$+5.75^\circ$(원본) 대 $-1.29^\circ$(디페이싱)로 갈린다. 둘 다 그럴듯한 소량 회전이므로
서로 다른 국소 최적해에 안착한 것이다.

**권고 — 분석 입력을 디페이싱하지 않는다.**

| | |
|---|---|
| 제자리 디페이싱 | **철회.** 정합이 바뀌어 기존 파생물이 무효화된다 |
| 재변환 | 불가. dcm2niix 버전 상이(2024 vs 2026), 프로베넌스 단절 |
| **공유용 사본만 디페이싱** | **채택.** 저장소 업로드본에만 적용하고 분석은 원본 유지 |

> 앞서 권고한 "제자리 디페이싱"은 이 위험을 과소평가한 것이었다. 검정 결과로 철회한다.

**논문 반영** — §S17 에 정합 안정성 문단 신설. §4a 참조.

---

## 4. 이번 회차에 정정한 사실 오류

| 항목 | 기존 | 정정 | 근거 |
|---|---|---|---|
| 플립각 | $75^\circ$ | **$70^\circ$** | SNUBIC 스캔로그 (sub-08 0609, sub-09 0629 일치) |
| 코일 | BioMatrix 3T coils | **64-channel head coil** | 동일 |
| SDC | 미언급 | **미적용 명시** | 세션1 파이프라인 4단계에 `fugue`/`topup`/`fsl_prepare_fieldmap` 0건 |
| §S17 참조 | HMC 재샘플링 arm | **움직임 회귀 arm** | HMC arm 재샘플링 2회, 신뢰도 붕괴 (HC −0.048, CVD −0.170) |
| `isoluminant` | 본문·캡션·Limitations 3곳 | **전부 제거** | $L^*$ 정합은 표준 관찰자 기준 |
| `Ishihara post-hoc` | 8AFC 문단 | **삭제** | Results·Discussion·Supplementary 검색 0건 |

**C010 오해 정정** — `preprocess_tests.md:36-45`에 따르면 C-플래그 3비트는 (고역통과, 1차 drift, 2차 drift)다. `C010 = 1차 drift 회귀자만`이며 HMC/STC/SDC와 무관하다. 그 문서에서 `hmc`·`stc`·`fieldmap`·`realign` 검색 결과 0건.

---

## 5. 다음 문단

`\subsection{ROI definition}` 이후. 76행 이후의 절들이 미검토 상태다.
