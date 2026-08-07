#!/usr/bin/env python3
"""
run_c010_motreg.py — 움직임 회귀 arm (2026-08-05)

목적
----
FD 교란을 **재샘플링 없이** 검정한다. 원본(method3) BOLD 를 그대로 쓰고, 2단계 GLM 설계행렬에
MCFLIRT 움직임 파라미터 6개 + 시간미분 6개를 잡음 회귀자로 추가한다. 복셀 위치가 변하지
않으므로 보간 비용이 없고, 움직임과 상관된 분산만 제거된다.

  HMC 재샘플링 arm : 재샘플링 2회 → 움직임 + 보간이 혼입
  이 arm           : 재샘플링 0회 → 움직임 단독

이 검정은 지금까지 한 번도 제대로 돌아간 적이 없다. `preprocess_tests.md` Part B 의
C010+P3 비교에 쓰인 motion 회귀자는 손상된 `*_desc-confounds_timeseries.tsv` 에서 왔고
(trans_*/rot_* 가 header 상수, FD 전부 0.0), 상수의 시간미분은 0 이므로 12개 회귀자가
전부 죽어 있었다. 유효한 기록은 `*_desc-motion.par` 뿐이다.

부수 효과 — HMC arm 진단
------------------------
HMC 재샘플링 arm 에서 sub-08 의 split-half RDM 신뢰도가 붕괴했다(.842→.360 등). 원인이
(a) 이중 보간인지 (b) 움직임 인공물의 정당한 제거인지 갈린다. 이 arm 은 보간 없이 움직임만
제거하므로 판별자가 된다.
  신뢰도 유지  → (a) 보간
  신뢰도 붕괴  → (b) 인공물 제거

구현
----
동결 파이프라인을 고치지 않는다. import 후
  - `MOTION_TISSUE = True` 로 켜고
  - `load_motion_confounds` 를 `.par` 판독기로 교체한다 (원본은 손상된 TSV 를 읽는다)
  - `OUTPUT_DIR` 만 새 트리로 바꾼다. `FMRIPREP_DIR` 은 **원본 그대로**

MCFLIRT `.par` 열 순서: rot_x rot_y rot_z (rad), trans_x trans_y trans_z (mm).

실행
    python run_c010_motreg.py --subject 08 --roi V2
"""

import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np

FROZEN = Path("/scratch/connectome/haba6030/colorBlind/analysis"
              "/validation/preprocess_detrend_temp/run_full_dataset_C010.py")
DEFAULT_OUTPUT = Path("/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010_motreg")


def load_frozen(path):
    if not path.exists():
        raise FileNotFoundError(f"frozen pipeline not found: {path}")
    spec = importlib.util.spec_from_file_location("c010_frozen", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["c010_frozen"] = mod
    spec.loader.exec_module(mod)
    return mod


def make_par_loader(add_derivatives=True, circshift_seed=None):
    """동결 스크립트의 load_motion_confounds 를 대체한다.

    호출부는 `*_desc-confounds_timeseries.tsv` 경로를 넘긴다. 같은 디렉터리의
    `*_desc-motion.par` 로 바꿔 읽는다. 반환 규약은 원본과 동일: (array, n_cols).
    """
    def load_motion_par(confounds_path):
        par = Path(str(confounds_path).replace(
            "_desc-confounds_timeseries.tsv", "_desc-motion.par"))
        if not par.exists():
            raise FileNotFoundError(f"MCFLIRT .par not found: {par}")
        m = np.loadtxt(par)                       # (n_scans, 6)
        if m.ndim != 2 or m.shape[1] != 6:
            raise ValueError(f"unexpected .par shape {m.shape}: {par}")
        if circshift_seed is not None:
            # 대조군: 순환이동으로 자기상관·스펙트럼은 보존하고 데이터와의
            # 시간 정렬만 파괴한다. 회귀자 12개를 넣는 일반 비용(공선성에 의한
            # 분산 팽창)과 실제 움직임 분산 제거를 구분하기 위함.
            # 결정적 시드 — 파이썬 hash() 는 프로세스마다 달라져 재현되지 않는다
            import zlib
            key = zlib.crc32(par.name.encode()) ^ (circshift_seed & 0xFFFFFFFF)
            rs = np.random.default_rng(key)
            m = np.roll(m, int(rs.integers(m.shape[0] // 8, m.shape[0] - m.shape[0] // 8)), axis=0)
        cols = [m]
        if add_derivatives:
            d = np.vstack([np.zeros((1, 6)), np.diff(m, axis=0)])
            cols.append(d)
        out = np.hstack(cols)
        # 상수열 방어 — 손상된 TSV 사건의 재발 방지
        sd = out.std(axis=0)
        n_const = int((sd < 1e-12).sum())
        if n_const:
            raise ValueError(
                f"{n_const} constant motion regressor(s) in {par.name} — "
                "이는 손상된 기록의 징후다. 중단한다.")
        return out, out.shape[1]
    return load_motion_par


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True)
    ap.add_argument("--roi", required=True, choices=["V1", "V2", "V3", "V4"])
    ap.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    ap.add_argument("--no-derivatives", action="store_true",
                    help="6 파라미터만 사용 (기본은 파라미터 + 시간미분 = 12)")
    ap.add_argument("--circshift", type=int, default=None,
                    help="대조군: 움직임 회귀자를 런별 무작위 순환이동 (시드 지정)")
    ap.add_argument("--frozen", default=str(FROZEN))
    args = ap.parse_args()

    mod = load_frozen(Path(args.frozen))

    mod.OUTPUT_DIR = Path(args.output_dir)
    mod.MOTION_TISSUE = True
    mod.WM_ACOMPCOR = False
    mod.load_motion_confounds = make_par_loader(not args.no_derivatives, args.circshift)

    n_reg = 6 if args.no_derivatives else 12
    print("=" * 80)
    print("C010 + motion regression (재샘플링 없음)")
    print(f"  frozen pipeline : {args.frozen}")
    print(f"  FMRIPREP_DIR    : {mod.FMRIPREP_DIR}   (원본 유지)")
    print(f"  OUTPUT_DIR      : {mod.OUTPUT_DIR}")
    print(f"  ROI_MASKS_DIR   : {mod.ROI_MASKS_DIR}   (unchanged)")
    print(f"  motion 회귀자    : {n_reg} (MCFLIRT .par"
          f"{' + 시간미분' if not args.no_derivatives else ''})"
          f"{'  [순환이동 대조군 seed=%d]' % args.circshift if args.circshift is not None else ''}")
    print(f"  target          : sub-{args.subject} {args.roi}")
    print("=" * 80)

    mod.run_subject_roi(args.subject, args.roi)


if __name__ == "__main__":
    main()
