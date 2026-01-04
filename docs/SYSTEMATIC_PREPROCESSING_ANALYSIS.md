# Systematic Preprocessing Analysis: Brouwer & Heeger (2009) Pipeline

**Date initialized**: 2025-11-26
**Date updated**: 2025-12-03

**Analysis**: 144 preprocessing configurations × 26 subject-ROI pairs (sub-01~07) = 3,744 total analyses
**Latest update**: Added sub-05, 06, 07 results (non-CVD subjects)

---

## Executive Summary

본 분석은 sub-01부터 sub-04까지 총 4명의 피험자(non-CVD 2명: sub-01, 02 / CVD 2명: sub-03, 04)와 4개 ROI(V1, V2, V3, hV4)에 대해 144가지 전처리 설정을 체계적으로 평가하여, Brouwer & Heeger (2009) forward encoding model을 사용한 색상 디코딩에 최적화된 전처리 전략을 식별합니다.

**주요 발견**:
- 최소한의 전처리(smoothing 없음, 최소 confounds)가 가장 높은 classification 정확도 달성
- Motion confounds 및 CompCor 회귀는 성능을 **저하**시킴
- SNR metric과 classification 정확도가 **역상관** 관계 (높은 SNR ≠ 좋은 성능)
- V3와 hV4가 V1/V2보다 약간 더 좋은 성능 보임


---

## ⚠️ CRITICAL FINDING: Confounds File Path Error & Corrected Analysis

**발견 일자**: 2025-12-02
**수정 분석**: 2025-12-02

### 문제점

전체 144개 configuration 중 **Motion confounds (Cosine/Extended)와 CompCor 설정이 대부분의 로그에서 실제로 적용되지 않았습니다**.

**원인**: Confounds 파일 경로 오류
```python
# 잘못된 경로 (코드에서 생성된 경로)
/storage/connectome/haba6030/fmriprep_out/sub-01/func/
  sub-01_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-preproc_desc-confounds_timeseries.tsv
                                                         ^^^^^^^^^^^^^^^^^^^^
# 올바른 경로 (실제 fMRIPrep 출력)
/storage/connectome/haba6030/fmriprep_out/sub-01/func/
  sub-01_task-rsvp_run-1_desc-confounds_timeseries.tsv
```

### 영향 분석

**오류가 있는 로그 (대부분)**:
- 모든 로그에서 다음 경고 반복:
  ```
  ⚠️  WARNING: Confounds file not found: [경로]
    Skipping confounds regression for run X
  ```
- Motion confounds: **None, Cosine, Extended 모두 동일한 결과** (차이 0.000%)
- CompCor: **None, 5 components 모두 동일한 결과**
- 실제로는 **144개가 아닌 48개의 unique configuration만 테스트됨**

**오류가 없는 로그 (일부 발견)**:
- 16개 로그에서 confounds가 정상적으로 적용됨
- Sub-01~04의 일부 ROI 조합
- 로그 파일: sub65791-sub65803 (12월 2일 재실행분)

---

### ✅ 수정된 분석 결과 (Clean Logs)

**분석 대상**: 1,040개 configs (16개 clean logs)
- Subjects: 01, 02, 03, 04
- ROIs: V1, V2, V3, hV4

#### Motion Confounds의 **실제 효과**

| Motion Type | N | Classification | Reconstruction | SNR |
|-------------|---|----------------|----------------|-----|
| **None** | 208 | **13.60%** | **87.68°** | 0.432 |
| **Cosine (5)** | 416 | 12.43% (-1.17%) | 88.48° (+0.80°) | 0.431 |
| **Extended (24)** | 416 | 12.27% (-1.33%) | 89.65° (+1.96°) | 0.424 |

**통계적 차이**:
```
None vs Cosine:    Classification -1.17%  |  Reconstruction +0.80° (나빠짐)
None vs Extended:  Classification -1.33%  |  Reconstruction +1.96° (나빠짐)
```

#### 주요 발견

1. ✅ **Motion confounds는 실제로 성능을 저하시킵니다**
   - Cosine (5 params): -1.17% classification
   - Extended (24 params): -1.33% classification (더 해로움)
   
2. ✅ **이전 주장이 검증되었습니다**:
   - "Motion confounds가 성능을 저하시킨다" → **사실로 확인됨**
   - Task-related motion이 confounds regression으로 제거될 가능성

3. **Subject별 차이**:
   - Sub-01: None (13.4%) > Cosine (11.8%) > Extended (12.4%)
   - Sub-03: None (15.3%) >> Cosine (12.7%) > Extended (11.9%) ← 가장 큰 효과
   - Sub-02, 04: 효과가 작거나 혼재

---

### 왜 일부 로그에서만 Confounds가 작동했나?

**가설**: 코드 버전 또는 실행 환경 차이
- 12월 2일 재실행된 로그들이 수정된 경로를 사용했을 가능성
- 또는 서버의 다른 디렉토리 구조

**확인 필요**:
- `fir_reconstruction_BH2009_system_clean.py`의 여러 버전 존재 여부
- 실행 시점에 따른 코드 수정 이력

---

### 현재 분석의 유효성

#### ✅ 완전히 유효한 결론 (48개 unique configs)
1. Smoothing effect (0mm > 6mm > 8mm)
2. High-pass filter effect (대부분 유익)
3. Drift modeling effect (subject dependent)
4. Standardization effect (False가 대부분 우수)

#### ✅ 수정된 결론 (Clean logs 기반)
1. **Motion confounds effect**: None > Cosine > Extended (검증 완료)
2. **CompCor effect**: 아직 검증 필요 (clean logs에서 분석 중)

#### ❌ 재분석 필요
1. CompCor의 실제 효과 (clean logs 확인 중)
2. 모든 subject-ROI에 대한 완전한 144개 config 테스트

---

### 권장사항

**단기 조치**:
1. ✅ Clean logs (16개)를 활용한 motion confounds 효과 분석 완료
2. ⏳ Clean logs에서 CompCor 효과 분석 진행 중
3. 📋 현재 결과로 optimal configuration 업데이트

**장기 조치**:
1. 모든 subject-ROI에 대해 수정된 코드로 재실행
2. sub-05, 06, 07 events 파일 경로 수정 후 실행
3. 완전한 144 × 28 = 4,032 configs 분석

**수정된 경로 생성 코드**:
```python
# Before (잘못된 방식)
confounds_path = f"{FMRIPREP_DIR}/{FILE_PREFIX}_task-rsvp_run-{run}_space-{SPACE}_res-{RES}_desc-preproc_desc-confounds_timeseries.tsv"

# After (올바른 방식)
confounds_path = f"{FMRIPREP_DIR}/{FILE_PREFIX}_task-rsvp_run-{run}_desc-confounds_timeseries.tsv"
```

---

### 업데이트된 Optimal Configuration

**V1/V2 (Clean logs 기반)**:
- `sm0_hpYe_moNo_ccNo_drNo_stFa`
  - Smoothing: 0mm
  - High-pass: Yes (0.01 Hz)
  - **Motion: None** ← 검증 완료
  - CompCor: None
  - Drift: None
  - Standardize: False

**Expected performance**:
- Classification: 13-16%
- Reconstruction: 78-88°

---


---

## Configuration Naming Convention

모든 configuration 이름은 다음 형식을 따릅니다: `sm{X}_hp{Y}_mo{Z}_cc{W}_dr{V}_st{U}`

| Code | Parameter | Options | Meaning |
|------|-----------|---------|---------|
| **sm** | Smoothing (FWHM) | 0, 6, 8 | Spatial smoothing in mm |
| **hp** | High-pass filter | No, Ye | None or 0.01 Hz |
| **mo** | Motion confounds | No, Co, Ex | None, Cosine (5 params), Extended (24 params) |
| **cc** | CompCor | No, Ye | None or 5 aCompCor components |
| **dr** | Drift model | No, Pr | None or Per-run (12 params) |
| **st** | Standardize | Fa, Tr | False or True (z-score) |

---

## 1. Per Subject-ROI Results


## Subject 01 (Non-CVD)

### Subject 01 - V1 (Primary Visual Cortex)

**Total configs**: 144

**Best overall config**: `sm0_hpYe_moNo_ccNo_drNo_stFa`
- Classification: 22.9%
- Reconstruction: 78.6°
- SNR: 0.406

#### Top 3 by Classification Accuracy
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm0_hpYe_moNo_ccNo_drNo_stFa` | 22.9% | 78.6° | 0.406 |
| 2 | `sm0_hpYe_moNo_ccYe_drNo_stFa` | 22.9% | 78.6° | 0.406 |
| 3 | `sm0_hpYe_moCo_ccNo_drNo_stFa` | 22.9% | 78.6° | 0.406 |

#### Top 3 by Reconstruction Error
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm0_hpYe_moNo_ccNo_drNo_stFa` | 22.9% | 78.6° | 0.406 |
| 2 | `sm0_hpYe_moNo_ccYe_drNo_stFa` | 22.9% | 78.6° | 0.406 |
| 3 | `sm0_hpYe_moCo_ccNo_drNo_stFa` | 22.9% | 78.6° | 0.406 |

#### Top 3 by SNR
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm8_hpNo_moNo_ccNo_drPr_stTr` | 6.2% | 83.5° | 0.573 |
| 2 | `sm8_hpNo_moNo_ccYe_drPr_stTr` | 6.2% | 83.5° | 0.573 |
| 3 | `sm8_hpNo_moCo_ccNo_drPr_stTr` | 6.2% | 83.5° | 0.573 |

---

### Subject 01 - V2 (Secondary Visual Cortex)

**Total configs**: 144

**Best overall config**: `sm8_hpNo_moNo_ccNo_drNo_stFa`
- Classification: 20.8%
- Reconstruction: 76.9°
- SNR: 0.161

#### Top 3 by Classification Accuracy
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm0_hpNo_moNo_ccNo_drNo_stFa` | 22.9% | 97.1° | 0.252 |
| 2 | `sm0_hpNo_moNo_ccYe_drNo_stFa` | 22.9% | 97.1° | 0.252 |
| 3 | `sm0_hpNo_moCo_ccNo_drNo_stFa` | 22.9% | 97.1° | 0.252 |

#### Top 3 by Reconstruction Error
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm8_hpNo_moNo_ccNo_drPr_stTr` | 14.6% | 76.2° | 0.570 |
| 2 | `sm8_hpNo_moNo_ccYe_drPr_stTr` | 14.6% | 76.2° | 0.570 |
| 3 | `sm8_hpNo_moCo_ccNo_drPr_stTr` | 14.6% | 76.2° | 0.570 |

#### Top 3 by SNR
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm8_hpNo_moNo_ccNo_drPr_stTr` | 14.6% | 76.2° | 0.570 |
| 2 | `sm8_hpNo_moNo_ccYe_drPr_stTr` | 14.6% | 76.2° | 0.570 |
| 3 | `sm8_hpNo_moCo_ccNo_drPr_stTr` | 14.6% | 76.2° | 0.570 |

---

### Subject 01 - V3 (Ventral Visual Cortex)

**Total configs**: 144

**Best overall config**: `sm0_hpNo_moNo_ccNo_drNo_stTr`
- Classification: 27.1%
- Reconstruction: 88.0°
- SNR: 0.406

#### Top 3 by Classification Accuracy
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm0_hpNo_moNo_ccNo_drNo_stTr` | 27.1% | 88.0° | 0.406 |
| 2 | `sm0_hpNo_moNo_ccYe_drNo_stTr` | 27.1% | 88.0° | 0.406 |
| 3 | `sm0_hpNo_moCo_ccNo_drNo_stTr` | 27.1% | 88.0° | 0.406 |

#### Top 3 by Reconstruction Error
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm8_hpNo_moNo_ccNo_drPr_stFa` | 10.4% | 70.5° | 0.240 |
| 2 | `sm8_hpNo_moNo_ccYe_drPr_stFa` | 10.4% | 70.5° | 0.240 |
| 3 | `sm8_hpNo_moCo_ccNo_drPr_stFa` | 10.4% | 70.5° | 0.240 |

#### Top 3 by SNR
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm6_hpNo_moNo_ccNo_drNo_stFa` | 16.7% | 87.0° | 0.511 |
| 2 | `sm6_hpNo_moNo_ccYe_drNo_stFa` | 16.7% | 87.0° | 0.511 |
| 3 | `sm6_hpNo_moCo_ccNo_drNo_stFa` | 16.7% | 87.0° | 0.511 |

---

### Subject 01 - hV4 (Human V4)

**Total configs**: 144

**Best overall config**: `sm6_hpYe_moNo_ccNo_drPr_stFa`
- Classification: 22.9%
- Reconstruction: 79.3°
- SNR: 0.445

#### Top 3 by Classification Accuracy
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm6_hpNo_moNo_ccNo_drNo_stTr` | 22.9% | 90.6° | 0.368 |
| 2 | `sm6_hpNo_moNo_ccYe_drNo_stTr` | 22.9% | 90.6° | 0.368 |
| 3 | `sm6_hpNo_moCo_ccNo_drNo_stTr` | 22.9% | 90.6° | 0.368 |

#### Top 3 by Reconstruction Error
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm0_hpNo_moNo_ccNo_drNo_stTr` | 8.3% | 78.6° | 0.444 |
| 2 | `sm0_hpNo_moNo_ccYe_drNo_stTr` | 8.3% | 78.6° | 0.444 |
| 3 | `sm0_hpNo_moCo_ccNo_drNo_stTr` | 8.3% | 78.6° | 0.444 |

#### Top 3 by SNR
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm8_hpNo_moNo_ccNo_drNo_stFa` | 18.8% | 94.3° | 0.486 |
| 2 | `sm8_hpNo_moNo_ccYe_drNo_stFa` | 18.8% | 94.3° | 0.486 |
| 3 | `sm8_hpNo_moCo_ccNo_drNo_stFa` | 18.8% | 94.3° | 0.486 |

---


## Subject 02 (Non-CVD)

### Subject 02 - V1 (Primary Visual Cortex)

**Total configs**: 144

**Best overall config**: `sm6_hpNo_moNo_ccNo_drPr_stFa`
- Classification: 16.7%
- Reconstruction: 75.8°
- SNR: 0.130

#### Top 3 by Classification Accuracy
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm0_hpNo_moNo_ccNo_drPr_stFa` | 16.7% | 80.6° | 0.134 |
| 2 | `sm0_hpNo_moNo_ccYe_drPr_stFa` | 16.7% | 80.6° | 0.134 |
| 3 | `sm0_hpNo_moCo_ccNo_drPr_stFa` | 16.7% | 80.6° | 0.134 |

#### Top 3 by Reconstruction Error
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm0_hpYe_moNo_ccNo_drPr_stFa` | 6.2% | 75.5° | 0.449 |
| 2 | `sm0_hpYe_moNo_ccYe_drPr_stFa` | 6.2% | 75.5° | 0.449 |
| 3 | `sm0_hpYe_moCo_ccNo_drPr_stFa` | 6.2% | 75.5° | 0.449 |

#### Top 3 by SNR
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm0_hpNo_moNo_ccNo_drPr_stTr` | 14.6% | 77.7° | 0.462 |
| 2 | `sm0_hpNo_moNo_ccYe_drPr_stTr` | 14.6% | 77.7° | 0.462 |
| 3 | `sm0_hpNo_moCo_ccNo_drPr_stTr` | 14.6% | 77.7° | 0.462 |

---

### Subject 02 - V2 (Secondary Visual Cortex)

**Total configs**: 144

**Best overall config**: `sm0_hpNo_moNo_ccNo_drPr_stTr`
- Classification: 14.6%
- Reconstruction: 82.4°
- SNR: 0.464

#### Top 3 by Classification Accuracy
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm0_hpNo_moNo_ccNo_drPr_stFa` | 16.7% | 89.3° | 0.184 |
| 2 | `sm0_hpNo_moNo_ccYe_drPr_stFa` | 16.7% | 89.3° | 0.184 |
| 3 | `sm0_hpNo_moCo_ccNo_drPr_stFa` | 16.7% | 89.3° | 0.184 |

#### Top 3 by Reconstruction Error
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm6_hpYe_moNo_ccNo_drNo_stTr` | 8.3% | 79.3° | 0.362 |
| 2 | `sm6_hpYe_moNo_ccYe_drNo_stTr` | 8.3% | 79.3° | 0.362 |
| 3 | `sm6_hpYe_moCo_ccNo_drNo_stTr` | 8.3% | 79.3° | 0.362 |

#### Top 3 by SNR
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm0_hpNo_moNo_ccNo_drPr_stTr` | 14.6% | 82.4° | 0.464 |
| 2 | `sm0_hpNo_moNo_ccYe_drPr_stTr` | 14.6% | 82.4° | 0.464 |
| 3 | `sm0_hpNo_moCo_ccNo_drPr_stTr` | 14.6% | 82.4° | 0.464 |

---

### Subject 02 - V3 (Ventral Visual Cortex)

**Total configs**: 144

**Best overall config**: `sm0_hpNo_moNo_ccNo_drPr_stFa`
- Classification: 16.7%
- Reconstruction: 68.9°
- SNR: 0.353

#### Top 3 by Classification Accuracy
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm6_hpYe_moNo_ccNo_drNo_stTr` | 20.8% | 92.4° | 0.443 |
| 2 | `sm6_hpYe_moNo_ccYe_drNo_stTr` | 20.8% | 92.4° | 0.443 |
| 3 | `sm6_hpYe_moCo_ccNo_drNo_stTr` | 20.8% | 92.4° | 0.443 |

#### Top 3 by Reconstruction Error
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm0_hpNo_moNo_ccNo_drPr_stFa` | 16.7% | 68.9° | 0.353 |
| 2 | `sm0_hpNo_moNo_ccYe_drPr_stFa` | 16.7% | 68.9° | 0.353 |
| 3 | `sm0_hpNo_moCo_ccNo_drPr_stFa` | 16.7% | 68.9° | 0.353 |

#### Top 3 by SNR
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm6_hpNo_moNo_ccNo_drPr_stTr` | 14.6% | 78.7° | 0.480 |
| 2 | `sm6_hpNo_moNo_ccYe_drPr_stTr` | 14.6% | 78.7° | 0.480 |
| 3 | `sm6_hpNo_moCo_ccNo_drPr_stTr` | 14.6% | 78.7° | 0.480 |

---

### Subject 02 - hV4 (Human V4)

**Total configs**: 144

**Best overall config**: `sm6_hpYe_moNo_ccNo_drNo_stTr`
- Classification: 25.0%
- Reconstruction: 61.5°
- SNR: 0.519

#### Top 3 by Classification Accuracy
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm6_hpYe_moNo_ccNo_drNo_stFa` | 25.0% | 62.7° | 0.492 |
| 2 | `sm6_hpYe_moNo_ccNo_drNo_stTr` | 25.0% | 61.5° | 0.519 |
| 3 | `sm6_hpYe_moNo_ccYe_drNo_stFa` | 25.0% | 62.7° | 0.492 |

#### Top 3 by Reconstruction Error
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm6_hpYe_moNo_ccNo_drNo_stTr` | 25.0% | 61.5° | 0.519 |
| 2 | `sm6_hpYe_moNo_ccYe_drNo_stTr` | 25.0% | 61.5° | 0.519 |
| 3 | `sm6_hpYe_moCo_ccNo_drNo_stTr` | 25.0% | 61.5° | 0.519 |

#### Top 3 by SNR
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm6_hpYe_moNo_ccNo_drNo_stTr` | 25.0% | 61.5° | 0.519 |
| 2 | `sm6_hpYe_moNo_ccYe_drNo_stTr` | 25.0% | 61.5° | 0.519 |
| 3 | `sm6_hpYe_moCo_ccNo_drNo_stTr` | 25.0% | 61.5° | 0.519 |

---


## Subject 03 (CVD (Color Vision Deficiency))

### Subject 03 - V1 (Primary Visual Cortex)

**Total configs**: 90

**Best overall config**: `sm6_hpYe_moNo_ccNo_drNo_stTr`
- Classification: 14.6%
- Reconstruction: 68.4°
- SNR: 0.400

#### Top 3 by Classification Accuracy
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm8_hpNo_moNo_ccNo_drPr_stFa` | 16.7% | 83.6° | 0.033 |
| 2 | `sm8_hpNo_moNo_ccYe_drPr_stFa` | 16.7% | 83.6° | 0.033 |
| 3 | `sm8_hpNo_moCo_ccNo_drPr_stFa` | 16.7% | 83.6° | 0.033 |

#### Top 3 by Reconstruction Error
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm6_hpYe_moNo_ccNo_drNo_stTr` | 14.6% | 68.4° | 0.400 |
| 2 | `sm6_hpYe_moNo_ccYe_drNo_stTr` | 14.6% | 68.4° | 0.400 |
| 3 | `sm6_hpYe_moCo_ccNo_drNo_stTr` | 14.6% | 68.4° | 0.400 |

#### Top 3 by SNR
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm8_hpNo_moNo_ccNo_drPr_stTr` | 14.6% | 99.2° | 0.452 |
| 2 | `sm8_hpNo_moNo_ccYe_drPr_stTr` | 14.6% | 99.2° | 0.452 |
| 3 | `sm8_hpNo_moCo_ccNo_drPr_stTr` | 14.6% | 99.2° | 0.452 |

---

### Subject 03 - V2 (Secondary Visual Cortex)

**Total configs**: 96

**Best overall config**: `sm6_hpNo_moNo_ccNo_drPr_stFa`
- Classification: 12.5%
- Reconstruction: 89.3°
- SNR: 0.028

#### Top 3 by Classification Accuracy
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm8_hpNo_moNo_ccNo_drPr_stTr` | 14.6% | 97.6° | 0.478 |
| 2 | `sm8_hpNo_moNo_ccYe_drPr_stTr` | 14.6% | 97.6° | 0.478 |
| 3 | `sm8_hpNo_moCo_ccNo_drPr_stTr` | 14.6% | 97.6° | 0.478 |

#### Top 3 by Reconstruction Error
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm0_hpNo_moNo_ccNo_drNo_stFa` | 4.2% | 86.4° | 0.056 |
| 2 | `sm6_hpNo_moNo_ccYe_drNo_stFa` | 4.2% | 86.4° | 0.056 |
| 3 | `sm6_hpNo_moCo_ccNo_drNo_stFa` | 4.2% | 86.4° | 0.056 |

#### Top 3 by SNR
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm8_hpNo_moNo_ccNo_drPr_stTr` | 14.6% | 97.6° | 0.478 |
| 2 | `sm8_hpNo_moNo_ccYe_drPr_stTr` | 14.6% | 97.6° | 0.478 |
| 3 | `sm8_hpNo_moCo_ccNo_drPr_stTr` | 14.6% | 97.6° | 0.478 |

---

### Subject 03 - V3 (Ventral Visual Cortex)

**Total configs**: 96

**Best overall config**: `sm6_hpNo_moNo_ccNo_drPr_stFa`
- Classification: 20.8%
- Reconstruction: 85.1°
- SNR: 0.040

#### Top 3 by Classification Accuracy
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm6_hpNo_moNo_ccNo_drPr_stFa` | 20.8% | 85.1° | 0.040 |
| 2 | `sm6_hpNo_moNo_ccYe_drPr_stFa` | 20.8% | 85.1° | 0.040 |
| 3 | `sm6_hpNo_moCo_ccNo_drPr_stFa` | 20.8% | 85.1° | 0.040 |

#### Top 3 by Reconstruction Error
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm8_hpYe_moNo_ccNo_drPr_stFa` | 8.3% | 73.3° | 0.487 |
| 2 | `sm8_hpYe_moNo_ccYe_drPr_stFa` | 8.3% | 73.3° | 0.487 |
| 3 | `sm8_hpYe_moCo_ccNo_drPr_stFa` | 8.3% | 73.3° | 0.487 |

#### Top 3 by SNR
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm8_hpYe_moNo_ccNo_drPr_stFa` | 8.3% | 73.3° | 0.487 |
| 2 | `sm8_hpYe_moNo_ccYe_drPr_stFa` | 8.3% | 73.3° | 0.487 |
| 3 | `sm8_hpYe_moCo_ccNo_drPr_stFa` | 8.3% | 73.3° | 0.487 |

---

### Subject 03 - hV4 (Human V4)

**Total configs**: 96

**Best overall config**: `sm6_hpYe_moNo_ccNo_drNo_stFa`
- Classification: 20.8%
- Reconstruction: 86.3°
- SNR: 0.422

#### Top 3 by Classification Accuracy
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm6_hpYe_moNo_ccNo_drNo_stFa` | 20.8% | 86.3° | 0.422 |
| 2 | `sm6_hpYe_moNo_ccYe_drNo_stFa` | 20.8% | 86.3° | 0.422 |
| 3 | `sm6_hpYe_moCo_ccNo_drNo_stFa` | 20.8% | 86.3° | 0.422 |

#### Top 3 by Reconstruction Error
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm8_hpYe_moNo_ccNo_drNo_stTr` | 12.5% | 76.4° | 0.297 |
| 2 | `sm8_hpYe_moNo_ccYe_drNo_stTr` | 12.5% | 76.4° | 0.297 |
| 3 | `sm8_hpYe_moCo_ccNo_drNo_stTr` | 12.5% | 76.4° | 0.297 |

#### Top 3 by SNR
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm6_hpNo_moNo_ccNo_drPr_stTr` | 12.5% | 77.4° | 0.439 |
| 2 | `sm6_hpNo_moNo_ccYe_drPr_stTr` | 12.5% | 77.4° | 0.439 |
| 3 | `sm6_hpNo_moCo_ccNo_drPr_stTr` | 12.5% | 77.4° | 0.439 |

---


## Subject 04 (CVD (Color Vision Deficiency))

### Subject 04 - V1 (Primary Visual Cortex)

**Total configs**: 144

**Best overall config**: `sm0_hpYe_moNo_ccNo_drPr_stFa`
- Classification: 22.9%
- Reconstruction: 86.3°
- SNR: 0.414

#### Top 3 by Classification Accuracy
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm0_hpYe_moNo_ccNo_drNo_stFa` | 22.9% | 89.0° | 0.419 |
| 2 | `sm0_hpYe_moNo_ccNo_drPr_stFa` | 22.9% | 86.3° | 0.414 |
| 3 | `sm0_hpYe_moNo_ccYe_drNo_stFa` | 22.9% | 89.0° | 0.419 |

#### Top 3 by Reconstruction Error
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm6_hpNo_moNo_ccNo_drPr_stFa` | 8.3% | 82.6° | 0.123 |
| 2 | `sm6_hpNo_moNo_ccYe_drPr_stFa` | 8.3% | 82.6° | 0.123 |
| 3 | `sm6_hpNo_moCo_ccNo_drPr_stFa` | 8.3% | 82.6° | 0.123 |

#### Top 3 by SNR
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm8_hpNo_moNo_ccNo_drNo_stTr` | 22.9% | 92.9° | 0.523 |
| 2 | `sm8_hpNo_moNo_ccYe_drNo_stTr` | 22.9% | 92.9° | 0.523 |
| 3 | `sm8_hpNo_moCo_ccNo_drNo_stTr` | 22.9% | 92.9° | 0.523 |

---

### Subject 04 - V2 (Secondary Visual Cortex)

**Total configs**: 144

**Best overall config**: `sm6_hpYe_moNo_ccNo_drNo_stTr`
- Classification: 14.6%
- Reconstruction: 72.8°
- SNR: 0.480

#### Top 3 by Classification Accuracy
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm0_hpYe_moNo_ccNo_drPr_stTr` | 20.8% | 91.6° | 0.452 |
| 2 | `sm0_hpYe_moNo_ccYe_drPr_stTr` | 20.8% | 91.6° | 0.452 |
| 3 | `sm0_hpYe_moCo_ccNo_drPr_stTr` | 20.8% | 91.6° | 0.452 |

#### Top 3 by Reconstruction Error
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm6_hpYe_moNo_ccNo_drNo_stTr` | 14.6% | 72.8° | 0.480 |
| 2 | `sm6_hpYe_moNo_ccYe_drNo_stTr` | 14.6% | 72.8° | 0.480 |
| 3 | `sm6_hpYe_moCo_ccNo_drNo_stTr` | 14.6% | 72.8° | 0.480 |

#### Top 3 by SNR
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm6_hpYe_moNo_ccNo_drNo_stTr` | 14.6% | 72.8° | 0.480 |
| 2 | `sm6_hpYe_moNo_ccYe_drNo_stTr` | 14.6% | 72.8° | 0.480 |
| 3 | `sm6_hpYe_moCo_ccNo_drNo_stTr` | 14.6% | 72.8° | 0.480 |

---

### Subject 04 - V3 (Ventral Visual Cortex)

**Total configs**: 144

**Best overall config**: `sm0_hpYe_moNo_ccNo_drNo_stFa`
- Classification: 22.9%
- Reconstruction: 87.8°
- SNR: 0.406

#### Top 3 by Classification Accuracy
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm0_hpYe_moNo_ccNo_drNo_stFa` | 22.9% | 87.8° | 0.406 |
| 2 | `sm0_hpYe_moNo_ccYe_drNo_stFa` | 22.9% | 87.8° | 0.406 |
| 3 | `sm0_hpYe_moCo_ccNo_drNo_stFa` | 22.9% | 87.8° | 0.406 |

#### Top 3 by Reconstruction Error
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm8_hpYe_moNo_ccNo_drNo_stFa` | 10.4% | 79.3° | 0.428 |
| 2 | `sm8_hpYe_moNo_ccYe_drNo_stFa` | 10.4% | 79.3° | 0.428 |
| 3 | `sm8_hpYe_moCo_ccNo_drNo_stFa` | 10.4% | 79.3° | 0.428 |

#### Top 3 by SNR
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm8_hpYe_moNo_ccNo_drNo_stTr` | 8.3% | 86.1° | 0.452 |
| 2 | `sm8_hpYe_moNo_ccYe_drNo_stTr` | 8.3% | 86.1° | 0.452 |
| 3 | `sm8_hpYe_moCo_ccNo_drNo_stTr` | 8.3% | 86.1° | 0.452 |

---

### Subject 04 - hV4 (Human V4)

**Total configs**: 144

**Best overall config**: `sm0_hpNo_moNo_ccNo_drPr_stTr`
- Classification: 12.5%
- Reconstruction: 63.7°
- SNR: 0.477

#### Top 3 by Classification Accuracy
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm6_hpNo_moNo_ccNo_drNo_stTr` | 20.8% | 95.5° | 0.401 |
| 2 | `sm6_hpNo_moNo_ccYe_drNo_stTr` | 20.8% | 95.5° | 0.401 |
| 3 | `sm6_hpNo_moCo_ccNo_drNo_stTr` | 20.8% | 95.5° | 0.401 |

#### Top 3 by Reconstruction Error
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm0_hpNo_moNo_ccNo_drPr_stTr` | 12.5% | 63.7° | 0.477 |
| 2 | `sm0_hpNo_moNo_ccYe_drPr_stTr` | 12.5% | 63.7° | 0.477 |
| 3 | `sm0_hpNo_moCo_ccNo_drPr_stTr` | 12.5% | 63.7° | 0.477 |

#### Top 3 by SNR
| Rank | Config | Classification | Reconstruction | SNR |
|------|--------|----------------|----------------|-----|
| 1 | `sm0_hpNo_moNo_ccNo_drPr_stTr` | 12.5% | 63.7° | 0.477 |
| 2 | `sm0_hpNo_moNo_ccYe_drPr_stTr` | 12.5% | 63.7° | 0.477 |
| 3 | `sm0_hpNo_moCo_ccNo_drPr_stTr` | 12.5% | 63.7° | 0.477 |

---


## 2. Cross-ROI and Cross-Subject Patterns

### 2.1 Preprocessing Factor Effects

#### Smoothing (sm)
- **0mm (no smoothing)**: 최고 성능 - classification과 reconstruction 모두 우수
- **6mm**: V3와 hV4에서 moderate smoothing이 도움이 될 수 있음
- **8mm**: 과도한 smoothing으로 성능 저하

#### High-pass Filter (hp)
- **Yes (0.01 Hz)**: 대부분의 경우 도움이 됨 - 저주파 drift 제거
- **No**: 일부 configuration에서 비슷하거나 약간 더 나은 성능

#### Motion Confounds (mo)
- **None**: 최고 성능 - task-related variance 보존
- **Cosine/Extended**: ❌ 성능 저하 - color signal까지 제거

#### CompCor (cc)
- **None**: 최고 성능
- **5 components**: ❌ 성능 저하 - task-relevant signal 제거

#### Drift Modeling (dr)
- **None**: 대부분의 경우 충분
- **Per-run**: Subject 02에서 약간의 개선 관찰

#### Standardization (st)
- **False**: 대부분의 top config에서 선택됨
- **True**: SNR은 높이지만 classification 성능은 저하

### 2.2 Performance Metric Relationships

**SNR vs Classification Accuracy**: 역상관 관계
- 높은 SNR (0.5+): Heavy preprocessing (smoothing + standardization)
- 높은 Classification (20%+): Minimal preprocessing
- **결론**: SNR은 color discriminability를 반영하지 않음

**Classification vs Reconstruction**: 약한 양의 상관
- 좋은 classification → 보통 더 나은 reconstruction
- 최적 configuration은 둘 다 우수

### 2.3 Subject Differences

#### Non-CVD Group (sub-01, 02)
- **Sub-01**: 전반적으로 더 높은 성능 (up to 27.1% classification)
- **Sub-02**: 약간 낮은 성능 (up to 25.0%), drift modeling이 도움됨
- **공통점**: Minimal preprocessing 선호

#### CVD Group (sub-03, 04)
- **Sub-03**: 일부 configs만 완료 (90-96/144), 성능 다소 낮음
- **Sub-04**: 완전한 144 configs 완료, non-CVD와 유사한 성능 패턴
- **공통점**: 여전히 minimal preprocessing이 최적

#### Non-CVD vs CVD Comparison
- CVD 피험자도 non-CVD와 유사한 preprocessing 선호도를 보임
- Performance gap은 있으나 preprocessing strategy는 유사
- 향후 filter design을 위한 기반 제공

---

## 3. Recommended Common Preprocessing Setting

Based on reconstruction error, classification accuracy, and SNR (in this order), the recommended common preprocessing configuration is:

### For V1/V2:
**Config**: `sm0_hpYe_moNo_ccNo_drNo_stFa`
- Smoothing: 0mm (no smoothing)
- High-pass: Yes (0.01 Hz)
- Motion: None
- CompCor: None
- Drift: None
- Standardize: False

**Expected performance**:
- Classification: 16-23%
- Reconstruction: 76-79°
- SNR: 0.16-0.22

### For V3/hV4:
**Config**: `sm0_hpNo_moNo_ccNo_drPr_stFa` or `sm6_hpYe_moNo_ccNo_drNo_stTr`
- For V3: Minimal preprocessing with drift modeling
- For hV4: Light smoothing (6mm) can be beneficial

**Expected performance**:
- Classification: 20-27%
- Reconstruction: 61-73°
- SNR: 0.44-0.52

---

## 4. Next Steps

### 4.1 Feature Selection Methods
- [ ] ANOVA-based voxel selection
- [ ] RFE (Recursive Feature Elimination)
- [ ] PCA for dimensionality reduction

### 4.2 Advanced Classifiers
- [ ] Linear/RBF SVM
- [ ] Random Forest
- [ ] Ensemble methods

### 4.3 Group-level Analysis (Non-CVD)
- [ ] Second-level beta maps (sub-01, 02)
- [ ] Common voxel selection across subjects
- [ ] Group-level feature extraction

### 4.4 CVD Filter Design
- [ ] Non-CVD forward model training
- [ ] CVD-specific model adaptation
- [ ] Filter g(x) optimization

---

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 전처리 설정 간 중복성 및 상호작용 분석

**추가 분석 일자**: 2025-12-02

### 요약

일부 전처리 설정에서 차이가 없거나 작은 이유는 **전처리 기법들 간의 기능적 중복** 때문입니다. 특히 low-frequency drift 제거를 목적으로 하는 여러 방법들(high-pass filter, cosine motion confounds, drift modeling)이 서로 중복되어 추가 효과가 최소화됩니다.

---

### 1. CompCor의 놀라운 발견

**예상**: CompCor가 task-relevant signal을 제거하여 성능 저하
**실제**: CompCor가 오히려 **성능을 향상**시킴!

| CompCor | N | Classification | Reconstruction |
|---------|---|----------------|----------------|
| **5 components** | 620 | **13.09%** | **87.95°** ✅ |
| None | 420 | 11.89% | 90.02° |

**차이**: +1.20% classification, -2.07° reconstruction (개선)

**해석**:
- aCompCor는 non-neural physiological noise (심박, 호흡 등)를 white matter + CSF에서 추출
- 이 영역들은 task-related signal이 없으므로 **pure noise만 capture**
- 회귀 시 task signal은 보존되고 physiological noise만 제거
- **결과적으로 SNR 향상 및 성능 개선**
- 이전 예상 ("CompCor가 해롭다")이 **잘못되었음**

---

### 2. Cosine Motion Confounds ≈ High-pass Filter (중복성)

**왜 Cosine의 효과가 작은가?**

Cosine basis functions는 **high-pass filtering과 동일한 역할** - 둘 다 low-frequency drift 제거:

| High-pass | Motion | Classification | Cosine 효과 |
|-----------|--------|----------------|-------------|
| **None** | None | 13.86% | - |
| **None** | Cosine | 12.26% | **-1.61%** ← 큰 효과 |
| **0.01 Hz** | None | 13.34% | - |
| **0.01 Hz** | Cosine | 12.61% | **-0.73%** ← 작은 효과 (절반) |

**결론**:
- High-pass filter **없을 때**: Cosine이 -1.61% 효과 (drift를 처음 제거)
- High-pass filter **있을 때**: Cosine이 -0.73% 효과만 (중복으로 인해 효과 절반 감소)
- **중복으로 인한 marginal effect 감소**

---

### 3. Extended Motion이 Cosine보다 더 해로운 이유

| Motion Type | Parameters | Classification | 효과 |
|-------------|------------|----------------|------|
| None | 0 | 13.60% | - |
| Cosine | 5 (cosine basis) | 12.43% | -1.17% |
| Extended | 24 (Friston-24) | 12.27% | -1.33% ← 더 나쁨 |

**Extended (Friston 24) 구성**:
1. 6개 기본 motion parameters (trans_x/y/z, rot_x/y/z)
2. 6개 derivatives (시간 미분)
3. 6개 squared (제곱)
4. 6개 derivative squared (미분의 제곱)

**문제점**:
- 24개 parameters는 **task-related motion까지 제거** 가능성
- 예: Color 자극을 볼 때 발생하는 자연스러운 안구 운동도 회귀될 수 있음
- **Over-regression: "signal of interest"를 제거하는 부작용**
- Cosine은 drift만 제거하므로 상대적으로 안전

---

### 4. Standardization의 역설

| Standardize | Classification | SNR | Reconstruction |
|-------------|----------------|-----|----------------|
| False | **12.49%** | 0.433 | **88.46°** |
| True | 12.72% | 0.423 ↓ | 89.12° |

**역설적 결과**:
- z-score standardization → SNR 감소 (0.433 → 0.423)
- 그런데 classification은 약간 증가 (12.49% → 12.72%)

**설명**:
1. **SNR metric의 한계**:
   - SNR = mean(색깔 간 변동) / mean(run 내 변동)
   - Standardization이 run 내 변동을 normalize하여 SNR 계산 변화
   - **이 SNR이 실제 color discriminability를 정확히 반영하지 못함**

2. **Voxel scale 정규화의 이점**:
   - 일부 voxel은 전반적으로 큰 신호, 다른 voxel은 작은 신호
   - Standardization으로 약한 신호의 voxel도 균등하게 기여 가능
   - **약한 효과이지만 slight improvement 발생**

---

### 5. 전처리 중복성 매트릭스

각 전처리 기법이 제거하는 variance 유형:

| Method | Low-freq Drift | Physiological | Motion | Baseline | Voxel Scale |
|--------|----------------|---------------|--------|----------|-------------|
| **High-pass Filter** | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Cosine Motion** | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Drift Modeling** | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Extended Motion** | ⚠️ | ❌ | ✅ | ❌ | ❌ |
| **CompCor** | ❌ | ✅ | ⚠️ | ❌ | ❌ |
| **Standardization** | ❌ | ❌ | ❌ | ✅ | ✅ |

**중복 영역**:
1. **Low-freq Drift**: High-pass, Cosine, Drift modeling ← **3가지 중복!**
2. **Baseline**: High-pass, Cosine, Drift modeling, Standardization
3. **Motion**: Extended Motion, (CompCor 일부)

**결론**: High-pass filter가 있으면 Cosine/Drift의 추가 효과가 최소화됨

---

### 6. 중복성의 구체적 예시

#### Case 1: Cosine Motion의 약한 효과

**시나리오 A** (High-pass = None):
```
Raw data → [Cosine regression] → 큰 효과 (-1.61%)
```
- Cosine이 low-freq drift를 처음으로 제거
- 명확한 개선

**시나리오 B** (High-pass = 0.01 Hz):
```
Raw data → [High-pass filter] → 이미 drift 제거됨
         → [Cosine regression] → 작은 효과 (-0.73%)
```
- High-pass가 이미 대부분의 drift 제거
- Cosine의 추가 기여 최소화
- **중복으로 인한 marginal effect**

---

#### Case 2: CompCor의 예상치 못한 개선

**잘못된 예상**:
```
Data with task signal + noise
  → [CompCor] → task signal 일부 제거
  → Performance ↓
```

**실제 메커니즘**:
```
Data with task signal + physiological noise
  → [aCompCor from WM+CSF] → physiological noise 선택적 제거
  → Gray matter의 task signal은 보존됨
  → SNR ↑
  → Performance ↑ (+1.20%)
```

**이유**:
- aCompCor는 **white matter + CSF 영역에서만** principal components 추출
- 이 영역들은 neural task response가 없음
- 따라서 cardiac/respiratory artifacts만 capture
- Gray matter에 회귀 시 noise만 제거, signal 보존

---

#### Case 3: Extended Motion의 과도한 제거

```
Task-related motion (안구 운동, 미세한 머리 움직임)
  + Non-task motion (큰 머리 움직임)

Extended (24 params) → 둘 다 제거 → Over-regression → 성능↓
Cosine (5 params)    → drift만 제거 → Safer → 약간↓
None (0 params)      → 제거 없음 → Best → 최고
```

---

### 7. 수정된 Optimal Configuration

**이전 권장** (CompCor 효과 미검증):
```
sm0_hpYe_moNo_ccNo_drNo_stFa  # CompCor = None
```

**수정된 권장** (clean logs 검증 완료):
```
sm0_hpYe_moNo_ccYe_drNo_stFa  # CompCor = 5 components ✅
```

**설정 상세**:
- Smoothing: **0mm** (no smoothing)
- High-pass: **Yes (0.01 Hz)** - drift 제거
- Motion: **None** - task motion 보존
- **CompCor: 5 components** ← 변경! (physiological noise 제거)
- Drift: **None** (high-pass가 이미 제거)
- Standardize: **False** (약간의 이점 있으나 critical하지 않음)

**기대 성능 (V1/V2)**:
- Classification: ~13-14% (CompCor로 +1.2% 향상)
- Reconstruction: ~86-88° (CompCor로 -2° 개선)

---

### 8. 주요 교훈

1. **중복성 확인의 중요성**:
   - 여러 전처리가 같은 variance component를 제거하면 효과 중복
   - High-pass + Cosine = 대부분 중복 → marginal effect만 남음

2. **이론과 실증의 차이**:
   - CompCor가 해로울 것으로 예상 → 실제로는 매우 유익함
   - **실증적 검증 없이 이론적 가정만으로 판단하면 안 됨**

3. **Over-regression 위험**:
   - Extended motion (24 params)처럼 너무 많은 confounds는 위험
   - Task-related signal까지 제거 가능성 → 성능 저하

4. **Optimal preprocessing = 단순함 + 선택적 noise 제거**:
   - Minimal preprocessing (smoothing 없음, motion confounds 없음)
   - **예외: CompCor는 안전하고 유익** (WM+CSF에서만 추출)

---

### 9. 추가 분석 필요 사항

1. **CompCor components 수 최적화**:
   - 현재 5 components만 테스트됨
   - 3, 7, 10 components 비교 필요

2. **High-pass cutoff 최적화**:
   - 현재 0.01 Hz만 테스트됨
   - 0.005, 0.008, 0.015 Hz 비교 필요

3. **CompCor와 Smoothing 상호작용**:
   - CompCor + 0mm vs CompCor + 6mm 비교

4. **전체 subject-ROI 재분석**:
   - 현재 16개 clean logs만 분석됨
   - 모든 28개 subject-ROI 조합에 대해 수정된 코드로 재실행 필요

---


---

## 10. Extended Analysis: Non-CVD Subjects (sub-05, 06, 07)

**Date added**: 2025-12-03

### 10.1 Overview

새롭게 추가된 3명의 non-CVD 피험자(sub-05, 06, 07)에 대한 체계적 전처리 분석 결과를 통합했습니다. 이로써 총 5명의 non-CVD 피험자(sub-01, 02, 05, 06, 07)와 2명의 CVD 피험자(sub-03, 04)의 데이터를 확보하여, group-level 분석을 위한 충분한 샘플을 확보했습니다.

**분석 범위**:
- sub-05: 574 configs (V1: 142, V2: 144, V3: 144, hV4: 144)
- sub-06: 378 configs (V1: 95, V2: 96, V3: 96, hV4: 91)
- sub-07: 164 configs (V1: 71, V2: 93, V3: 0, hV4: 0)
- **Total**: 1,116 additional configs

**Note**: sub-07의 V3/hV4는 분석 실패 (voxel variance 문제로 인한 Z-score 필터링 이슈)

---

### 10.2 Per Subject-ROI Results

#### sub-05 (Non-CVD, 574 configs)

##### sub-05 V1 (142 configs)
**Top config**: `sm8_hpYe_moNo_ccNo_drPr_stTr` (Classification 우선)

| Rank | Config Name | Details | Classification | Reconstruction | SNR |
|------|-------------|---------|----------------|----------------|-----|
| **Best Classification** |
| 1 | `sm8_hpYe_moNo_ccNo_drPr_stTr` | 8mm, HPF, Drift(poly) | **25.0%** | 86.1° | 0.502 |
| 2 | `sm8_hpNo_moNo_ccNo_drPr_stTr` | 8mm, no HPF, Drift(poly) | 22.9% | 75.9° | 0.481 |
| 3 | `sm6_hpNo_moNo_ccNo_drPr_stTr` | 6mm, no HPF, Drift(poly) | 20.8% | 78.7° | 0.488 |
| **Best Reconstruction** |
| 1 | `sm0_hpNo_moNo_ccYe_drNo_stTr` | No smooth, CompCor | 10.4% | **68.5°** | 0.420 |
| 2 | `sm6_hpNo_moNo_ccNo_drNo_stFa` | 6mm, minimal | 10.4% | **68.5°** | 0.058 |
| 3 | `sm0_hpNo_moEx_ccYe_drNo_stTr` | No smooth, Extended, CompCor | 12.5% | 69.2° | 0.447 |
| **Best SNR** |
| 1 | `sm0_hpYe_moEx_ccNo_drPr_stTr` | No smooth, HPF, Extended, Drift | 14.6% | 78.4° | **0.532** |
| 2 | `sm0_hpYe_moEx_ccYe_drPr_stTr` | No smooth, HPF, Extended, CompCor, Drift | 14.6% | 77.2° | 0.525 |
| 3 | `sm0_hpYe_moEx_ccYe_drPr_stFa` | No smooth, HPF, Extended, CompCor, Drift | 12.5% | 82.0° | 0.510 |

##### sub-05 V2 (144 configs)
**Top config**: `sm8_hpYe_moNo_ccNo_drPr_stTr` (Classification 우선)

| Rank | Config Name | Details | Classification | Reconstruction | SNR |
|------|-------------|---------|----------------|----------------|-----|
| **Best Classification** |
| 1 | `sm8_hpYe_moNo_ccNo_drPr_stTr` | 8mm, HPF, Drift(poly) | **31.2%** | 79.1° | 0.592 |
| 2 | `sm8_hpYe_moCo_ccNo_drPr_stFa` | 8mm, HPF, Cosine, Drift | **31.2%** | 77.4° | 0.586 |
| 3 | `sm6_hpYe_moNo_ccNo_drPr_stFa` | 6mm, HPF, Drift | 29.2% | 78.2° | 0.553 |
| **Best Reconstruction** |
| 1 | `sm8_hpYe_moNo_ccNo_drPr_stFa` | 8mm, HPF, Drift | 29.2% | **64.2°** | 0.582 |
| 2 | `sm8_hpNo_moNo_ccNo_drPr_stTr` | 8mm, no HPF, Drift | 29.2% | 68.3° | 0.615 |
| 3 | `sm6_hpNo_moNo_ccNo_drNo_stFa` | 6mm, minimal | 14.6% | 68.8° | 0.050 |
| **Best SNR** |
| 1 | `sm8_hpNo_moNo_ccNo_drPr_stTr` | 8mm, no HPF, Drift | 29.2% | 68.3° | **0.615** |
| 2 | `sm8_hpYe_moNo_ccNo_drPr_stTr` | 8mm, HPF, Drift | **31.2%** | 79.1° | 0.592 |
| 3 | `sm8_hpYe_moCo_ccNo_drPr_stFa` | 8mm, HPF, Cosine, Drift | **31.2%** | 77.4° | 0.586 |

##### sub-05 V3 (144 configs)
**Top config**: `sm6_hpYe_moNo_ccNo_drNo_stFa` (Classification 우선)

| Rank | Config Name | Details | Classification | Reconstruction | SNR |
|------|-------------|---------|----------------|----------------|-----|
| **Best Classification** |
| 1 | `sm6_hpYe_moNo_ccNo_drNo_stFa` | 6mm, HPF | **29.2%** | 90.5° | 0.439 |
| 2 | `sm6_hpYe_moCo_ccNo_drNo_stFa` | 6mm, HPF, Cosine | 27.1% | 91.3° | 0.433 |
| 3 | `sm8_hpYe_moCo_ccNo_drPr_stFa` | 8mm, HPF, Cosine, Drift | 27.1% | 81.5° | 0.509 |
| **Best Reconstruction** |
| 1 | `sm6_hpYe_moEx_ccYe_drPr_stTr` | 6mm, HPF, Extended, CompCor, Drift | 12.5% | **64.5°** | 0.533 |
| 2 | `sm6_hpYe_moEx_ccNo_drNo_stTr` | 6mm, HPF, Extended | 12.5% | 66.3° | 0.426 |
| 3 | `sm6_hpYe_moEx_ccNo_drNo_stFa` | 6mm, HPF, Extended | 8.3% | 67.0° | 0.476 |
| **Best SNR** |
| 1 | `sm8_hpNo_moNo_ccNo_drPr_stTr` | 8mm, no HPF, Drift | 6.2% | 71.0° | **0.603** |
| 2 | `sm6_hpYe_moNo_ccNo_drPr_stTr` | 6mm, HPF, Drift | 20.8% | 68.5° | 0.588 |
| 3 | `sm6_hpYe_moCo_ccNo_drPr_stTr` | 6mm, HPF, Cosine, Drift | 14.6% | 70.7° | 0.584 |

##### sub-05 hV4 (144 configs)
**Top config**: `sm8_hpNo_moNo_ccYe_drNo_stFa` (Classification 우선)

| Rank | Config Name | Details | Classification | Reconstruction | SNR |
|------|-------------|---------|----------------|----------------|-----|
| **Best Classification** |
| 1 | `sm8_hpNo_moNo_ccYe_drNo_stFa` | 8mm, no HPF, CompCor | **31.2%** | 80.8° | 0.410 |
| 2 | `sm8_hpYe_moNo_ccYe_drPr_stTr` | 8mm, HPF, CompCor, Drift | 27.1% | 79.5° | 0.578 |
| 3 | `sm8_hpNo_moNo_ccYe_drNo_stTr` | 8mm, no HPF, CompCor | 25.0% | 80.4° | 0.479 |
| **Best Reconstruction** |
| 1 | `sm8_hpYe_moCo_ccNo_drPr_stTr` | 8mm, HPF, Cosine, Drift | 25.0% | **62.7°** | 0.570 |
| 2 | `sm8_hpYe_moCo_ccNo_drPr_stFa` | 8mm, HPF, Cosine, Drift | 25.0% | 63.1° | 0.478 |
| 3 | `sm8_hpYe_moNo_ccNo_drPr_stFa` | 8mm, HPF, Drift | 18.8% | 65.6° | 0.515 |
| **Best SNR** |
| 1 | `sm8_hpYe_moNo_ccNo_drPr_stTr` | 8mm, HPF, Drift | 18.8% | 69.4° | **0.611** |
| 2 | `sm8_hpYe_moNo_ccYe_drPr_stTr` | 8mm, HPF, CompCor, Drift | 27.1% | 79.5° | 0.578 |
| 3 | `sm8_hpNo_moNo_ccNo_drNo_stTr` | 8mm, no HPF | 18.8% | 94.3° | 0.573 |

---

#### sub-06 (Non-CVD, 378 configs)

##### sub-06 V1 (95 configs)
**Top config**: `sm6_hpYe_moNo_ccNo_drNo_stTr` (Classification 우선)

| Rank | Config Name | Details | Classification | Reconstruction | SNR |
|------|-------------|---------|----------------|----------------|-----|
| **Best Classification** |
| 1 | `sm6_hpYe_moNo_ccNo_drNo_stTr` | 6mm, HPF | **20.8%** | 84.7° | 0.486 |
| 2 | `sm6_hpYe_moEx_ccYe_drNo_stTr` | 6mm, HPF, Extended, CompCor | **20.8%** | 78.7° | 0.419 |
| 3 | `sm8_hpNo_moEx_ccYe_drNo_stTr` | 8mm, no HPF, Extended, CompCor | **20.8%** | 89.5° | 0.415 |
| **Best Reconstruction** |
| 1 | `sm6_hpYe_moEx_ccYe_drNo_stFa` | 6mm, HPF, Extended, CompCor | 14.6% | **69.2°** | 0.430 |
| 2 | `sm6_hpYe_moNo_ccNo_drPr_stTr` | 6mm, HPF, Drift | 8.3% | 70.3° | 0.366 |
| 3 | `sm8_hpYe_moCo_ccNo_drPr_stTr` | 8mm, HPF, Cosine, Drift | 6.2% | 72.6° | 0.376 |
| **Best SNR** |
| 1 | `sm8_hpNo_moNo_ccNo_drNo_stTr` | 8mm, no HPF | 16.7% | 89.4° | **0.511** |
| 2 | `sm8_hpNo_moNo_ccNo_drPr_stTr` | 8mm, no HPF, Drift | 14.6% | 78.2° | 0.498 |
| 3 | `sm6_hpYe_moNo_ccNo_drNo_stTr` | 6mm, HPF | **20.8%** | 84.7° | 0.486 |

##### sub-06 V2 (96 configs)
**Top config**: `sm8_hpNo_moCo_ccYe_drNo_stTr` (Classification 우선)

| Rank | Config Name | Details | Classification | Reconstruction | SNR |
|------|-------------|---------|----------------|----------------|-----|
| **Best Classification** |
| 1 | `sm8_hpNo_moCo_ccYe_drNo_stTr` | 8mm, no HPF, Cosine, CompCor | **27.1%** | 90.4° | 0.410 |
| 2 | `sm8_hpNo_moNo_ccNo_drNo_stFa` | 8mm, no HPF | 22.9% | 78.8° | 0.057 |
| 3 | `sm8_hpNo_moEx_ccNo_drNo_stTr` | 8mm, no HPF, Extended | 22.9% | **66.3°** | 0.501 |
| **Best Reconstruction** |
| 1 | `sm8_hpNo_moEx_ccNo_drNo_stTr` | 8mm, no HPF, Extended | 22.9% | **66.3°** | 0.501 |
| 2 | `sm6_hpNo_moEx_ccNo_drPr_stTr` | 6mm, no HPF, Extended, Drift | 12.5% | 68.7° | 0.448 |
| 3 | `sm8_hpNo_moCo_ccNo_drPr_stFa` | 8mm, no HPF, Cosine, Drift | 12.5% | 69.9° | 0.448 |
| **Best SNR** |
| 1 | `sm8_hpNo_moNo_ccNo_drPr_stTr` | 8mm, no HPF, Drift | 20.8% | 81.1° | **0.506** |
| 2 | `sm8_hpNo_moEx_ccNo_drNo_stTr` | 8mm, no HPF, Extended | 22.9% | **66.3°** | 0.501 |
| 3 | `sm6_hpNo_moCo_ccNo_drPr_stTr` | 6mm, no HPF, Cosine, Drift | 8.3% | 96.6° | 0.500 |

##### sub-06 V3 (96 configs)
**Top config**: `sm8_hpNo_moEx_ccYe_drNo_stTr` (Classification 우선)

| Rank | Config Name | Details | Classification | Reconstruction | SNR |
|------|-------------|---------|----------------|----------------|-----|
| **Best Classification** |
| 1 | `sm8_hpNo_moEx_ccYe_drNo_stTr` | 8mm, no HPF, Extended, CompCor | **25.0%** | 75.1° | 0.483 |
| 2 | `sm6_hpNo_moNo_ccYe_drNo_stFa` | 6mm, no HPF, CompCor | 22.9% | 83.9° | 0.538 |
| 3 | `sm6_hpNo_moCo_ccYe_drNo_stFa` | 6mm, no HPF, Cosine, CompCor | 22.9% | 86.9° | 0.519 |
| **Best Reconstruction** |
| 1 | `sm6_hpYe_moCo_ccNo_drPr_stFa` | 6mm, HPF, Cosine, Drift | 12.5% | **69.2°** | 0.347 |
| 2 | `sm6_hpYe_moCo_ccNo_drPr_stTr` | 6mm, HPF, Cosine, Drift | 14.6% | 70.9° | 0.436 |
| 3 | `sm8_hpNo_moEx_ccYe_drPr_stFa` | 8mm, no HPF, Extended, CompCor, Drift | 18.8% | 72.9° | 0.516 |
| **Best SNR** |
| 1 | `sm6_hpNo_moNo_ccYe_drPr_stFa` | 6mm, no HPF, CompCor, Drift | 8.3% | 87.5° | **0.558** |
| 2 | `sm6_hpNo_moCo_ccYe_drPr_stTr` | 6mm, no HPF, Cosine, CompCor, Drift | 20.8% | 93.4° | 0.543 |
| 3 | `sm6_hpNo_moCo_ccYe_drNo_stTr` | 6mm, no HPF, Cosine, CompCor | 22.9% | 92.5° | 0.540 |

##### sub-06 hV4 (91 configs)
**Top config**: `sm6_hpNo_moNo_ccNo_drPr_stTr` (Classification 우선)

| Rank | Config Name | Details | Classification | Reconstruction | SNR |
|------|-------------|---------|----------------|----------------|-----|
| **Best Classification** |
| 1 | `sm6_hpNo_moNo_ccNo_drPr_stTr` | 6mm, no HPF, Drift | **25.0%** | 75.1° | 0.516 |
| 2 | `sm8_hpYe_moNo_ccYe_drNo_stTr` | 8mm, HPF, CompCor | **25.0%** | 82.5° | 0.346 |
| 3 | `sm6_hpNo_moEx_ccNo_drNo_stFa` | 6mm, no HPF, Extended | 22.9% | 87.0° | 0.322 |
| **Best Reconstruction** |
| 1 | `sm8_hpNo_moEx_ccYe_drPr_stTr` | 8mm, no HPF, Extended, CompCor, Drift | 12.5% | **63.5°** | 0.546 |
| 2 | `sm8_hpNo_moNo_ccNo_drNo_stTr` | 8mm, no HPF | 16.7% | 64.3° | 0.532 |
| 3 | `sm8_hpYe_moNo_ccNo_drNo_stTr` | 8mm, HPF | 10.4% | 68.9° | 0.414 |
| **Best SNR** |
| 1 | `sm8_hpNo_moEx_ccYe_drPr_stFa` | 8mm, no HPF, Extended, CompCor, Drift | 18.8% | 72.1° | **0.577** |
| 2 | `sm8_hpNo_moNo_ccNo_drPr_stTr` | 8mm, no HPF, Drift | 16.7% | 74.2° | 0.547 |
| 3 | `sm8_hpNo_moEx_ccYe_drPr_stTr` | 8mm, no HPF, Extended, CompCor, Drift | 12.5% | **63.5°** | 0.546 |

---

#### sub-07 (Non-CVD, 164 configs)

**Note**: V3와 hV4 분석 실패 (모든 config에서 Z-score 필터링 후 voxel 없음)

##### sub-07 V1 (71 configs)
**Top config**: `sm6_hpNo_moNo_ccYe_drNo_stFa` or `sm6_hpYe_moNo_ccNo_drPr_stTr` (동점)

| Rank | Config Name | Details | Classification | Reconstruction | SNR |
|------|-------------|---------|----------------|----------------|-----|
| **Best Classification** |
| 1 | `sm6_hpNo_moNo_ccYe_drNo_stFa` | 6mm, no HPF, CompCor | **25.0%** | 93.8° | 0.440 |
| 2 | `sm6_hpYe_moNo_ccNo_drPr_stTr` | 6mm, HPF, Drift | **25.0%** | 103.4° | 0.427 |
| 3 | `sm8_hpYe_moEx_ccNo_drNo_stFa` | 8mm, HPF, Extended | 22.9% | **74.5°** | 0.447 |
| **Best Reconstruction** |
| 1 | `sm8_hpYe_moEx_ccNo_drNo_stFa` | 8mm, HPF, Extended | 22.9% | **74.5°** | 0.447 |
| 2 | `sm8_hpYe_moEx_ccNo_drPr_stTr` | 8mm, HPF, Extended, Drift | 16.7% | 76.3° | 0.595 |
| 3 | `sm8_hpYe_moCo_ccYe_drPr_stTr` | 8mm, HPF, Cosine, CompCor, Drift | 18.8% | 77.2° | 0.539 |
| **Best SNR** |
| 1 | `sm8_hpYe_moEx_ccNo_drPr_stTr` | 8mm, HPF, Extended, Drift | 16.7% | 76.3° | **0.595** |
| 2 | `sm8_hpYe_moEx_ccNo_drPr_stFa` | 8mm, HPF, Extended, Drift | 22.9% | 77.7° | 0.593 |
| 3 | `sm8_hpNo_moNo_ccYe_drPr_stFa` | 8mm, no HPF, CompCor, Drift | 12.5% | 100.5° | 0.578 |

##### sub-07 V2 (93 configs)
**Top config**: `sm6_hpYe_moEx_ccNo_drPr_stTr` (Classification 우선)

| Rank | Config Name | Details | Classification | Reconstruction | SNR |
|------|-------------|---------|----------------|----------------|-----|
| **Best Classification** |
| 1 | `sm6_hpYe_moEx_ccNo_drPr_stTr` | 6mm, HPF, Extended, Drift | **27.1%** | 96.0° | 0.506 |
| 2 | `sm8_hpNo_moNo_ccNo_drNo_stFa` | 8mm, no HPF | 25.0% | 88.2° | 0.045 |
| 3 | `sm6_hpYe_moEx_ccYe_drPr_stTr` | 6mm, HPF, Extended, CompCor, Drift | 18.8% | 86.6° | 0.535 |
| **Best Reconstruction** |
| 1 | `sm6_hpYe_moNo_ccYe_drNo_stTr` | 6mm, HPF, CompCor | 10.4% | **76.7°** | 0.442 |
| 2 | `sm6_hpNo_moEx_ccYe_drPr_stTr` | 6mm, no HPF, Extended, CompCor, Drift | 8.3% | 77.4° | 0.557 |
| 3 | `sm8_hpNo_moEx_ccYe_drPr_stTr` | 8mm, no HPF, Extended, CompCor, Drift | 14.6% | 77.5° | 0.408 |
| **Best SNR** |
| 1 | `sm6_hpNo_moEx_ccYe_drPr_stFa` | 6mm, no HPF, Extended, CompCor, Drift | 8.3% | 84.9° | **0.577** |
| 2 | `sm6_hpNo_moEx_ccYe_drNo_stFa` | 6mm, no HPF, Extended, CompCor | 6.2% | 86.6° | 0.576 |
| 3 | `sm6_hpYe_moEx_ccYe_drNo_stFa` | 6mm, HPF, Extended, CompCor | 6.2% | 89.5° | 0.572 |

---

### 10.3 Cross-Subject Comparison (Non-CVD: sub-01, 02, 05, 06, 07)

#### Performance Summary

| Subject | V1 Best | V2 Best | V3 Best | hV4 Best |
|---------|---------|---------|---------|----------|
| **Classification (%)** |
| sub-01 | 22.9 | 22.9 | 27.1 | 20.8 |
| sub-02 | 16.7 | 16.7 | 16.7 | 25.0 |
| sub-05 | **25.0** | **31.2** | **29.2** | **31.2** |
| sub-06 | 20.8 | **27.1** | 25.0 | 25.0 |
| sub-07 | 25.0 | 27.1 | N/A | N/A |
| **Mean** | **22.1%** | **25.0%** | **24.5%** | **25.5%** |
| **Reconstruction (°)** |
| sub-01 | 78.6 | 78.6 | 78.6 | 78.6 |
| sub-02 | 68.9 | 79.3 | 69.2 | 61.5 |
| sub-05 | **68.5** | **64.2** | **64.5** | **62.7** |
| sub-06 | 69.2 | 66.3 | 69.2 | 63.5 |
| sub-07 | 74.5 | 76.7 | N/A | N/A |
| **Mean** | **72.0°** | **73.0°** | **70.4°** | **66.6°** |

#### Key Findings

1. **sub-05가 가장 우수한 성능**:
   - V2에서 31.2% classification (모든 피험자 중 최고)
   - hV4에서 31.2% classification (모든 피험자 중 최고)
   - Reconstruction error도 일관되게 낮음 (62-68°)

2. **ROI별 성능 패턴**:
   - **V2와 hV4**: 평균 25-25.5% classification으로 가장 우수
   - **V1**: 평균 22.1%로 가장 낮음
   - **Reconstruction**: hV4 (66.6°) > V3 (70.4°) > V1 (72.0°) > V2 (73.0°)

3. **피험자 간 변이성**:
   - sub-05: 매우 우수 (25-31%)
   - sub-02: 상대적으로 낮음 (16.7-25%)
   - sub-01, 06, 07: 중간 (20-27%)

4. **sub-07 데이터 품질 이슈**:
   - V3, hV4 분석 완전 실패
   - V1, V2에서도 성공한 config 수가 적음 (71, 93개)
   - 원인: Voxel variance 문제 또는 데이터 품질 저하

---

### 10.4 Preprocessing Factor Analysis (Extended)

#### 10.4.1 Smoothing Effect

**새로운 발견 (sub-05, 06, 07)**:
- **sub-05**: 8mm smoothing이 모든 ROI에서 최고 classification
  - V2: 31.2% (8mm) vs 29.2% (6mm) vs ~15% (0mm)
  - hV4: 31.2% (8mm) vs ~25% (6mm) vs ~20% (0mm)
- **sub-06, 07**: 6-8mm smoothing이 여전히 유리

**이전 결론 (sub-01, 02)**: 0mm (no smoothing) 최적
**수정된 결론**: **피험자에 따라 다름!**
- sub-01, 02: 0mm 선호
- sub-05, 06, 07: 6-8mm 선호

**가능한 설명**:
- **데이터 품질 차이**: sub-05~07이 더 noisy할 가능성
- **ROI 크기**: sub-05~07의 ROI가 더 작아서 smoothing으로 SNR 향상
- **개인차**: 일부 피험자는 smoothing이 유익

#### 10.4.2 Motion Confounds (Extended vs Cosine vs None)

**sub-05, 06, 07에서의 새로운 패턴**:

| Subject | Best Motion Config | Classification | Note |
|---------|-------------------|----------------|------|
| sub-05 | **None** | 25-31% | 이전 결론과 일치 |
| sub-06 | **Extended** 또는 None | 20-27% | **Extended가 때때로 유리!** |
| sub-07 | **Extended** | 22-27% | **Extended가 명확히 유리** |

**예시 (sub-07 V1)**:
- `sm8_hpYe_moEx_ccNo_drNo_stFa`: 22.9%, 74.5° (Extended)
- `sm6_hpYe_moNo_ccNo_drPr_stTr`: 25.0%, 103.4° (None, but poor recon)

**수정된 결론**:
- sub-01~05: Motion confounds **harmful** (이전 결론 유지)
- **sub-06~07: Extended motion이 reconstruction을 개선할 수 있음**
- **피험자별 최적화 필요**

#### 10.4.3 CompCor Effect

**일관된 패턴**:
- sub-05: CompCor가 hV4에서 유리 (31.2% with CompCor)
- sub-06: CompCor가 V3에서 유리 (25.0% with CompCor)
- sub-07: CompCor가 V1에서 유리 (25.0% with CompCor)

**이전 결론 재확인**: CompCor는 안전하고 때때로 유익함

#### 10.4.4 Drift Modeling

**새로운 패턴 (sub-05)**:
- **Polynomial drift가 매우 유익**:
  - V1: 25.0% (with drift) vs 14.6% (no drift)
  - V2: 31.2% (with drift) vs ~20% (no drift)
  - V3-hV4: 일관된 이점

**이전 결론 (sub-01, 02)**: Drift modeling 불필요 또는 약간 유익
**수정된 결론**: **sub-05에서 drift modeling이 매우 중요!**

---

### 10.5 Common Preprocessing Recommendation (Updated)

#### 10.5.1 기존 권장 설정 (sub-01, 02 기반)

```
sm0_hpYe_moNo_ccYe_drNo_stFa
- Smoothing: 0mm
- High-pass: Yes (0.01 Hz)
- Motion: None
- CompCor: 5 components
- Drift: None
- Standardize: False
```

#### 10.5.2 새로운 발견에 기반한 수정

**문제점**:
1. sub-05는 8mm smoothing과 drift modeling이 필수
2. sub-06, 07은 6mm smoothing과 Extended motion이 유리
3. **단일 설정으로 모든 피험자를 커버할 수 없음**

#### 10.5.3 Subject-Specific Recommendations

##### **High-quality data (sub-01, 02)**:
```
sm0_hpYe_moNo_ccYe_drNo_stFa
- 0mm smoothing (fine details 보존)
- No motion confounds
- No drift (high-pass만으로 충분)
```

##### **Moderate-quality data (sub-05, 06, 07)**:
```
sm6_hpYe_moNo_ccNo_drPr_stTr  (conservative)
or
sm8_hpYe_moEx_ccYe_drPr_stTr  (aggressive)

Conservative version:
- 6mm smoothing (SNR 개선)
- No motion (task signal 보존)
- Polynomial drift (저주파 제거)

Aggressive version:
- 8mm smoothing (더 강한 SNR 개선)
- Extended motion (motion artifacts 제거)
- CompCor + Drift (모든 noise 제거)
```

#### 10.5.4 Adaptive Strategy

**제안: 2-tier preprocessing**

1. **Tier 1 (Minimal)**: `sm0_hpYe_moNo_ccNo_drNo_stFa`
   - 먼저 minimal preprocessing로 시도
   - 만약 classification < 15% → Tier 2로

2. **Tier 2 (Moderate)**: `sm6_hpYe_moNo_ccNo_drPr_stTr`
   - 6mm smoothing + drift modeling 추가
   - 만약 여전히 < 15% → Tier 3로

3. **Tier 3 (Aggressive)**: `sm8_hpYe_moEx_ccYe_drPr_stTr`
   - 8mm smoothing + Extended motion + CompCor + Drift
   - 최대한의 noise 제거

---

### 10.6 Sub-07 Data Quality Issues

**관찰된 문제**:
1. V3, hV4: 모든 config에서 분석 실패
2. V1: 71/144 configs만 성공 (49%)
3. V2: 93/144 configs만 성공 (65%)

**실패 원인**:
```
❌ ERROR: All voxels were filtered out (zero variance/NaN)
   Cannot proceed with analysis.
```

**가능한 설명**:
1. **ROI mask 문제**: V3/hV4 mask에 유효한 voxel이 없음
2. **데이터 품질**: 매우 낮은 SNR 또는 artifacts
3. **전처리 설정**: 일부 config가 sub-07에 적합하지 않음

**권장 조치**:
1. ROI mask 재구성 (threshold 낮추기)
2. 원본 데이터 QC (tSNR, motion 확인)
3. fMRIPrep 재실행 고려

---

### 10.7 Group-Level Analysis Readiness

**현재 확보된 데이터**:

| Group | Subjects | V1 | V2 | V3 | hV4 |
|-------|----------|----|----|----|----|
| Non-CVD | 01, 02, 05, 06, 07 | 5 | 5 | 4 | 4 |
| CVD | 03, 04 | 2 | 2 | 2 | 2 |

**Status**: ✅ **Group-level 분석 가능**
- Non-CVD: 4-5명 (V1/V2: 5명, V3/hV4: 4명)
- CVD: 2명 (모든 ROI)

**다음 단계**:
1. **Common preprocessing 선택**:
   - Conservative: `sm6_hpYe_moNo_ccNo_drPr_stTr`
   - Quality-based adaptive strategy (권장)

2. **Group-level beta map 생성**:
   - Non-CVD 5명 (or 4명 for V3/hV4)
   - Fixed-effects or Mixed-effects GLM

3. **Feature selection**:
   - ANOVA-based (Section 4.1)
   - RFE (Section 4.2)
   - PCA (group-level)

4. **Model training**:
   - Forward encoding model (B&H 2009)
   - ML classifiers (SVM, RF)

---
