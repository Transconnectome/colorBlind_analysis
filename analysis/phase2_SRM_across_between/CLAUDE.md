# phase2_SRM_across_between — CLAUDE.md

**Stage A** · **Status**: Stabilized.

## Objective

SRM(Shared Response Model)로 HC와 CVD를 공통 신경 공간에 정렬한 뒤, **metric-level 왜곡**을 그룹 및 개인 수준에서 측정한다.

## Direction

- HC-only로 shared space 학습 → CVD는 SVD 투영 (circularity 방지).
- LOO-consistent 참조로 HC·CVD 동일 기준에서 비교.
- SRM 결과는 **metric property** (존재 증거)로 취급하고, **filter fitting criterion으로 쓰지 않는다**. 필터 피팅은 LOCO(functional)가 primary (future_phase2 참조).

## Results location

- 그룹·개인·robustness 결과 및 canonical k 값: 이 폴더의 `README.md` 및 `results/`.
- Canonical script: `rerun_loo_consistent.py` (세 가지 bias fix 모두 적용됨 — 원복 금지).

## Rule of action

1. 확정된 k 값과 세 가지 bias fix(HC-only SRM / LOO-HC / 동일 LOO refs)를 원복하지 않는다.
2. BrainIAK 실행은 반드시 `mpirun -np 1 python …` (bare python 금지).
3. sub-07 hV4는 voxel 수 부족 → 상관거리 nan, hV4 그룹 통계 제외.
4. ΔRDM·필터·inverse 관련 작업은 이 폴더가 아닌 `future_phase2_filter_optimization/`에서.
5. 결과 저장 규칙: flat `results/<name>/` + `config.json` 1개.
