# phase4_forward_model — CLAUDE.md

**Stage A→B bridge** · **Status**: Core pipeline complete.

## Objective

`Y_s(θ) = W_s · C(θ; K)` 형태의 360° hue forward encoder를 피팅·검증한다. Future_phase2 필터의 **neural forward model** 역할.

## Direction

- 모델은 ridge_gcv 직접 피팅(no group prior)로 확정. SRM group prior 계열과 smoothing Tikhonov 계열은 이미 기각.
- LOCO(보간)과 LORO(분류)는 다른 과제 — 보간이 있는지는 LOCO 영구 permutation null로만 주장.
- V1/V2는 분류는 되지만 보간은 null에 가까움 → "discrimination ≠ interpolation" 프레임 유지.
- hV4를 primary ROI, V3은 conditional로 취급.

## Results location

- Per-ROI K 선정, gate, HC-CVD 차이, W 안정성: 이 폴더의 `README.md`, `RESULTS.md`, `results/`.
- W 산출물은 future_phase2에서 **읽기 전용** 입력으로 사용.

## Rule of action

1. Encoder를 ridge_gcv 외로 바꾸지 않는다. 새 basis/encoder 제안 시 기각 이력을 확인 후 **사용자 승인**.
2. LOCO는 pooled runs(42 samples)로 수행, run-averaged로 되돌리지 않는다.
3. V1/V2 LOCO bar를 "해석 가능"하다고 주장하지 않는다 (null 범위).
4. W 결과는 이 폴더에서만 갱신. future_phase2의 스크립트가 역방향으로 W를 덮어쓰지 않는다.
5. 결과 저장 규칙: flat `results/<name>/` + `config.json` 1개.
