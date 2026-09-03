# superseded_loro_recompute

**아카이브 일자**: 2026-09-02 · **대체한 것**: `results/loro_eightway_arms.json` + `scripts/_loro_eightway_arm.py` (README §2.5)

`future_phase1_sensitivity/README.md` 의 구 §2.5 "LORO 8-way 색 식별" 표를 여기로 옮겼다. **인용 금지**이며, 원고에 들어간 값은 §2.5 의 재산출판이다.

## 폐기 사유

이 표의 **HC 평균이 발표본과 어긋난다.** CVD 셀은 발표본과 일치하므로 오랫동안 문제가 드러나지 않았다.

| ROI | 구 표 HC | 발표본 HC (`tab:alignment`) | 차이 |
|---|---|---|---|
| V1 | 0.571 | 0.580 | $-0.009$ |
| V2 | 0.574 | 0.607 | $-0.033$ |
| V3 | 0.589 | 0.574 | $+0.015$ |
| hV4 | 0.500 | 0.488 | $+0.012$ |

원인은 **readout 이 다르다**는 것이다. 발표본 LORO(`tab:alignment` 의 Procrustes 열)는 `phase3_decoder_comparing` 의 `ForwardEncoding acc_exact` 이고, 구 표는 진폭 위에서 직접 계산한 값이다. 구 README 가 *"정확 재현이 아니라 구조적 확인"* 이라고 단서를 달아 둔 것이 이 차이를 가리킨다.

2026-09-02 에 LOCO 쪽 관례(FE-6 uniform basis + OLS pseudoinverse)로 LORO 를 직접 재구현해 확인한 결과도 발표본과 어긋났다(HC V2 0.568 vs 0.607, deutan V3 0.354 vs 0.396). 즉 **손으로 재구현하는 경로로는 발표본 LORO 가 재현되지 않으며**, 정본 드라이버 `loro_baseline.py` 를 arm 트리에 그대로 돌리는 것이 유일한 정확 경로다.

**이 표를 산출한 스크립트는 저장소에 없다.** 임시 계산이었으므로 값을 검산할 방법이 남아 있지 않다는 점도 폐기 사유에 포함된다.

## 보존된 표 (인용 금지)

### LORO 8-way 색 식별 (chance = 0.125) — 구 §2.5

| ROI | HC 정본 / hmc | deutan 정본 / hmc | protan 정본 / hmc |
|---|---|---|---|
| V1 | 0.571 / 0.515 | 0.562 / 0.229 | 0.562 / 0.521 |
| V2 | 0.574 / 0.512 | 0.521 / 0.521 | 0.562 / 0.333 |
| V3 | 0.589 / 0.560 | 0.375 / 0.479 | 0.458 / 0.500 |
| hV4 | 0.500 / 0.577 | 0.375 / 0.583 | 0.375 / 0.396 |

원문 단서: *"최저 셀(deutan V1 hmc = 0.229)도 chance 의 1.8배다. `All eight colors remained decodable` 는 두 arm 에서 유지된다. 발표 Figure 3A 는 SRM 공간 LORO 이고 위는 진폭 위 직접 계산이므로 정확 재현이 아니라 구조적 확인이다."*

## 정성 결론은 바뀌지 않았다

CVD 셀이 재산출판과 거의 일치하므로(재정렬 arm 은 8셀 중 6셀이 동일, V2 deutan 0.521 → 0.479, V3 deutan 0.375 → 0.479), **`All eight colors remained decodable` 와 최저 셀 deutan V1 = 0.229 라는 결론은 두 계산에서 같다.** 폐기는 결론이 틀려서가 아니라 **HC 기준선이 발표본과 달라 두 파이프라인을 같은 잣대로 비교할 수 없기 때문**이다.
