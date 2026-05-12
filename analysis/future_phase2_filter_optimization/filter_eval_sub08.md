# Filter Candidate Evaluation — sub-08 deutan

Source figures: `candidates/` (4 col: Original | CVD perceives | Filtered pre-image | CVD Filtered)
Script: `scripts/visualization/visualize_filter_candidates.py`
Behavioral reports: `raw_behav.md`

---

## 1. Sub-08 원색 지각 (필터 없음, raw_behav.md # Original)

| c | θ | HC 기준색 | sub-08 실제 지각 | 왜곡 수준 |
|---|---|---|---|---|
| c1 | 0° | 빨강 | 빨강에 분홍 섞인 | minor |
| c2 | 45° | 주황 | 연한 빨강 | distorted |
| c3 | 90° | 노랑 | 연두 | distorted |
| c4 | 135° | 초록 | 노랑 | distorted |
| c5 | 180° | 청록 | 웜톤 아이보리 | MAJOR |
| c6 | 225° | 하늘 | 하늘 | preserved |
| c7 | 270° | 파랑 | 더 진한 하늘 | minor |
| c8 | 315° | 마젠타 | 진파랑 | MAJOR |

---

## 2. P2a — 시뮬레이터 예측 정확도 (col2 vs sub-08 원색 지각)

- col2 색상: HC 구두 보고 기준. Canonical/Cycle14 = CURRENT Stockman-corrected formula(θ_pred JSON). V4-only = OLD CIELab-direct formula (primary.png 생성 시점).
- `candidates/primary.png`는 2026-05-10 two_component.py 통합 **이전** OLD formula(Stockman h_base 변환 없음)로 생성됨. V4-only θ_cvd는 OLD formula 기준.
- Canonical/Cycle14는 CURRENT formula로 생성. θ_pred JSON(`candidates/{canonical,cycle14}.json`)과 일치. v4only.json은 2026-05-11 OLD formula 기준으로 업데이트됨 → primary.png 실제 색과 일치.

| c | sub-08 실재 | θ_cvd V4-only (OLD) | col2 색 (HC 구두) | P2a | θ_pred Canonical | col2 색 (HC 구두) | P2a | θ_pred Cycle14 | col2 색 (HC 구두) | P2a |
|---|---|---|---|---|---|---|---|---|---|---|
| c1 | 빨강에 분홍 | 353.9° | 분홍빨강 | ✓ | 345.8° | pinkish | ✓ | 352.4° | pinkish | ✓ |
| c2 | 연한 빨강 | 70.1° | 주황 | ✗ | 24.1° | salmon orange | ✗ | 25.8° | salmon orange | ✗ |
| c3 | 연두 | 131.5° | 초록 | partial | 64.4° | orange | ✗ | 61.8° | orange | ✗ |
| c4 | 노랑 | 168.6° | 청록 | ✗ | 106.0° | yellowish green | ✗ | 99.8° | yellowish green | ✗ |
| c5 | 웜톤 아이보리 | 186.1° | 청록 | ✗ | 148.5° | green | ✗ | 138.7° | green | ✗ |
| c6 | 하늘 | 199.9° | 하늘 | ✓ | 194.0° | teal-cyan | partial | 174.4° | teal | ✗ |
| c7 | 더 진한 하늘 | 228.5° | 하늘-시안 | ✓ | 301.6° | purple | ✗ | 311.8° | purple | ✗ |
| c8 | 진파랑 | 281.4° | 파랑 | ✓ | 320.7° | pinkish purple | ✗ | 337.6° | pinkish | ✗ |
| **합계** | | | | **4+1p/8** | | | **1+1p/8** | | | **1/8** |

---

## 3. P1 & P2b — 필터 효과 (col4 = CVD Filtered, raw_behav.md)

- P1: col4가 HC 목표 색 계열인가?  P2b: sub-08이 HC 목표 색으로 보고했는가?

### Canonical (β_s=38, β_c=−14) — `candidates/canonical.png`

| c | HC 목표 | sub-08 필터 후 보고 | P1 | P2b |
|---|---|---|---|---|
| C1 | 빨강 | 분홍기 줄고 순수한 빨강 | ✓ | ✓ |
| C2 | 주황 | 약간 초록, 색 옅음 | ✗ | ✗ |
| C3 | 노랑 | C4와 같은 노랑 (collapse) | partial | partial |
| C4 | 초록 | C3와 같은 노랑 (unchanged) | ✗ | ✗ |
| C5 | 청록 | C6와 같은 하늘 (collapse) | partial | partial |
| C6 | 하늘 | C5와 같은 하늘 | neutral | partial |
| C7 | 파랑 | 더 짙은 파랑 | ✓ | ✓ |
| C8 | 마젠타 | 변화 없음 (진파랑 유지) | ✗ | ✗ |
| **합계** | | | **2+2p/8** | **2+2p/8** |

### V4-only (β_s=38, β_c=+7) — `candidates/primary.png`

- **⚠ 방법론적 주의**: primary.png는 OLD CIELab-direct formula로 생성. **이 P1/P2b는 OLD formula V4-only 필터에 대한 sub-08의 실제 행동 보고 (OLD formula 기준 행동검증 완료).** 다만 cycle10d 최적화(β_s=38, β_c=+7)는 CURRENT Stockman formula로 결정되었으므로, CURRENT formula 기준 V4-only pre-image는 primary.png와 다름 → **CURRENT formula V4-only는 행동검증 미완료.**

| c | HC 목표 | sub-08 필터 후 보고 | P1 | P2b |
|---|---|---|---|---|
| C1 | 빨강 | 언급 없음 | — | — |
| C2 | 주황 | 더 짙은 빨강 | ✗ | ✗ |
| C3 | 노랑 | 연한 주황 | partial | ✗ |
| C4 | 초록 | 연한 연두 | partial✓ | partial |
| C5 | 청록 | 완전 옅은 연두 | ✗ | ✗ |
| C6 | 하늘 | 더 진한 하늘 | ✓ | ✓ |
| C7 | 파랑 | 완전 짙은 파랑 | ✓ | ✓ |
| C8 | 마젠타 | 핑크빛 섞인 보라 | partial | partial |
| **합계** | | | **2+3p/8** | **2+2p/8** |

### Cycle 14 (β_s=58, β_c=−36) — `candidates/cycle14.png`

| c | HC 목표 | sub-08 필터 후 보고 | P1 | P2b |
|---|---|---|---|---|
| C1 | 빨강 | 보라→핑크 (역방향) | ✗ | ✗ |
| C2 | 주황 | 더 옅은 주황 | partial | partial |
| C3 | 노랑 | 연한 주황→노랑 | ✓ | ✓ |
| C4 | 초록 | 연둣빛 노랑→웜톤 아이보리 | ✗ | ✗ |
| C5 | 청록 | 웜톤 아이보리→하늘 | ✓ | ✓ |
| C6 | 하늘 | 약간 진한 하늘 | ✓ | ✓ |
| C7 | 파랑 | 파랑→하늘 (역방향) | ✗ | ✗ |
| C8 | 마젠타 | 진한 파랑→파랑 | ✗ | ✗ |
| **합계** | | | **2+1p/8** | **3/8** |

---

## 4. HC Specificity (descriptive only — §0 rule, CLAUDE.md §2.6)

HC V4 norms: [44.4, 26.3, 49.2, 36.8, 42.0, 42.2]° (mean=40.1°, std=7.9°)

| 필터 | norm | boot_frac | 판정 |
|---|---|---|---|
| Canonical (38,−14) | 40.5° | 0.517 | ✗ HC 내부 |
| V4-only (38,+7) | 38.6° | 0.299 | ✗ HC 평균 이하 |
| Cycle14 (58,−36) | 68.3° | 1.000 | ✓✓ HC 범위 초과 |

Script: `python scripts/hc_specificity_check.py --beta_s <v> --beta_c <v> --cvd_type deutan --roi V4`

---

## 5. Windows 비교 (P2a 없음 — 시뮬레이터 아님)

| c | HC 목표 | sub-08 Windows 후 보고 | P1 |
|---|---|---|---|
| C1 | 빨강 | 핑크→빨강 | ✓ |
| C2 | 주황 | 같은 주황 | ambiguous |
| C3 | 노랑 | 연두→옅은 주황 | partial |
| C4 | 초록 | 노랑→연두 | partial✓ |
| C5 | 청록 | 웜톤→쿨톤 아이보리 | partial |
| C6 | 하늘 | 같은 하늘 | ✓ |
| C7 | 파랑 | 같은 파랑 | ✓ |
| C8 | 마젠타 | 진파랑→보라 (식별 어려움) | partial |
| **합계** | | | **3+4p/8** |

---

## 6. 종합 요약

| 필터 | P2a | P1 | P2b | HC spec | 행동검증 범위 |
|---|---|---|---|---|---|
| V4-only (38,+7) | **4+1p/8** | 2+3p/8 | 2+2p/8 | ✗ | OLD formula 기준 완료; CURRENT formula 미완료 |
| Canonical (38,−14) | 1+1p/8 | 2+2p/8 | 2+2p/8 | ✗ | CURRENT formula 기준 완료 (behav §3 PASS) |
| Cycle14 (58,−36) | 1/8 | 2+1p/8 | 3/8 | ✓✓ | CURRENT formula 기준 완료 |
| Windows | N/A | 3+4p/8 | N/A | N/A | 완료 (공식 개념 없음) |

**핵심 관찰:**
- V4-only P1/P2b는 OLD formula pre-image 기반 행동검증. CURRENT formula V4-only의 pre-image는 다르므로 별도 검증 필요
- V4-only P2a 4+1p/8: OLD formula가 c6·c7·c8 예측 정확. CURRENT formula는 c7=purple → V4-only만 c7 ✓
- c5 (웜톤 아이보리): 어떤 모델도 재현 불가 — 구조적 한계
- C5 보정 (아이보리→하늘): Canonical/Cycle14 달성, Windows partial
- C3/C4 collapse: Canonical에서만 발생
- Windows P1 경쟁적 (신경 개인화 없이도)
