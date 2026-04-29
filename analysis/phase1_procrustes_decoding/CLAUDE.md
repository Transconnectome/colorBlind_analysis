# phase1_procrustes_decoding — CLAUDE.md

**Stage A** · **Status**: Complete (frozen).

## Objective

전처리 파이프라인(C010)과 baseline color decoding을 확정한다. **모든 하위 phase가 입력으로 쓰는 Procrustes-aligned amplitudes**를 생산한다.

## Direction

- GLM·Procrustes·basis·voxel selection의 확정안은 이 phase에서 검증·동결되었다.
- 신규 파이프라인 변형 실험은 이 폴더에서 하지 않는다 (필요 시 별도 phase로).
- 본 폴더의 스크립트는 "amplitudes 생산"과 "pipeline 비교 기록"에 한정한다.

## Results location

- Amplitudes (downstream input): `derivatives/full_dataset_C010/{subject}/{ROI_dir}/amplitudes_procrustes.npy` — shape `(6, 8, n_voxels)`.
- 비교·검증 결과 및 최종 수치: 이 폴더의 `README.md`.

## Rule of action

1. 확정된 GLM/Procrustes/voxel 파라미터를 수정하지 않는다. 수정 사유 발생 시 **사용자 승인 필수**.
2. 이 phase의 출력을 **읽기 전용**으로 사용하는 하위 phase 스크립트는 다른 폴더에서 작성한다.
3. ROI dir에서 hV4는 `V4`로 저장된다. sub-07 hV4는 voxel 수 부족으로 그룹 통계에서 제외.
4. 결과 저장 규칙: flat `results/<name>/` + `config.json` 1개.
