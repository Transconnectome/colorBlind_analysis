# 원래 가설과 목표 (Original Hypothesis and Goal)

## 🎯 최종 목표: Color Filter 제작

**Color Filter**: CVD가 착용하면 정상처럼 색을 인지할 수 있는 필터

---

## 📋 초기 가정 (Initial Assumptions)

### 1. ✅ CVD도 뇌에서는 색을 구분한다
- **Evidence**: CVD subjects의 classification accuracy > chance (12.5%)
- **의미**: 뇌 신호로는 8가지 색상이 구분 가능함
- **하지만**: 지각(perception)에서는 색약 증상 있음

### 2. ✅ HC끼리는 voxel response pattern이 비슷하다
- **가정**: 정상인들은 색상에 대한 voxel 반응이 유사함
- **기대**: HC group template 구축 가능
- **현실**: ❌ 실패 (RDM 0.26, 목표 >0.5)
  - HC끼리도 개인차가 큼
  - MNI 정렬만으로는 부족

### 3. ❓ CVD는 HC와 **systematic하게** 다르다
- **가정**: CVD의 voxel response가 HC와 일관되게(systematically) 다름
- **Not random**: 모든 CVD에서 공통된 차이 패턴
- **검증 필요**: Option 2D로 확인 중

### 4. 🎯 CVD voxel response를 HC voxel response로 변환 가능
- **방법**: Transformation matrix T를 찾음
- **수식**: `CVD_response + T = HC_like_response`
- **조건**: T가 모든 CVD에서 공통되어야 함

### 5. 🎯 Shared W matrix 사용 가능
- **가정**: Color encoding model (W matrix)은 HC와 CVD 공통
- **근거**: Brouwer & Heeger (2009) 방법론
- **수식**: `B = W × C` (B: brain activity, W: weights, C: color channels)
- **의미**: W는 universal, 차이는 input (voxel response)만

---

## 🔬 Filter 제작 전략

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Color Filter                          │
└─────────────────────────────────────────────────────────────┘

Input: 외부 색상 stimulus → CVD eye → CVD voxel response

Step 1: Transformation
   CVD voxel response → [Apply T] → HC-like voxel response

Step 2: Shared Encoding Model
   HC-like voxel response → [W matrix] → Color channels

Step 3: Reconstruction
   Color channels → Reconstructed color (correct perception)
```

### 핵심 가정

1. **Voxel response가 다르다**:
   - HC: "정상" voxel response
   - CVD: "왜곡된" voxel response
   - 차이: **Systematic & correctable**

2. **W matrix는 같다**:
   - HC와 CVD 모두 같은 color encoding model 사용
   - 차이는 input (voxel response)만
   - 따라서 input을 고치면 output도 고쳐짐

3. **Filter = Inverse Transformation**:
   - T_CVD_to_HC를 찾으면
   - Filter = T_inverse
   - 외부 stimulus에 filter 적용 → CVD가 HC처럼 인지

---

## 🔍 검증해야 할 질문들

### Question 1: HC끼리 정말 같은가?
- **Current Status**: ❌ 실패
- **Evidence**: RDM 0.26, Procrustes 0.91
- **의미**: Geometric structure는 비슷, but color distance structure 다름
- **Action**: HC group template 대신 reference-based approach

### Question 2: CVD는 HC와 systematic하게 다른가?
- **Current Status**: ❓ 검증 중 (Option 2D)
- **Method**:
  - CVD common pattern 계산
  - Consistency across CVDs 확인
  - Color/voxel-specific difference 분석
- **Success Criteria**:
  - CVD common magnitude > 0.4
  - Consistency score > 0.7
  - Specific color pairs (red-green) show large difference

### Question 3: HC 내 variability vs CVD difference 비율?
- **핵심**: CVD difference가 HC variability보다 커야 함
- **If not**: Filter가 HC variability도 왜곡시킴
- **Metric**: `Signal-to-Noise = CVD_difference / HC_variability`

### Question 4: Transformation T가 stable한가?
- **Test**: Sub-08, 09, 10에서 같은 T를 찾을 수 있는가?
- **Method**: T_08, T_09, T_10의 correlation
- **Success**: r > 0.7

### Question 5: Transformed CVD가 reconstruction 개선되는가?
- **Test**:
  1. CVD voxel response → Reconstruction (baseline)
  2. CVD + T → HC-like response → Reconstruction (filtered)
  3. Compare reconstruction error
- **Success**: Error reduction > 20%

---

## 📊 현재 상태 (Current Status)

### ✅ 검증된 가정
1. CVD도 뇌에서 색 구분 가능 (classification > chance)
2. Procrustes alignment 작동함 (stability 0.91)
3. Within-subject stability 높음 (0.83)

### ❌ 실패한 가정
1. HC끼리 voxel response 같음 → RDM 0.26
2. HC group template 가능 → 불가능

### ❓ 검증 중인 가정
1. CVD systematic difference (Option 2D 실행 중)
2. Shared W matrix (아직 테스트 안 함)
3. Filter effectiveness (아직 테스트 안 함)

---

## 🎯 다음 단계 (Next Steps)

### Immediate (진행 중)
- **Option 2D**: CVD vs HC systematic difference 분석
- **결과 대기 중**: ~1시간

### If Option 2D Success (Systematic difference 발견)
1. **Transformation T 계산**:
   ```python
   T = HC_mean - CVD_pattern
   CVD_corrected = CVD_pattern + T
   ```

2. **Validation**:
   - CVD_corrected로 reconstruction
   - Error 감소 확인
   - Across CVDs consistency 확인

3. **W matrix 학습**:
   - HC data로 W matrix 학습
   - CVD_corrected에도 같은 W 적용
   - Reconstruction quality 비교

4. **Filter design**:
   - Stimulus space에서 T_inverse 계산
   - 외부 색상 → Filter → CVD eye
   - Simulation & validation

### If Option 2D Fails (No systematic difference)
1. **Pivot to individual-level**:
   - CVD 각자의 T 계산
   - Personalized filter
   - 하지만 generalization 안 됨

2. **Alternative finding**:
   - Individual variability as main finding
   - CVD-specific patterns characterization
   - No universal filter, but scientific contribution

---

## 💡 핵심 통찰 (Key Insights So Far)

### 1. Procrustes는 성공했다!
- **Stability 0.91**: Geometric alignment 잘 됨
- **But RDM 0.26**: Color distance structure 안 맞음
- **의미**: 전체 shape는 비슷, 거리 비율이 다름

### 2. HC group template의 실패 ≠ 전체 실패
- HC끼리 개인차 있어도
- CVD vs HC difference가 클 수 있음
- Reference-based approach로 해결 가능

### 3. 핵심은 "Systematic"
- CVD들이 **같은 방향**으로 HC와 다른가?
- Random individual difference ❌
- Shared CVD pattern ✅

### 4. Filter 가능성의 조건
```
Filter 가능 ⟺ CVD_common_difference > HC_within_variability
```

---

## 📚 이론적 배경 (Theoretical Background)

### Brouwer & Heeger (2009)
- **Forward encoding model**: B = W × C
- **W matrix**: voxel × channel weights
- **C**: 6 idealized color channels
- **Assumption**: W is learned from training data

### Our Extension
- **HC와 CVD의 W는 같다고 가정**
- **차이는 B (voxel response)**
- **따라서**: B_CVD를 B_HC처럼 만들면 → C도 같아짐

### Critical Assumption
```
If: W_HC = W_CVD  (shared encoding)
And: B_CVD ≠ B_HC  (different responses)
Then: Can we find T such that B_CVD + T ≈ B_HC?
```

---

## 🔬 실험 설계 요약

### Current Experiment (Option 2D)
- **Goal**: Find systematic CVD vs HC difference
- **Method**:
  - Option A: Reference-based (sub-02)
  - Option B: Iterative alignment
  - Option C: Voxel weighting
- **Metrics**:
  - CVD common magnitude
  - Consistency scores
  - Color/voxel-specific patterns

### Future Experiments (If 2D succeeds)
1. **Transformation validation**
2. **Shared W matrix test**
3. **Reconstruction improvement**
4. **Filter simulation**

---

## ⚠️ 중요한 주의사항

### 1. W matrix 가정 검증 필요
- 현재: 가정만 함
- 필요: HC와 CVD에서 각각 W 학습 → 비교
- Test: W_HC와 W_CVD의 correlation

### 2. Transformation의 방향성
- Forward: CVD → HC (analysis)
- Inverse: External stimulus → CVD-friendly (filter)
- 둘이 다를 수 있음!

### 3. Color space vs Brain space
- Transformation은 brain space에서 계산
- Filter는 color space에서 적용
- Mapping 필요!

### 4. Individual differences
- HC 내 variability가 크면
- Filter가 일부 HC도 왜곡시킬 수 있음
- Trade-off 필요

---

## 📌 결론

**초기 목표**: Color filter 제작

**핵심 가정**:
1. CVD ≠ HC (systematic difference) ← **검증 중**
2. W_CVD = W_HC (shared encoding) ← **검증 필요**
3. T exists: CVD + T ≈ HC ← **검증 중**

**현재 단계**: Option 2D로 가정 1 검증 중

**성공 시나리오**: Systematic difference 발견 → T 계산 → Filter 제작

**실패 시나리오**: No systematic pattern → Individual filter or scientific finding

**결과 대기 중**: ~1시간
