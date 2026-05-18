# Sub-08 label 정정 후 한계 재평가 및 개선 제안 (2026-05-15)

**Trigger**: 사용자가 c7/c8 label과 실제 STIM_LAB 렌더링의 불일치를 지적.

## 1. Label 정정 (STIM_LAB 실제 렌더링 기반)

| c | θ | OLD label | actual render (RGB) | NEW label |
|---|---|---|---|---|
| c1 | 0° | red | [240, 89, 146] #F05992 | **pink** |
| c2 | 45° | orange | [247, 116, 72] #F77448 | red-orange |
| c3 | 90° | yellow | [159, 135, 58] #9F873A | **olive** |
| c4 | 135° | green | [92, 189, 67] #5CBD43 | green |
| c5 | 180° | cyan | [66, 203, 182] #42CBB6 | cyan |
| c6 | 225° | sky | [0, 186, 222] #00BADE | **sky-cyan** |
| c7 | 270° | violet/purple | [0, 152, 247] #0098F7 | **sky-blue** |
| c8 | 315° | magenta | [182, 118, 222] #B676DE | **violet** |

★ 5개 label이 mismatch였습니다. 특히 c7 (violet→sky-blue), c8 (magenta→violet)이 핵심.

## 2. Sub-08 ORIGINAL 보고 vs CORRECTED actual render

| c | 실제 렌더 | sub-08 보고 | 평가 |
|---|---|---|---|
| c1 | pink | 핑크 | **OK** ✓ |
| c2 | red-orange | 초록 | deutan miss (red→green collapse) |
| c3 | olive | 초록 | deutan miss (olive merge with green) |
| c4 | green | 연두 | minor miss |
| c5 | cyan | 아이보리 | deutan miss (cyan→warm olive) |
| c6 | sky-cyan | 탁한 하늘 | **OK** ✓ |
| c7 | sky-blue | 파랑 | **OK** ✓ |
| c8 | violet | 진한 파랑 | deutan miss (violet→blue-violet adjacent) |

**핵심**: sub-08은 c1, c6, c7을 NATIVE-LIKE perceive함 (label 정정 후 명확).

## 3. CURRENT (40, +26) 한계 — corrected labels로 재평가

P2a 변화: **0.575 (OLD vocab) → 0.500 (CORRECTED vocab)**

### Per-color analysis

| c | filter col 3 RGB | sub-08 보고 | target (CORRECTED) | 평가 |
|---|---|---|---|---|
| c1 | #F85B7F pink | 연한 빨강 | pink | ✓ |
| c2 | #FC6A5A red-orange | 초록+빨강주황 | red-orange | partial (deutan miss inevitable) |
| c3 | #DE7D3B orange-brown | 초록 | olive | **✗ MERGE — model class limit** |
| c4 | #A98637 olive | 초록 | green | partial (olive→green adjacent) |
| c5 | #7CAF35 olive-green | 연두 | cyan | **✗ filter mis-targeted** |
| c6 | #4F91F7 sky-blue | 탁한 하늘 | sky-cyan | ✓ |
| c7 | #C271D6 violet/purple | 보라 | sky-blue | **✗ FILTER DESTROYED correct perception** |
| c8 | #E85DA9 pink | 핑크 | violet | **✗ FILTER DESTROYED correct perception** |

### 진짜 한계 (label 정정 후 명확)

1. **c3 → 초록 (model class limit)**: orange-brown 렌더가 sub-08의 wide "초록" 카테고리에 머지. hue-only 모델 + STIM_LAB 렌더러 조합의 본질적 한계.

2. **c7, c8 → filter-induced damage**: sub-08이 ORIGINAL을 correct하게 봤던 c7 (sky-blue→파랑), c8 (violet→진한 파랑)을, CURRENT (40, +26)의 큰 β_c=+26 rotation이 col 3 pre-image을 purple/pink로 밀어 sub-08이 **wrong한 perception**을 reports하게 함.

3. **c5 → filter mis-targeted**: cyan 원본이 olive-green으로 pre-image 이동 → sub-08 deutan miss 유발.

c7/c8 한계는 **filter가 적극적으로 만든 한계** — corrected labels로만 보이는 것.

## 4. 개선 방향 — grid 내 corrected-label-best 후보

| 후보 | bs | bc | P2a (corrected) | exact | ΔL from neural argmin |
|---|---|---|---|---|---|
| CURRENT | 40 | +26 | 0.500 | 2/8 | 0 (global argmin) |
| **(24, -22)** | **24** | **-22** | **0.750** | **2/8** | **+0.265** |
| (26, -22) | 26 | -22 | 0.750 | 2/8 | +0.276 |
| (24, -24) | 24 | -24 | 0.750 | 2/8 | +0.271 |
| (28, -22) | 28 | -22 | 0.750 | 2/8 | +0.399 |

### (24, -22) — primary 추천 후보

Per-color predicted under CORRECTED labels:
- c1: pink/pink ✓
- c2: red-orange/green (model can't fix deutan miss for orange→green)
- c3: olive/green (model class merge — c3 limitation 잔존)
- c4: green/yellow-green (adjacent)
- c5: cyan/olive (deutan miss for cyan→olive)
- **c6: sky-cyan/sky-cyan ✓** (preserved)
- **c7: sky-blue/sky-blue ✓** (preserved — vs CURRENT의 보라/violet 머지)
- **c8: violet/blue-violet** (adjacent — vs CURRENT의 핑크/pink 머지)

### 정당화

(24, -22)는:
- ✅ **신경 loss formulation 변경 없음** (Option C composite 동일)
- ✅ **임의 constraint 추가 없음** — 단순히 corrected-label P2a가 maximum인 grid cell
- ⚠️ **Globally argmin은 아님** (ΔL = +0.265 over Option C 신경 best (40, +26))

### Trade-off
- Neural fit: (40, +26)이 V4 LOCO best (L_topk=0.000 unique zero). (24, -22)는 L_topk=0.500.
- Behavior (corrected): (24, -22)가 P2a 0.750, CURRENT은 0.500.
- **이는 신경 ↔ 행동 dissociation을 노출**. 신경 모델이 c7/c8을 over-rotate 하지만 행동상 손상.

## 5. 남은 한계 (label 정정 후에도)

### A. C3 → 초록 (model class limit)
어떤 candidate를 선택해도:
- 90° 근처 pre-image (olive 렌더링) → sub-08 "초록"
- ≤45° pre-image (red-orange) → sub-08 "주황+빨강" (no longer olive)
- → 본질적으로 hue-only 모델 + sub-08의 wide "초록" 카테고리로 인한 제약.

### B. C2, C5의 deutan miss
- c2 (red-orange render) → sub-08 sees green (deutan absorbs red into green)
- c5 (cyan render) → sub-08 sees olive (deutan miss)
- 둘 다 sub-08의 ORIGINAL perception이 already wrong. Filter는 이를 못 고침 — 모델이 hue만 manipulate.

### C. 모든 deutan-affected 색의 model class limit
Sub-08의 deutan은 단순 hue rotation이 아닌 **saturation/lightness-dependent categorization**을 동반 ("밝은 주황 → 주황 / 어두운 주황 → 초록"). 2-component cosine는 hue만 → 본질적 한계.

## 6. 권고

1. **Label 정정을 codebase에 반영** — `HC_NAME_BINS`, `SUB08_ORIGINAL_HC_EQUIV`, `HC_TARGETS` 업데이트.
2. **(24, -22)를 행동 검증 대상으로 제시** — c7/c8 보호 효과 확인.
3. **C3 한계는 model class limit으로 manuscript에 명시** — saturation/chroma 항 도입 (Phase 4) 또는 fine hue resolution 추가 fMRI 데이터가 본질적 해결책.
4. **신경 ↔ 행동 dissociation을 핵심 finding으로 보고**: V4 LOCO best fit이 perceptual best fit이 아님. 

## 7. 생성된 파일

- `results/c3_relabel/relabel_audit.json` — STIM_LAB 렌더링 vs label 비교 raw data
- `results/c3_relabel/p2a_corrected_labels.json` — P2a grid 결과 (corrected vocab)
- `results/c3_relabel/RELABEL_24m22_4col_sub-08.png/pdf` — **(24, -22) 행동 검증용**
- `results/c3_relabel/RELABEL_26m22_4col_sub-08.png/pdf` — 대안 (26, -22)
- `results/c3_proposals/c3prop_CURRENT_4col_sub-08.png` — CURRENT 비교용
- `scripts/c3_relabel_audit.py` — label audit
- `scripts/c3_relabel_p2a.py` — corrected-label P2a 계산

## 8. 결론

**Label 정정이 분석을 근본적으로 바꿉니다**:
- CURRENT (40, +26)의 c8=핑크 한계는 **label-mismatch artifact가 아닌 진짜 filter 손상**
- CURRENT의 c7=보라 한계도 **filter가 만든 손상** (이전엔 보이지 않았음)
- C3=초록 한계는 **여전히 진짜** — model class limit

**(24, -22)가 corrected-label P2a maximum** (0.750). 신경 fit ΔL=+0.265 손실로 c7/c8 preservation 가능. C3 한계는 모델 한계로 잔존.

BEST_summary.json은 변경하지 않았습니다 — 행동 검증 결과를 바탕으로 사용자 결정 후 업데이트할 사안입니다.
