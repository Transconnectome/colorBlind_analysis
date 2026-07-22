# Introduction 인용 뒷받침 제안 (검토용 · 상세점검 별도)

> 작성 2026-07-14. 출처 = NotebookLM `ColorBlind_comprehensive`(174 sources) 질의 검증.
> 목적: abstract Gap의 두 주장(① generic 필터 discrimination 개선 미미, ② subtype 내 개인차 → group-level 부적절)을 Introduction에서 뒷받침하는 인용 현황 + 보강 제안.
> **결론 먼저: 현 intro(introduction_v2.tex)가 두 주장을 이미 뒷받침함. 필수 추가 없음. 선택적 보강만 아래.**

---

## Claim ① — Generic/population-average 필터는 appearance만 바꾸고 discrimination은 개선 못함

**현 intro 커버리지 (이미 있음):**
- `introduction_v2.tex:57` — *"population-average filters shift the appearance of color while leaving generalized color discrimination largely unchanged"* `\citep{somers2024}` ✅
- `:57` — *"Color-enhancing glasses improved discrimination for only one of two consumer products tested"* `\citep{patterson2022}` ✅
- `:66` — post-receptoral 보상이 threshold에서 안 나타남 `\citep{basim2025}` ✅ (기전)

**추가 후보 (선택, NotebookLM 근거):**
| 논문 | 연도/venue | 주장 | 추가 가치 |
|---|---|---|---|
| Somers, Franklin & Bosten | 2024, *Vision Research* 218:108390 | EnChroma: appearance(saturation)↑ 유의, **discrimination threshold 개선 미미(red만)** | 이미 인용 ✅ (가장 직접적) |
| Marques et al. | 2023 | natural colors, EnChroma/Vino **discrimination 무효** | 선택 — somers와 중복 |
| Álvaro et al. | 2022 | sorting error 무효 + 소요시간↑ | 선택 |
| Basim, Goddard, Yang & Webster | 2025, *J Vision* 25(10):17 | 보상 "not manifest at threshold, limited by intrinsic noise" | 이미 인용 ✅ |

→ **Claim ① : 추가 불필요.**

---

## Claim ② — CVD는 subtype 내에서도 개인차 → one-size-fits-all 부적절

**현 intro 커버리지 (이미 있음):**
- `introduction_v2.tex:57` — *"the phenotype varies markedly even within one diagnostic category"* `\citep{bosten2019}` ✅
- `:66` — 개인별 보상 편차 `\citep{emery2021, boehm2014, tregillus2021}` ✅

**추가 후보 (선택):**
| 논문 | 연도/venue | 주장 | 추가 가치 |
|---|---|---|---|
| Bosten | 2019 (*known unknowns of anomalous trichromacy*) | "discrete labels obscure the plethora of individual variation"; Δλmax 1–12 nm | 이미 인용 ✅ |
| **Tian et al.** | **2022** (*Inverse-Designed Aid Lenses for Precise Correction of CVD*) | "none of the current lenses provides a customized correction ... undesirable correction effects" → 환자별 Δλ 측정해 inverse-design | ➕ **권장 후보** — "개인화 교정 시도" 선행연구로 §Intro-2/3 강화. 우리 접근(cortical 개인화)과 대비(그들은 retinal 개인화). |
| Zhu et al. | 2021 | 정적 channel 조정은 "personal degree of CVD" 무시 → 개인 calibration 필요 | 선택 — software recoloring 계열 |

→ **Claim ② : 필수 없음. Tian 2022 추가 시 "개인화 교정이 이미 시도됐으나 retinal 수준에 머묾" 대비가 선명해짐** (우리의 cortical-level 차별점 부각). intro line 57의 "personalize at the retinal rather than the cortical level" 서술과 잘 맞음.

---

## 한 줄 제안
- **필수 추가 없음** (현 intro가 abstract Gap을 충분히 뒷받침).
- **선택 1건**: `\citep{tian2022}`를 §Intro-2(현행 CVD 교정 한계, line 55–57)에 추가 — retinal-level 개인화 선행연구로. bib에 없으면 추가 필요.
- 상세 문안 점검은 사용자 별도 진행.
