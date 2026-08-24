# phase5_filter_optimization

**Status**: Pipeline 2 CLOSURE READY (2026-05-27) → Phase 3 행동 실험 진입 대기

**Project goal**: CVD subject (sub-08 deutan, sub-09 protan) 의 fMRI 기반 *individualized color filter* 추출.

---

## ⭐ 메인 entry point

| 문서 | 용도 |
|---|---|
| **`PIPELINE_2_CLOSURE.md`** | **single source of truth** — 5-step axis narrative, RQ + answers, final candidates, limitations (Phase C seed audit 포함; 옛 PIPELINE_2_AUDIT supersede) |
| `CLAUDE.md` | 프로젝트 instructions (§0 framework decision, assumptions, status) |
| `prior-works.md` | Literature mapping (R+C, 2-Component grounding) |
| `mathematical_basis.md` | Forward model 수학적 배경 |
| `PI-feedback-priorwork.md` | PI feedback tracker |
| `raw_behav.md` | Behavioral JND raw 데이터 노트 |
| `index.md` | 폴더 navigation |

---

## ⭐ Pipeline 2 final candidates

> **현행 main candidate = 2개** (2026-06): **S08-robust (β_s=6, β_c=−42) deutan** · **S09-primary (β_s=2, β_c=+24) protan**.
> **βs-dom (38, −10)은 dropped** — 아래 표의 βs-dom 행은 closure verification 스냅샷으로만 보존된 이력이며 현행 후보 아님.

| Subject | Label | Model | Loss combo | Parameters | Family | bdy | 식별성 (Round 3) |
|---|---|---|---|---|---|---|---|
| sub-08 deutan | **βs-dom** | 2-Component | γ_all + RDM_V1 | β_s=38, β_c=−10 | deutan | 0% | FAIL (β_c sign-flip) |
| sub-08 deutan | **βc-dom** | 2-Component | γ_OY + RDM_V2/V3 | β_s=6, β_c=−42 | deutan | 9% | FAIL (β_c IQR=68) |
| sub-09 protan | **βc-rot** | 2-Component | γ_all + RDM_V1 / γ_GB + RDM_V1 | β_s=2, β_c=24 | protan | **0%** | FAIL (β_c sign-flip) |

**R+C 1-DOF**: 두 subject 모두 *structural insufficient* (boundary saturation 또는 near-saturation) — `PIPELINE_2_CLOSURE.md` §RQ1 + L6 참조.

**식별성 verdict**: Round 3 multi-point recovery 가 모든 candidates 에 대해 FAIL → candidates 는 *descriptive fits at fit point only*, *unique parameter estimates* 가 아님. **Phase 3 행동 실험이 sole verification path** (`PIPELINE_2_CLOSURE.md` §5.2 + L1).

---

## 폴더 구조

```
phase5_filter_optimization/
├── README.md                          ← (본 문서) navigation + final candidates
├── PIPELINE_2_CLOSURE.md              ← MAIN: 5-step axis + RQ + limitations + Phase C seed audit
├── CLAUDE.md                          ← project instructions
├── prior-works.md, mathematical_basis.md, PI-feedback-priorwork.md, raw_behav.md, index.md
├── scripts/                           ← Pipeline 2 code (scripts/README.md 참조)
├── results/                           ← Pipeline 2 output (results/README.md 참조)
├── sbatch/                            ← SLURM submission scripts
├── simulator/                         ← interactive filter simulator (4-col HTML)
├── presentation/                      ← figure/slide assets
├── logs/                              ← run logs
└── archive/                           ← deprecated docs + scripts (superseded_2026-05-27/)
```

---

## 5-step pipeline (간략)

| Step | 역할 | 주 script |
|---|---|---|
| 1. 모델·로스 후보 선정 | precondition (HC LOO gate) | `scripts/s10a_precondition.py` |
| 2. 손실항·조합 후보 소개 | atom 정의 + cell enumeration (no fitting) | `scripts/s10b_v6_pca_rdm.py` (atom factories + enum) |
| 3. 조합 fit + 평가 | 5/2 HC split × 300 + strict HC LOO 7-fold | `scripts/s10b_v6_pca_rdm.py`, `scripts/s17_hc_loo.py` |
| 4. 가중치 sweep sanity check | raw-weight robustness on Step 3 candidates | `scripts/cycle6b_extended_raw_weight.py` |
| 5. 최종 결정 + 식별성 | closure + Phase D Round 3 multi-point sim | `scripts/s13_round3.py` |

각 step 의 자세한 내용은 `PIPELINE_2_CLOSURE.md` 참조.

---

## SRQ — Pipeline 2 답변

| RQ | 결과 (요약) |
|---|---|
| RQ1. R+C vs 2-Component 어느 모델 better? | **2-Component** 양 subject 모두 better. R+C 1-DOF 는 structural insufficiency (cortical confusion-axis DOF 부재) |
| RQ2. 특정 model-loss 가 HC subset 에 robust? | **Yes** — sub-09 (β_s=2, β_c=24) param IQR=(0, 0) deterministic, multiple loss combos 일치 |
| RQ3. CVD/HC 간 일반화 가능? | **No** — CVD N=2, identifiability FAIL, individualized filter framing 만 가능 |
| RQ4. R+C behav fit 이 기존 논문과 일치? Neural 추가 benefit? | R+C g 비교 invalid (방법론 mismatch); **Neural 추가 시 boundary 70% → 0%, β_c 추정 안정화** |
| RQ5. Behav 와 Neural 같은 방향? | Sub-08: agreement; **Sub-09: disagreement** (behav β_c≈0, neural β_c=+24 — neural-only 가 cortical mechanism 노출) |

---

## Closure 이후 next steps

1. **Phase 3 행동 실험 design** — 현행 2 main candidates ((6,−42) S08-robust, (2,+24) S09-primary) 적용 filter 의 색 perception/discrimination 검증
2. **Paper draft** (`PIPELINE_2_CLOSURE.md` §Paper 기반)
3. **Filter visualization** — `simulator/` 의 4-col HTML 활용

---

## Archived

이전 Pipeline 1/3 framework docs 및 session-specific notes: `archive/superseded_2026-05-27/`
