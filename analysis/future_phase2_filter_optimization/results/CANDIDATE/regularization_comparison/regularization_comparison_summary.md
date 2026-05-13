# Regularization Comparison — BEST/Tier 2 × Tikh/L_smooth

## P2a comparison

| Loss | Reg | Subject | argmin (β_s, β_c) | norm | L_total | **P2a** | exact/8 |
|---|---|---|---|---|---|---|---|
| BEST | tikh | sub-08 | (44, +28) | 52.2° | 0.456 | **0.575** | 4/8 |
| BEST | tikh | sub-09 | (30, +46) | 54.9° | 0.607 | **0.650** | 3/8 |
| BEST | lsmooth | sub-08 | (44, +28) | 52.2° | 0.451 | **0.575** | 4/8 |
| BEST | lsmooth | sub-09 | (30, +46) | 54.9° | 0.602 | **0.650** | 3/8 |
| TIER2 | lsmooth | sub-08 | (50, +24) | 55.5° | 0.502 | **0.575** | 4/8 |
| TIER2 | lsmooth | sub-09 | (34, +44) | 55.6° | 0.398 | **0.650** | 3/8 |
| TIER2 | tikh | sub-08 | (50, +24) | 55.5° | 0.508 | **0.575** | 4/8 |
| TIER2 | tikh | sub-09 | (34, +44) | 55.6° | 0.404 | **0.650** | 3/8 |

## P2a aggregate (min, avg per condition)

| Loss | Reg | sub-08 P2a | sub-09 P2a | min | avg |
|---|---|---|---|---|---|
| BEST | tikh | 0.575 | 0.650 | 0.575 | 0.613 |
| BEST | lsmooth | 0.575 | 0.650 | 0.575 | 0.613 |
| TIER2 | tikh | 0.575 | 0.650 | 0.575 | 0.613 |
| TIER2 | lsmooth | 0.575 | 0.650 | 0.575 | 0.613 |
