"""_icc_all_pairs.py — LOCO 지표 신뢰도를 여러 방식으로 재계산한다 (2026-08-24).

배경: 원고에 올리려던 ICC(2,1) = 0.825 는 정본↔`hmc_v2` 쌍에서만 계산된 값이었다
(`_arm_agreement.py` 의 `ARMS = ["with_residuals", "hmc_v2"]`). 그 값이 arm 쌍에
의존하는지, 그리고 CVD 두 명을 포함한 것이 값을 부풀리는지 확인한다.

산출 요약 (results/icc_all_pairs.json):
  - 정본 대비 세 arm 각각의 ICC(2,1), HC+CVD(n=9) 와 HC만(n=7) 두 벌
  - 정본 arm 내부 split-half (3런 vs 3런, 10개 분할 평균) — arm 비교가 필요 없는 대안

판정: 게이트 순서와 일치하는 깨끗한 그림은 `hmc_v2` 쌍 하나에서만 나온다.
`motreg` 로 바꾸면 HC 만 볼 때 V2 가 hV4 를 앞서고, arm 내부 split-half 에서는
hV4 와 V2 차이가 0.02 로 좁혀진다. n=9 와 n=7 의 차이는 CVD 두 명의 극단값이
피험자 간 분산을 키우기 때문이며, ICC 는 그 분산을 분모에 쓴다.
→ ICC 는 원고에 쓰지 않는다.
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _perm_adjacent_arm as M          # noqa: E402
from _arm_agreement import icc21        # noqa: E402

OUT = HERE.parent / "results"
ROIS = {"V1": "V1", "V2": "V2", "V3": "V3", "hV4": "V4"}
ARMS = ["motreg", "motshift", "hmc_v2"]
ALL = M.HC + list(M.CVD)
PIN6 = M.fold_pinvs(6)
PIN3 = M.fold_pinvs(3)
SPLITS = [(list(c), [r for r in range(6) if r not in c])
          for c in itertools.combinations(range(6), 3)][:10]


def loco(arm, rdir, subs, runs=None):
    root = M.arm_root(arm)
    pin = PIN6 if runs is None else PIN3
    return np.array([M.loco_adj(M.load(root, s, rdir) if runs is None
                                else M.load(root, s, rdir)[runs], pin) for s in subs])


def main():
    out = {"note": "LOCO adjacent accuracy reliability; the published 0.825 is the "
                   "with_residuals<->hmc_v2 pair at n=9 and does not generalise",
           "cross_arm": {}, "within_arm_split_half": {}}

    for tag, subs in [("n9_hc_plus_cvd", ALL), ("n7_hc_only", M.HC)]:
        base = {r: loco("with_residuals", d, subs) for r, d in ROIS.items()}
        out["cross_arm"][tag] = {
            r: {a: icc21(base[r], loco(a, d, subs)) for a in ARMS}
            for r, d in ROIS.items()}

    for roi, rdir in ROIS.items():
        amps = {s: M.load(M.arm_root("with_residuals"), s, rdir) for s in ALL}
        iccs, rs = [], []
        for a, b in SPLITS:
            xa = np.array([M.loco_adj(amps[s][a], PIN3) for s in ALL])
            xb = np.array([M.loco_adj(amps[s][b], PIN3) for s in ALL])
            if np.std(xa) == 0 or np.std(xb) == 0:
                continue
            iccs.append(icc21(xa, xb))
            rs.append(float(np.corrcoef(xa, xb)[0, 1]))
        out["within_arm_split_half"][roi] = {
            "icc21": float(np.mean(iccs)), "pearson_r": float(np.mean(rs)),
            "n_splits": len(iccs), "n_subjects": len(ALL)}

    out["verdict"] = ("hV4 is top in every measure at n=9, but at n=7 the motreg pair puts "
                      "V2 (0.826) above hV4 (0.634), and within-arm split-half separates "
                      "hV4 (0.744) from V2 (0.724) by only 0.02. The 'V1 near zero' half "
                      "holds only for the hmc_v2 and motreg pairs (motshift gives 0.642). "
                      "Do not cite ICC in the manuscript.")
    (OUT / "icc_all_pairs.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))

    print("cross-arm ICC(2,1) vs with_residuals")
    for tag in out["cross_arm"]:
        print(f"  [{tag}]  " + "".join(f"{a:>12s}" for a in ARMS))
        for r in ROIS:
            print(f"  {r:>7s}  " + "".join(f"{out['cross_arm'][tag][r][a]:>12.3f}" for a in ARMS))
    print("within-arm split-half (with_residuals)")
    for r, v in out["within_arm_split_half"].items():
        print(f"  {r:>7s}  ICC {v['icc21']:.3f}   r {v['pearson_r']:.3f}")
    print(f"\nwrote {OUT / 'icc_all_pairs.json'}")


if __name__ == "__main__":
    main()
