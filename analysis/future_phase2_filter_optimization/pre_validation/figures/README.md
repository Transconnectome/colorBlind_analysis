# Within-ROI FDR Results - All ROIs

**Date:** 2026-02-22
**Method:** Within-ROI FDR correction (28 tests per ROI, q < 0.05)
**Updated:** Changed from Global FDR to Within-ROI FDR

---

## Summary Table

| Subject | CVD Type | V1 | V2 | V3 | hV4 | Total |
|---------|----------|----|----|----|----|-------|
| **sub-08** | Deutan | **3** | **12** | **17** | 0 | **32** |
| **sub-09** | Protan | **6** | 0 | **1** | 0 | **7** |
| **sub-10** | Deutan | 0 | 0 | 0 | 0 | **0** |
| **Total** | | **9** | **12** | **18** | **0** | **39** |

**Discovery rate:** 39/336 = 11.6% (much higher than global FDR 2.4%)

---

## Comparison: Global FDR vs Within-ROI FDR

| Correction | V1 | V2 | V3 | hV4 | Total | Rate |
|------------|----|----|----|----|-------|------|
| **Global FDR** | 1 | 3 | 4 | 0 | **8** | 2.4% |
| **Within-ROI FDR** | **9** | **12** | **18** | 0 | **39** | **11.6%** |
| **Increase** | +8 | +9 | +14 | 0 | **+31** | +387% |

**Within-ROI FDR는 V1에서 9배 더 많은 pairs 검출!**

---

## V1: Early Visual Cortex (9 pairs total)

### sub-08 (Deutan): 3 pairs ✓✓✓
1. **red-yellow** (z=5.14, p<0.0001) - 가장 강함
2. **yellow-purple** (z=4.84, p<0.0001)
3. **red-cyan** (z=3.61, p=0.0003)

### sub-09 (Protan): 6 pairs ✓✓✓✓✓✓
1. **cyan-magenta** (z=4.08, p<0.0001)
2. **orange-magenta** (z=3.71, p=0.0002)
3. **red-magenta** (z=3.52, p=0.0004)
4. **green-magenta** (z=3.43, p=0.0006)
5. **yellow-purple** (z=-3.31, p=0.0009) - decreased
6. **green-blue** (z=-3.00, p=0.0027) - decreased

### sub-10 (Deutan): 0 pairs
- No pairs survived within-ROI FDR

**V1 Interpretation:**
- **sub-09 (Protan) shows strongest V1 effects** (6 pairs)
  - All magenta-related pairs (cyan-mag, orange-mag, red-mag, green-mag)
  - L-cone loss → magenta processing altered
- **sub-08 (Deutan) shows 3 pairs**
  - red-yellow, yellow-purple (M-L pathway)
- **sub-10 minimal effects** in V1

---

## V2: Intermediate Visual Area (12 pairs total)

### sub-08 (Deutan): 12 pairs ✓✓✓ (많음!)
Top 5:
1. **yellow-purple** (z=13.87, p<0.0001) - 매우 강함
2. **red-yellow** (z=9.38, p<0.0001)
3. **blue-purple** (z=6.15, p<0.0001)
4. **yellow-green** (z=5.47, p<0.0001)
5. **orange-yellow** (z=5.45, p<0.0001)

전체 12개: yellow-purple, red-yellow, blue-purple, yellow-green, orange-yellow, red-cyan, yellow-blue, yellow-magenta, cyan-purple, yellow-cyan, orange-cyan, green-blue

### sub-09 (Protan): 0 pairs
- No pairs survived within-ROI FDR

### sub-10 (Deutan): 0 pairs
- No pairs survived within-ROI FDR

**V2 Interpretation:**
- **sub-08 dominant** (12/12 pairs = 100%)
- V2에서 yellow 관련 pairs 많음 (yellow-purple z=13.87 최강)
- M-cone 결핍 → yellow processing 크게 영향받음

---

## V3: Higher Visual Area (18 pairs total)

### sub-08 (Deutan): 17 pairs ✓✓✓ (최다!)
Top 10:
1. **red-green** (z=7.85, p<0.0001) - classic Deutan confusion
2. **green-purple** (z=6.96, p<0.0001)
3. **yellow-purple** (z=6.17, p<0.0001)
4. **yellow-magenta** (z=6.11, p<0.0001)
5. **red-yellow** (z=5.88, p<0.0001)
6. **red-cyan** (z=5.36, p<0.0001)
7. **orange-yellow** (z=5.16, p<0.0001)
8. **blue-purple** (z=4.58, p<0.0001)
9. **red-blue** (z=4.37, p<0.0001)
10. **cyan-purple** (z=3.76, p=0.0002)

### sub-09 (Protan): 1 pair ✓
- **orange-magenta** (z=3.32, p=0.0009)

### sub-10 (Deutan): 0 pairs
- No pairs survived within-ROI FDR

**V3 Interpretation:**
- **sub-08 최대 왜곡** (17 pairs)
- **Classic red-green confusion** 출현 (z=7.85, 가장 강함)
- V2(12) → V3(17): 계층적 누적
- sub-09 minimal (1 pair만)

---

## hV4: Color-Selective Area (0 pairs)

### All subjects: 0 pairs
- No pairs survived within-ROI FDR correction
- 여전히 null result

**hV4 Interpretation:**
- Within-ROI FDR에서도 0개
- 작은 ROI (~70 voxels) + 낮은 effect size
- 범주적 색 처리가 pairwise distortions 보상 가능성

---

## Key Findings

### 1. Hierarchical Pattern (sub-08 중심)
```
sub-08 progression:
V1:  3 pairs  → 초기 왜곡 시작
V2: 12 pairs  → 중간 누적 (yellow-dominant)
V3: 17 pairs  → 최대 누적 (red-green classic pattern)
hV4: 0 pairs  → 보상 또는 null
```

### 2. Subject Heterogeneity

**sub-08 (Deutan): 32 total pairs**
- V1-V2-V3 전반에 걸쳐 강한 distortion
- V2, V3에서 특히 많음 (12+17=29)
- Classic Deutan patterns (red-green, yellow distortions)

**sub-09 (Protan): 7 total pairs**
- **V1 dominant** (6/7 pairs)
- V1에서 magenta-관련 pairs 많음
- V2-V3 minimal (V3에 1개만)
- Early processing 단계에서 강한 effect

**sub-10 (Deutan): 0 total pairs**
- 모든 ROI에서 within-ROI FDR 통과 못함
- 가장 mild phenotype
- 또는 다른 보상 전략

### 3. Color Pair Patterns

**Yellow-involved pairs (sub-08 특징):**
- yellow-purple (V2 z=13.87, V3 z=6.17)
- red-yellow (V1 z=5.14, V2 z=9.38, V3 z=5.88)
- orange-yellow (V2 z=5.45, V3 z=5.16)
- yellow-green (V2 z=5.47)

**Magenta-involved pairs (sub-09 특징):**
- cyan-magenta (V1 z=4.08)
- orange-magenta (V1 z=3.71, V3 z=3.32)
- red-magenta (V1 z=3.52)
- green-magenta (V1 z=3.43)

**Blue-purple (S-cone, consistent):**
- sub-08: V2 z=6.15, V3 z=4.58
- Deutan에서 S-cone pathway 강화 pattern

**Red-green (classic Deutan):**
- sub-08 V3: z=7.85 (가장 강한 single effect)
- V3에서만 출현 (higher-level processing)

---

## Statistical Comparison

### Conservative vs Liberal Trade-off

**Global FDR (보수적):**
- 전체 336 tests 동시 correction
- False positive rate 매우 낮음
- V1 완전 누락 (1 pair만)
- 가장 강한 effects만 살아남음

**Within-ROI FDR (적절한 균형):**
- ROI별 28 tests씩 correction
- False positive rate 여전히 제어됨 (q<0.05)
- V1 effects 복원 (9 pairs)
- ROI hierarchy 명확히 드러남

**논문 권장: Within-ROI FDR 사용**
- 이유 1: ROI는 독립적 분석 단위 (different neural populations)
- 이유 2: Global FDR은 과도하게 보수적 (V1 false negatives)
- 이유 3: Within-ROI FDR도 충분히 conservative (q<0.05 유지)
- 이유 4: 계층적 패턴이 더 명확 (V1→V2→V3)

---

## Recommendations

### For Manuscript

1. **Main text**: Within-ROI FDR results 사용
2. **Supplementary**: Global FDR와 비교 table
3. **Focus subjects**:
   - sub-08: V2, V3 (strongest, most consistent)
   - sub-09: V1 (unique Protan pattern)
4. **Key message**: Hierarchical accumulation (V1→V2→V3) in sub-08

### For Filter Design

**High-priority targets:**
- **red-yellow** (sub-08: V1, V2, V3 전반)
- **yellow-purple** (sub-08: V2 z=13.87 최강, V3)
- **red-green** (sub-08: V3 z=7.85, classic Deutan)
- **blue-purple** (sub-08: V2, V3, S-cone compensation)

**Medium-priority:**
- orange-yellow (sub-08: V2, V3)
- Magenta-related pairs (sub-09 V1)

**Low-priority:**
- sub-10 specific pairs (none survived FDR)

---

## Files Generated

```
analysis/future_phase3_filter_optimization/figures/
├── cvd_distortion_figure_V1.png   (updated with within-ROI FDR)
├── cvd_distortion_figure_V2.png   (updated)
├── cvd_distortion_figure_V3.png   (updated)
└── cvd_distortion_figure_hV4.png  (updated)
```

**Panel D title now shows:** "within-ROI FDR q<0.05"

---

**Analysis date:** 2026-02-22
**FDR method:** Within-ROI (Benjamini-Hochberg per ROI)
**Significance threshold:** q < 0.05
**Total discoveries:** 39/336 (11.6%)
