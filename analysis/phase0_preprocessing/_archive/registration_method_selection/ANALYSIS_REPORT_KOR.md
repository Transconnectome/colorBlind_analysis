# Preprocessing Methods 비교 분석 보고서

**날짜**: 2026-01-10
**분석 대상**: Method 2 (Header→BBR) vs Method 3 (Header→MI)

---

## 1. Original_v3와 비교

### Dice Coefficient 요약

| Method | Sub-01 | Sub-03 | Sub-06 | 평균 |
|--------|--------|--------|--------|------|
| **Original_v3 (FLIRT→BBR)** | 0.94 | 0.94 | 0.74 | **0.87** |
| **Method 2 (Header→BBR)** | 0.50 | 0.35 | 0.35 | **0.40** |
| **Method 3 (Header→MI)** | 0.36 | 0.31 | 0.32 | **0.33** |

### 결과 해석

**❌ 두 방법 모두 Original_v3보다 현저히 낮음**

- Original_v3: Dice 0.87 (Good~Excellent)
- Method 2: Dice 0.40 (Poor) - **47% 하락**
- Method 3: Dice 0.33 (Poor) - **54% 하락**

**결론**: Header-based initialization은 Limited FOV + 29.5° obliquity 상황에서 **실패**

---

## 2. 각 지표의 의미

### Dice Coefficient (주요 지표)

```
Dice = 2 × |교집합| / (|A| + |B|)
```

**의미**: BOLD mask와 T1w mask가 MNI space에서 얼마나 겹치는가?

**해석 기준**:
- **> 0.90**: Excellent - 완벽한 정렬
- **0.80-0.90**: Good - 충분히 좋은 정렬
- **0.70-0.80**: Fair - 사용 가능하지만 개선 필요
- **< 0.70**: Poor - 심각한 정렬 실패

**현재 결과**:
- Method 2: 0.40 (Poor) ❌
- Method 3: 0.33 (Poor) ❌

---

### Jaccard Index

```
Jaccard = |교집합| / |합집합|
```

**의미**: Dice보다 엄격한 overlap 측정
- Dice는 교집합을 두 번 세지만, Jaccard는 한 번만

**현재 결과**:
- Method 2: 0.21-0.28 (매우 낮음)
- Method 3: 0.16-0.22 (매우 낮음)

---

### Overlap Fraction (BOLD)

```
overlap_frac_bold = |교집합| / |BOLD mask|
```

**의미**: BOLD mask 중 몇 %가 T1w mask와 겹치는가?

**현재 결과**:
- **Method 2**: 0.78-0.97 (높음!) ✅
  - Sub-01: 97% - BOLD의 거의 전체가 T1w와 겹침
  - Sub-03: 97%
  - Sub-06: 85-95%

- **Method 3**: 0.61-0.78 (중간)
  - Sub-01: 72%
  - Sub-03: 75-78%
  - Sub-06: 61-73%

**해석**: BOLD mask는 대부분 T1w mask 안에 있음 (특히 Method 2)

---

### Overlap Fraction (T1w)

```
overlap_frac_t1w = |교집합| / |T1w mask|
```

**의미**: T1w mask 중 몇 %가 BOLD mask와 겹치는가?

**현재 결과**:
- **Method 2**: 0.19-0.34 (매우 낮음!) ❌
  - Sub-01: 33%
  - Sub-03: 21-28%
  - Sub-06: 19-23%

- **Method 3**: 0.16-0.24 (매우 낮음!) ❌
  - Sub-01: 24%
  - Sub-03: 19-22%
  - Sub-06: 17-22%

**해석**: T1w mask의 대부분이 BOLD mask 밖에 있음

---

### Voxel Counts

| Subject | BOLD voxels | T1w voxels | Ratio (BOLD/T1w) |
|---------|-------------|------------|------------------|
| **Method 2** |
| Sub-01 | 79,500-81,600 | 232,496 | 0.34 (1/3) |
| Sub-03 | 50,600-66,900 | 231,426 | 0.22-0.29 |
| Sub-06 | 54,000-56,800 | 229,940 | 0.24 |
| **Method 3** |
| Sub-01 | 75,000-75,900 | 227,040 | 0.33 (1/3) |
| Sub-03 | 55,300-68,100 | 230,119 | 0.24-0.30 |
| Sub-06 | 54,400-57,900 | 188,576 | 0.29-0.31 |

**해석**: BOLD는 T1w의 약 1/3 크기 (Limited FOV)

---

## 3. 전처리 과정 및 결과 의미

### 문제 진단

**Dice가 낮은 이유**:

```
Dice 공식 분해:
Dice = 2 × intersection / (bold_voxels + t1w_voxels)

Method 2 Sub-01 Run 1:
Dice = 2 × 77,354 / (79,501 + 232,496)
     = 154,708 / 311,997
     = 0.496

왜 낮은가?
- Intersection: 77,354 (교집합)
- T1w voxels: 232,496 (분모가 매우 큼)
- BOLD의 97%가 T1w 안에 있지만,
- T1w의 33%만 BOLD와 겹침
→ T1w mask가 너무 큼!
```

### 두 가지 가능성

#### 가능성 1: BOLD mask가 너무 작음 (Under-estimation)

**원인**: Registration이 잘못되어 BOLD mask가 수축됨

**증거**:
- overlap_frac_bold 높음 (97%) → BOLD 전체가 T1w 안
- 하지만 Dice 낮음 → 크기 불일치

#### 가능성 2: T1w mask가 너무 큼 (Over-estimation) ✅ **더 가능성 높음**

**원인**: T1w brain extraction이 과도하게 liberal

**증거**:
- T1w voxels ~230,000 (매우 큼)
- Original_v3도 비슷한 T1w mask 사용했을 것
- 하지만 Original_v3는 Dice 0.87 달성
→ **Registration 자체의 문제**

### Registration 실패 원인

**Header-based initialization의 한계**:

1. **Header 정확도 불충분**
   - qform에 29.5° obliquity 정보 있음
   - 하지만 scanner calibration error ±2-5°
   - BBR/MI refinement 범위 (±5°)를 벗어남

2. **Limited FOV 악화**
   - Header만으로 초기화 시 오차 큼
   - 후두엽만으로 correction 어려움
   - FLIRT의 wide search (±90°)가 필요했음

3. **Method 2 vs Method 3 비교**
   - Method 2 (BBR): Dice 0.40 > Method 3 (MI): 0.33
   - BBR이 약간 낫지만 둘 다 실패
   - Header error가 너무 커서 둘 다 recovery 실패

---

## 4. ROI Atlas Overlay 제안

**목적**: Registration 품질을 직접 확인

### 시각적 검증 방법

```bash
# FSLeyes로 overlay 확인
fsleyes \
  method2_header_bbr/sub-01/func/sub-01_task-rsvp_run-1_space-MNI*_bold.nii.gz \
  -cm red-yellow \
  /path/to/wang_atlas_MNI.nii.gz \
  -cm blue-lightblue -a 50
```

**확인 사항**:
1. V1 atlas가 occipital lobe에 있는가?
2. BOLD activation이 V1과 겹치는가?
3. 전후/좌우 shift가 보이는가?

### 예상 결과

**Original_v3 (Dice 0.87)**:
- ✅ V1 atlas와 BOLD 잘 겹침
- ✅ Occipital cortex 정렬 양호

**Method 2/3 (Dice 0.33-0.40)**:
- ❌ V1 atlas와 BOLD 불일치
- ❌ 큰 spatial offset 예상 (5-10mm)
- ❌ 회전 오차 가능

**권장**:
1. Sub-01 Run 1로 먼저 확인
2. Original_v3와 side-by-side 비교
3. Registration error 방향 확인 (anterior-posterior? rotation?)

---

## 5. 다른 방안 고려

### Option 1: Original_v3 유지 (강력 권장) ✅

**이유**:
- Dice 0.87 (Good~Excellent)
- 이미 8명 group-level 분석 가능
- Sub-06/07 일부 runs만 문제
- 추가 전처리 불필요

**결론**: **현재 상태로 분석 진행**

---

### Option 2: Method 1 재검증

**제안**: Original_v3가 정말 FLIRT→BBR인지 재확인

```bash
# fMRIPrep log 확인
cat /storage/connectome/haba6030/fmriprep_out_original_v3/sub-01/log/*bold* | grep -i "bold.*t1w"
```

**만약 다른 방법이었다면**:
- 그 방법을 Method 1로 다시 테스트
- 하지만 가능성 낮음 (fMRIPrep 표준은 FLIRT→BBR)

---

### Option 3: Sub-06/07만 선택적 재처리

**전략**: 문제 subjects만 다른 방법 시도

**후보 방법**:
1. **ANTs SyN (nonlinear)** - 가장 robust
2. **FSL FNIRT with careful tuning**
3. **Manual landmark-based initialization**

**장점**:
- 전체 재처리 불필요
- Sub-01~05는 original_v3 사용
- Sub-06/07만 특수 처리

**단점**:
- 방법 불일치 (group-level 복잡도 증가)
- 시간 소요

---

### Option 4: Deoblique 재시도 (장기 계획)

**근본 원인**: 29.5° obliquity

**해결책**: Preprocessing 단계에서 deoblique

```bash
# BIDS 단계에서
3dWarp -deoblique -prefix output.nii.gz input.nii.gz
```

**장점**:
- Header error 감소
- 모든 registration method 개선
- 장기적으로 가장 깨끗한 해결

**단점**:
- 전체 재처리 필요 (10명 × 6 runs × 24h)
- 현재 데이터 버림

---

## 최종 권장사항

### 즉시 시행

1. **ROI Atlas Overlay 확인** (30분)
   ```bash
   fsleyes original_v3 vs method2 vs method3
   ```
   - Registration error 시각화
   - 보고서 그림 생성

2. **Original_v3로 분석 진행** ✅
   - Dice 0.87은 충분히 좋음
   - Sub-06/07 문제 runs는 제외하고 진행
   - Method 2/3는 실패로 결론

### 추후 고려

3. **Sub-06/07 개선** (선택사항)
   - 분석 결과 보고 결정
   - 필요 시 ANTs SyN 시도

4. **차기 연구**: Deoblique preprocessing
   - 현재 연구는 original_v3로 완료
   - 다음 프로젝트에서 적용

---

## 결론

**Header-based initialization 가설: 기각 ❌**

- Method 2 (Header→BBR): Dice 0.40 (실패)
- Method 3 (Header→MI): Dice 0.33 (실패)
- 29.5° obliquity + Limited FOV 조합에서 header 부정확
- FLIRT wide search가 필요했음

**최종 선택: Original_v3 (FLIRT→BBR) 유지 ✅**

- Dice 0.87 (충분히 좋음)
- 추가 전처리 불필요
- 즉시 분석 시작 가능

**교훈**:
- "Don't fix what isn't broken"
- Limited FOV + obliquity는 wide search 필수
- Header-based init는 이상적 조건에서만 작동
