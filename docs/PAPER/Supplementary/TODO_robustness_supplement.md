# TODO — Forward-model 강건성 / 다중비교 Supplementary (미작성)

> 기록일 2026-07-22. 상태: **보류** — `docs/presentation/Project_colorblind_v2.pptx` 슬라이드 검토를 마친 뒤 반영한다.
> 배경: 발표 슬라이드 24·26이 방어하는 논점이 논문 본문·부록에는 하나도 들어 있지 않다.
> `docs/PAPER/` 전체(.tex/.md) 검색 결과 아래 4개 항목 모두 **0건**.
> (`omnibus` 2건은 `Methods/methods_v2_HYBRID_backup.tex:139`,
> `Methods/methods_v2_prewrap_backup.tex:141` — LOSO pairwise generalization의 별개 검정이며,
> 두 파일 모두 `_backup`이라 `main.tex`의 `\input` 체인 밖이다.)

**범위 결정**: GCV λ(α) plateau/안정성 점검은 **이번 범위에서 제외**한다 — 현재 파이프라인에서 GCV를 거의 쓰지 않는다.
(참고 수치는 `analysis/phase4_forward_model/RESULTS.md:290-299`에 남아 있음.)

## 추가할 항목 (4개)

| # | 항목 | 근거 위치 | 핵심 수치 |
|---|---|---|---|
| 1 | Stouffer omnibus | `RESULTS.md:853` (§4c N1) | Z = 2.869, p = 0.0021 |
| 2 | Fisher omnibus | 〃 | χ²(8) = 21.18, p = 0.0067 |
| 3 | Friedman 색별 균일성 검정 | `RESULTS.md:268` | hV4 χ²(7)=6.48, p=0.485 (uniform) / V1 p=0.011, V2 p=0.047 (non-uniform) |
| 4 | 잔차 RDM 분석 | `RESULTS.md:278`, `scripts/residual_structure_loco.py` | r(resid,orig): hV4 0.053 vs V1 0.453 / V2 0.454 / V3 0.329 |

### 1–2. Stouffer / Fisher omnibus

목적: Red Team FATAL #2 중화 — "hV4 p=0.026은 Bonferroni-4(α=0.0125)를 통과하지 못하고, 4 ROI × 6+ basis = 24개 이상 검정을 돌렸다".
주장 단위를 개별 ROI에서 **피질 수준 1개 omnibus**로 올린다.

2단계 위계적 결합: ① ROI 내부에서 HC 7명의 per-subject permutation p를 Stouffer 결합 → ROI별 p, ② ROI 4개 p를 다시 결합 → omnibus.

| ROI | basis | Stouffer Z | p |
|---|---|---|---|
| V1 | FE-2 | 0.956 | 0.170 |
| V2 | FE-3 | 1.149 | 0.125 |
| V3 | FE-8 | 1.692 | 0.045 |
| hV4 | FE-3 | 1.941 | 0.026 |

서술 시 반드시 포함할 것:

- **Stouffer를 primary로 두는 이유**: p<0.01인 ROI가 하나도 없고 V1→V2→V3→hV4의 단조 gradient가 있다. 즉 single hotspot(Fisher 민감)이 아니라 distributed pattern(Stouffer 민감). Stouffer p=0.002 < Fisher p=0.007이라는 비대칭 자체가 정보다.
- **post-hoc 한계**: 개별 ROI 중 Bonferroni-4를 통과하는 것은 **없다**. V3/hV4가 uncorrected로 marginal일 뿐.
- omnibus는 **방어**이지 hV4 특이성의 근거가 아니다. 특이성은 항목 3·4가 담당한다.

### 3. Friedman 색별 균일성

hV4만 8색에 걸쳐 보간 성능이 균일 → GO가 특정 색 하나에 끌려간 결과가 아님. V1/V2는 non-uniform (Blue/Cyan 높고 Yellow/Green 낮음).

### 4. 잔차 RDM

8색 전체 ridge 적합 → 잔차의 correlation-RDM ↔ 원 색 RDM upper-triangle **Spearman**.
hV4 잔차만 사실상 무구조(0.053) = 모형이 가용 구조 대부분 포착. V1/V2 잔차에는 색 기하가 남음 = under-fit → "V1/V2 discrimination-only" 해석의 근거.

## 작성 전에 반드시 해소할 문제 (2건)

1. **순환성 — omnibus 입력이 per-ROI *optimal* basis다.** FE-2/3/8/3은 basis 탐색의 산물인데, 이 omnibus가 방어하려던 대상이 바로 그 basis 탐색("4 ROI × 6+ basis")이다. 다중비교를 해결하려는 검정이 다중비교로 고른 값을 입력받고 있다. 리뷰어가 확실히 찌를 지점.
   - canonical **FE-6 uniform** (Methods 기준 basis, 프로젝트 정책) 기준 ROI별 p = 0.126 / 0.154 / 0.367 / 0.039. **이 조합의 omnibus는 아직 계산되어 있지 않다.** 계산해서 병기할 것.
2. **잔차 분석은 in-sample이다** — 8색 전부로 학습한 잔차이며 held-out이 아니다. "모형 적정성"의 방증으로만 쓰고 LOCO 성능의 독립 검증으로 서술하지 말 것.

추가로, 세 축(Friedman / 잔차 / omnibus)은 **동일한 48 샘플의 서로 다른 분석**이므로 독립 증거가 아니라 다면적 특성화다 (Red Team 취약점 #1, `RESULTS.md:834`). "N개의 수렴하는 독립 증거" 식 표현 금지.

## 반영 시 위치

- `docs/PAPER/Supplementary/` 에 신규 `.tex` 1개 (번호 미정 — S3/S16과 충돌 없게)
- `main.tex` 의 `\input` 체인에 등록 (현재 `Supplementary/S3_identifiability`, `Supplementary/S16_filter_eval_design` 다음)
