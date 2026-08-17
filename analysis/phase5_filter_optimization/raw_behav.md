# Source

Behavioral reports collected by sub-08 (deutan) while viewing 4-column visualizations:
Original | CVD perceives | Filtered (pre-image) | CVD(Filtered)

Generator: `scripts/visualization/visualize_filter_candidates.py`

| Filter section | Source figure |
|---|---|
| beta_s=38, beta_c=−14 (Canonical) | `candidates/canonical.png` |
| V4-only beta_s=38, beta_c=+7 | `candidates/primary.png` |
| Cycle 14, beta_s=58, beta_c=−36 | `candidates/cycle14.png` |
| Windows | Windows built-in color filter (Color Blind Ease of Access), no figure |

Note: Reports were made before visualization improvements. P2a analysis uses column 2
("CVD perceives") of the candidates/ figures as authoritative simulator output.

---

# Original 

## sub-08
C1 | 핑크 
C2 | 초록
C3 | 초록 
C4 | 연두 
C5 | 아이보리 
C6 | 탁한 하늘
C7 | 파랑
C8 | 진한 파랑

## sub-09
C1 | 붉은색에 가까운 핑크 
C2 | 주황색
C3 | 올리브색 
C4 | 연두 + 민트색 
C5 | 칙칙한 하늘색 
C6 | 조금 덜 칙칙한 하늘색
C7 | 파란색
C8 | 연보라+연분홍 

# Filter
## sub-08
### P2AMAX L(β_s, β_c) = 0.3 · (L_topk(V4) + L_mse(V4 vuln) + L_rdmV1(SRM)) + 3.0 · Tikh(β)
항목	| Filter 보고
C1	| 연한 빨강
C2	| 초록에 약간 빨간빛 도는 주황
C3	| 초록
C4	| 초록
C5	| 연두
C6	| 탁한 하늘
C7	| 보라
C8	| 핑크


### Hybrid (beta_s = 16, beta_c = 40) : 0.7·L_mse + 0.3·L_rdm_cosine + 2.0·Tikh
항목	| Filter 보고
C1	| 연한 빨강
C2	| 초록
C3	| 초록
C4	| 연한 초록
C5	| 연두
C6	| 하늘
C7	| 진한 파랑
C8	| 핑크

* 연한 주황이면 바로 초록으로 하며, 붉은 기운이 있어야 주황이라고 함
** 밝은 주황은 주황으로 보나 어두운 주황을 초록으로 봄
** 초록을 갈색 (c3)로 봄

## sub-09
항목	| Filter 보고
C1	| 다홍색
C2	| 갈색
C3	| 올리브색
C4	| 진한 연두
C5	| 옥색
C6	| 탁한 하늘
C7	| 파랑
C8	| 진한 핑크