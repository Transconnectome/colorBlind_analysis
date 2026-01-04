# Signal Quality Concerns - Version Comparison

**우려사항**: MNI 정합 수치는 동일하지만, 실제 signal quality가 다를 수 있음
**핵심 질문**: original_v3을 쓰면 sub-01, sub-04 문제가 해결되나?

---

## 🤔 우려사항 상세

### 1. Sub-04: V1 Signal Dropout

**deoblique_v2에서의 문제**:
- V1 atlas 위치에 BOLD signal 없음
- fMRIPrep brain mask가 visual cortex 제외
- 또는 실제 signal dropout

**질문**:
```
original_v3을 쓰면:
- V1 위치에 signal이 있을까?
- Brain mask가 더 넓을까?
- Deoblique가 오히려 문제를 일으켰나?
```

### 2. Sub-01: Voxel Count Outlier

**deoblique_v2에서의 문제**:
- Feature selection 후 voxel 수 극단적으로 적음
- V3: 3 voxels vs 다른 피험자 58 voxels
- Group-level 분석 불가

**질문**:
```
original_v3을 쓰면:
- Voxel count가 더 많을까?
- Signal quality가 더 나을까?
- Deoblique로 인한 artifact?
```

### 3. 시각화 품질

**우려**:
- 시각화에서 깨져보이거나 안 겹쳐보임
- MNI 정합 수치는 같아도 실제로는?

**질문**:
```
original_v3에서:
- 시각화가 더 깨끗할까?
- ROI overlay가 더 잘 맞을까?
```

---

## 🔍 확인 방법

### Method 1: ROI Signal Quality 직접 비교 (권장) ⭐

**스크립트 실행**:
```bash
# 서버에 업로드
scp check_roi_quality_comparison.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_roi_quality_check.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/

# 서버에서 실행
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
sbatch run_roi_quality_check.sbatch

# 결과 확인 (5분 후)
cat logs/roi_quality_check.out
```

**확인 항목**:
1. **Sub-04 occipital region**:
   - deoblique_v2: 0 voxels
   - original_v3: ? voxels
   - → 차이 있으면 original_v3 고려

2. **Sub-01 voxel count**:
   - deoblique_v2 vs original_v3 비교
   - → 큰 차이 있으면 재고

3. **전반적 signal quality**:
   - Mean signal, SNR 비교

### Method 2: Baseline 분석 결과 비교

**기존 결과 확인**:
```bash
# deoblique_v2 baseline 결과
ls derivatives/BH2009_deoblique_v2/baseline*/sm*_sub-01_*
ls derivatives/BH2009_deoblique_v2/baseline*/sm*_sub-04_*

# Classification accuracy 확인
grep "Classification accuracy" derivatives/BH2009_deoblique_v2/baseline*/sm*_sub-01_*/classification_results.txt
grep "Classification accuracy" derivatives/BH2009_deoblique_v2/baseline*/sm*_sub-04_*/classification_results.txt
```

**original_v3 baseline 실행** (필요시):
```bash
# 같은 설정으로 sub-01, sub-04만 실행
# Config 81 (baseline)
python fir_reconstruction_BH2009_system_clean.py \
    --dataset original_v3 \
    --subject 01 04 \
    --roi V1 V2 V3 hV4 \
    --smooth 6 \
    --highpass 0.01 \
    ...
```

### Method 3: 시각적 비교

**두 버전 overlay 비교**:
```bash
# 두 버전 모두 다운로드
mkdir -p visual_compare/{deob_v2,orig_v3}

# deoblique_v2
scp 'haba6030@node2:/storage/.../fmriprep_out_deoblique_v2/sub-01/func/*boldref.nii.gz' \
    visual_compare/deob_v2/

# original_v3
scp 'haba6030@node2:/storage/.../fmriprep_out_original_v3/sub-01/func/*boldref.nii.gz' \
    visual_compare/orig_v3/

# Atlas도 다운로드
scp 'haba6030@node2:/scratch/.../derivatives/roi_pipeline_deob_determin/sub-01_V1_roi_mask.nii.gz' \
    visual_compare/

# fsleyes로 비교
fsleyes visual_compare/deob_v2/*boldref.nii.gz \
         visual_compare/roi_mask.nii.gz -cm red -a 30

fsleyes visual_compare/orig_v3/*boldref.nii.gz \
         visual_compare/roi_mask.nii.gz -cm red -a 30
```

---

## 📊 예상 시나리오

### 시나리오 A: 두 버전 동일한 문제

**결과**:
```
sub-04:
  deoblique_v2: V1 signal = 0
  original_v3:  V1 signal = 0  ← 동일!

sub-01:
  deoblique_v2: V3 voxels = 3
  original_v3:  V3 voxels = 3  ← 동일!
```

**해석**:
- 문제는 **데이터 자체** (acquisition, subject motion 등)
- Preprocessing 방법과 무관
- 어느 버전을 써도 동일
- → **deoblique_v2 유지**

### 시나리오 B: original_v3이 더 나음

**결과**:
```
sub-04:
  deoblique_v2: V1 signal = 0
  original_v3:  V1 signal > 0  ← 개선!

sub-01:
  deoblique_v2: V3 voxels = 3
  original_v3:  V3 voxels = 50  ← 개선!
```

**해석**:
- Deoblique가 **signal 손실** 유발?
- 또는 brain mask에 영향
- → **original_v3 전환 고려**

### 시나리오 C: deoblique_v2가 더 나음

**결과**:
```
sub-04:
  deoblique_v2: V1 signal = 100
  original_v3:  V1 signal = 50  ← 더 나쁨!
```

**해석**:
- Deoblique가 실제로 도움됨
- → **deoblique_v2 유지**

---

## 🎯 의사결정 트리

```
ROI Quality 비교 실행
    ↓
결과 분석
    ├─ 시나리오 A (동일) → deoblique_v2 유지
    │   이유: 어차피 같음, 현재 것 유지
    │
    ├─ 시나리오 B (orig_v3 더 나음) → 전환 고려
    │   ↓
    │   추가 확인:
    │   - Baseline 전체 재실행
    │   - 다른 피험자도 비교
    │   - Trade-off 분석
    │   ↓
    │   전환 여부 결정
    │
    └─ 시나리오 C (deob_v2 더 나음) → deoblique_v2 유지
        이유: 이미 더 나은 버전 사용 중
```

---

## ⚠️ 중요 고려사항

### 1. Trade-off 분석

**만약 original_v3이 sub-01, sub-04에서 더 나은데, 다른 피험자에서 더 나쁘다면?**

| 버전 | sub-01 | sub-04 | sub-02~10 | 선택 |
|------|--------|--------|-----------|------|
| deob_v2 | ❌ | ❌ | ✅ Good | ? |
| orig_v3 | ✅ | ✅ | ❌ Worse | ? |

**판단 기준**:
- Non-CVD group: 7명 중 몇 명 사용 가능?
- CVD group: 3명 중 몇 명 사용 가능?
- 전체 trade-off

### 2. 이미 완료된 분석

**deoblique_v2로 이미 분석 완료**:
- Baseline 분석
- Feature selection
- 일부 group-level

**전환 시 비용**:
- 모든 분석 재실행
- 결과 재검증
- 문서 업데이트

**판단**: original_v3이 **확실히 더 나을 때만** 전환

### 3. 신뢰도

**deoblique_v2**:
- 검증됨
- 결과 있음
- 안정적

**original_v3**:
- 아직 검증 안 됨
- Baseline 결과 없음
- 불확실성

---

## 📝 확인 체크리스트

### 즉시 실행

- [ ] ROI quality 비교 스크립트 업로드
- [ ] sbatch 실행
- [ ] 결과 확인 (sub-01, sub-04 중점)

### 결과 분석

- [ ] Sub-04 V1 signal 비교
- [ ] Sub-01 voxel count 비교
- [ ] 전체 피험자 signal quality 비교

### 의사결정

- [ ] 시나리오 판정
- [ ] Trade-off 분석 (필요 시)
- [ ] 버전 선택 확정
- [ ] 문서 업데이트

---

## 💡 빠른 답변 (예상)

**질문**: original_v3을 쓰면 sub-01, sub-04가 괜찮을까?

**예상 답변**: **아마도 아니오** (동일할 가능성 높음)

**근거**:
1. **MNI 정합 동일** → 공간적 위치 동일
2. **Sub-04 V1 dropout** → acquisition 문제일 가능성
3. **Sub-01 outlier** → signal quality 자체 문제
4. **Deoblique 영향** → MNI 정합에는 없음 (확인됨)

**하지만**: 실제로 확인해봐야 정확함!

---

## 🚀 권장 조치

### 1단계: 빠른 확인 (30분)

```bash
# 서버에서 ROI quality 비교
sbatch run_roi_quality_check.sbatch
```

### 2단계: 결과에 따라

**Case 1: 동일** → deoblique_v2 유지
**Case 2: 차이 있음** → 상세 분석

### 3단계: 최종 결정

필요시 전체 피험자 비교 또는 Baseline 재실행

---

**현재 권장**: 빠른 확인 먼저 → 결과 보고 판단
**예상**: 두 버전 동일 → deoblique_v2 유지
