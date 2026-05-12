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
C1 빨강에 분홍 섞인
C2는 original이 연한 빨강 
C3는 original이 연두
C4는 original이 노랑 
C5는 original이 웜톤 아이보리 
C6은 original 하늘
C7은 original이  더 진한 하늘
c8 진파랑

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
## beta_s = 38, beta_c = -14

항목	| Filter 보고
C1	| original C1보다 분홍기가 줄고, 더 순수한 빨강에 가까워짐
C2	| 약간 초록색 느낌. original보다 색이 옅음
C3	| filter C4와 같은 노란색으로 보임
C4	| filter C3와 같은 노란색으로 보임. original C4 색과 같음
C5	| filter C6와 같은 하늘색으로 보임
C6	| filter C5와 같은 하늘색으로 보임. original C7 색과 같음
C7	| original C7보다 더 짙은 파란색
C8	| original과 같음

## V4-only beta_s = 38, beta_c = 7, z_combined CI disjoint from HC
C1	| 언급 없음
C2	| filtered가 더 짙은 빨강
C3	| filtered는 연한 주황
C4	| filtered는 연한 연두
C5	| filtered는 완전 옅은 연두
C6	| filtered가 더 진한 하늘색
C7	| filtered는 완전 짙은 파랑
C8	| filtered는 핑크빛 섞인 보라

## Windows
C1	| 핑크에서 빨강
C2	| 같은 주황
C3	| 연두에서 옅은 주황
C4	| 노랑에서 연두
C5	| 웜톤 아이보리에서 쿨톤 아이보리
C6	| 같은 하늘
C7	| 같은 파랑
C8	| 짙은 파랑에서 보라, 정확한 식별 어려움

## Cycle 14, beta_s = 58, beta_c = -36
C1	| 보라에서 핑크
C2	| 더 옅은 주황
C3	| 연한 주황에서 노랑
C4	| 연둣빛 도는 노랑에서 웜톤 아이보리
C5	| 웜톤 아이보리에서 하늘
C6	| 약간 진한 하늘
C7	| 파랑에서 하늘
C8	| 진한 파랑에서 파랑

## Cycle 12, `cycle12_xroi` (β_s=68°, β_c=−38°)
C1 | filter가 보라에서 핑크빛 도는 빨강. 
C2 | filter가 더 연한 주황. 
C3 | filter가 연두에서 노랑. 
C4 | filter가 노랑에서 웜톤 아이보리. 
C5 | filter가 웜톤 아이보리에서 하늘. 
C6 | filter가 미세하게 옅은 하늘 c5 c6 c7 filter 색이 같음. 
C7 | filter가 더 옅은 하늘. 
C8 | filter가 더 옅은 파랑. 