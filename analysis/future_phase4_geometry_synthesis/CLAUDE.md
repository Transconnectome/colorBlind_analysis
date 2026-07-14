# CLAUDE.md — future_phase4_geometry_synthesis

## §0 성격 (필독)
**소비(consumer) 층.** exp2_neural Stage-1/2 산출 JSON을 읽어 **시각화·기전분해·null·per-color**만 추가한다.
신경 amplitude를 다시 로드하거나 SRM/FE를 recompute **하지 않는다** (서버·brainiak 불필요, pure JSON arithmetic + matplotlib).

## 입력 (모두 로컬 존재)
- Stage 1 coords: `../future_phase3_behavioral_analysis/exp2_neural/results/exp2_embeddings_sub-{ID}_{variant}.json`
  - `rois.{ROI}.embeddings.{procrustes|srm|fe_latent}.{hc_ref|conditions.{nofilter|window|optimal}}.coords` (procrustes 8×V, srm 8×K, fe_latent 8×6)
  - `dist_eucl`/`dist_corr` (28-vec), `rois.{ROI}.loco.{cond}.{decoded_hue,hue_error_deg,confusion(8×8)}`
- Stage 2 파생: `.../exp2_geometry_derived_sub-{ID}_{variant}.json` (agreement/displacement/jnd_correlation) — 교차검증용
- HC self-consistency (병기용): `../phase2_SRM_across_between/results/loo_consistent/20260218_163819/loo_consistent_results.json` → `results.{ROI}.rdm_correlations.hc_hc.mean`
- JND: `../future_phase3_behavioral_analysis/results/exp2_behavior/sub-{ID}_jnd_compare.csv`

## 스크립트 (scripts/)
- `utils_p4.py` — 공유: JSON 로더, classical MDS(고유값 포함), RDM(eucl/corr), Procrustes 분해, label-perm null, anisotropy, HC-consistency 로더
- `p4_overlay_viz.py` — GAP1: SRM vs FE 임베딩 오버레이 (RDM→MDS 2D/3D, Procrustes 정렬, displacement 선), ROI×조건 그리드
- `p4_geometry_decomposition.py` — GAP2/3/4: 등방scale(gain)/회전/잔차 분해 + anisotropy(λ1/λ2) + label-perm null + HC-consistency 병기
- `p4_percolor_loco.py` — GAP5: in-sample(true) vs LOCO-decoded 색별 displacement + confusion

## 출력 (results/, figures/) — flat, timestamp 서브디렉토리 금지
- `results/config.json` (배치당 1개), `results/p4_{analysis}_sub-{ID}_{variant}.json`
- `figures/overlay_sub-{ID}_{metric}_{2d|3d}.png` 등

## 정책 (필독)
- **descriptive·가설-생성적만.** N=2 CVD, 8점 원형 → disparity 낮음은 구조적. **primary 판별 = label-perm null**.
- Q1 gain 분해는 opponent-gain 전제 **지지**까지, "증명" 금지 (repo policy §specificity).
- metric 3종(eucl/corr, + 필요시 crossnobis)에서 결론 robustness 보고.

## Env
`conda activate srm` (local). matplotlib Agg. seaborn 사용 무방(로컬).
