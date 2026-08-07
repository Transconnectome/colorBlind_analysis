#!/usr/bin/env python3
"""
run_c010_hmc.py — HMC 재산출용 C010 실행기 (Candidate A, 2026-08-05)

왜 래퍼인가
-----------
`analysis/phase1_procrustes_decoding/`는 frozen 이고 그 CLAUDE.md 는
  1. 확정된 GLM/Procrustes/voxel 파라미터를 수정하지 않는다
  2. 신규 파이프라인 변형 실험은 이 폴더에서 하지 않는다
를 규정한다. 따라서 `run_full_dataset_C010.py` 를 고치지도, 복사하지도 않는다.
이 래퍼는 동결 모듈을 **그대로 import** 하고 경로 상수 두 개만 바꾼다.
GLM·drift·Procrustes 코드는 바이트 단위로 동일하다.

  FMRIPREP_DIR : fmriprep_out_method3_header_mi  →  fmriprep_out_method3_hmc
  OUTPUT_DIR   : full_dataset_C010_with_residuals →  full_dataset_C010_hmc

ROI 마스크는 바꾸지 않는다
--------------------------
`ROI_MASKS_DIR`(method3_header_mi)를 그대로 쓴다. 두 arm 이 **동일한 voxel 집합**을
공유해야 차이가 HMC 단독으로 귀인된다. 새 BOLD 트리는 shape·affine 이 현행과 같으므로
기존 마스크가 그대로 유효하다(검증런에서 확인).

실행
----
    python run_c010_hmc.py --subject 01 --roi V1
    python run_c010_hmc.py --subject 01 --roi V1 \
        --fmriprep-dir <path> --output-dir <path>       # 기본값 재정의
"""

import argparse
import importlib.util
import sys
from pathlib import Path

# 서버상의 동결 파이프라인 위치. 저장소에서는 analysis/phase1_procrustes_decoding/ 에 있으나
# 서버 배포본은 analysis/validation/preprocess_detrend_temp/ 에 있다 (기존
# run_C010_with_residuals.sbatch:35 가 이 디렉터리로 cd 한다). md5 동일함을 확인:
# c344b6a1625a3011e7762e507a22a882
FROZEN = Path("/scratch/connectome/haba6030/colorBlind/analysis"
              "/validation/preprocess_detrend_temp/run_full_dataset_C010.py")
DEFAULT_FMRIPREP = Path("/storage/connectome/haba6030/fmriprep_out_method3_hmc")
DEFAULT_OUTPUT = Path("/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010_hmc")


def load_frozen(path):
    if not path.exists():
        raise FileNotFoundError(f"frozen pipeline not found: {path}")
    spec = importlib.util.spec_from_file_location("c010_frozen", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["c010_frozen"] = mod
    spec.loader.exec_module(mod)          # main() 은 __main__ 가드 뒤라 실행되지 않는다
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True)
    ap.add_argument("--roi", required=True, choices=["V1", "V2", "V3", "V4"])
    ap.add_argument("--fmriprep-dir", default=str(DEFAULT_FMRIPREP))
    ap.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    ap.add_argument("--frozen", default=str(FROZEN))
    args = ap.parse_args()

    mod = load_frozen(Path(args.frozen))

    before = (mod.FMRIPREP_DIR, mod.OUTPUT_DIR)
    mod.FMRIPREP_DIR = Path(args.fmriprep_dir)
    mod.OUTPUT_DIR = Path(args.output_dir)

    print("=" * 80)
    print("C010 re-run — Candidate A (method3 + HMC)")
    print(f"  frozen pipeline : {args.frozen}")
    print(f"  FMRIPREP_DIR    : {before[0]}\n                 -> {mod.FMRIPREP_DIR}")
    print(f"  OUTPUT_DIR      : {before[1]}\n                 -> {mod.OUTPUT_DIR}")
    print(f"  ROI_MASKS_DIR   : {mod.ROI_MASKS_DIR}   (unchanged — voxel set held constant)")
    print(f"  target          : sub-{args.subject} {args.roi}")
    print("=" * 80)

    if not mod.FMRIPREP_DIR.exists():
        raise FileNotFoundError(f"BOLD tree missing: {mod.FMRIPREP_DIR}")

    mod.run_subject_roi(args.subject, args.roi)


if __name__ == "__main__":
    main()
