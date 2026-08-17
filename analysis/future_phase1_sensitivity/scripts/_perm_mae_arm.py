"""_perm_mae_arm.py — color-label permutation null for continuous circular error.

Adjacent accuracy scores a prediction correct within 45 deg and therefore has an
analytic and a permutation chance level already. The mean absolute circular error
(MAE) introduced in `_arm_agreement.py` is a different statistic, so calling any
value of it "chance level" requires its own null. This builds that null with the
same per-subject color-label permutation used by `_perm_adjacent_arm.py`.

Reported per participant / ROI / arm:
  * observed MAE (deg, lower is better)
  * permutation null mean and SD (N = 1000 label shuffles)
  * p_perm = P(null <= observed), i.e. one-tailed in the "better than chance" direction
  * Crawford-Howell test of each CVD case against the HC distribution on MAE

Decision the manuscript needs:
  A  both arms indistinguishable from null  -> the 0.125 vs 0.271 difference was
     threshold crossing in a discretized summary; the phenomenon is arm-robust
  B  hmc protan better than null            -> the deficit is preprocessing-sensitive
  C  both better than null but far from HC  -> partial interpolation, persistent deficit
"""
import argparse
import json

import sys as _sys
from pathlib import Path as _Path

# Moved out of docs/PAPER/repro on 2026-08-17 (analysis/future_phase1_sensitivity).
# _repro_util still lives there and stays the single definition of the data roots.
_REPRO = _Path(__file__).resolve().parents[3] / "docs" / "PAPER" / "repro"
_sys.path.insert(0, str(_REPRO))
OUT = _Path(__file__).resolve().parent.parent / "results"
OUT.mkdir(parents=True, exist_ok=True)

import numpy as np

import _repro_util as U
from _arm_agreement import loco_detail  # noqa: E402
from _perm_adjacent_arm import (  # noqa: E402
    CVD, HC, ROI_DIR, arm_root, fold_pinvs, load,
)

ARMS = ["with_residuals", "hmc_v2"]
ALL = HC + list(CVD)
N_PERM = 1000
SEED = 42


def mae(amp, pinvs):
    return float(np.nanmean(loco_detail(amp, pinvs)[2]))


def ch(x, ctrl):
    """Crawford-Howell one-tailed; returns t and p for x being WORSE (higher MAE)."""
    from scipy import stats
    m, sd, n = float(np.mean(ctrl)), float(np.std(ctrl, ddof=1)), len(ctrl)
    t = (x - m) / (sd * np.sqrt((n + 1) / n))
    return float(t), float(1 - stats.t.cdf(t, n - 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-perm", type=int, default=N_PERM)
    a = ap.parse_args()

    out = {"n_perm": a.n_perm, "seed": SEED, "metric": "mean absolute circular error (deg)",
           "arms": ARMS, "rois": {}}

    for roi, rdir in ROI_DIR.items():
        out["rois"][roi] = {}
        for arm in ARMS:
            root = arm_root(arm)
            amps = {s: load(root, s, rdir) for s in ALL}
            pin = fold_pinvs(next(iter(amps.values())).shape[0])

            obs, nulls = {}, {}
            for s in ALL:
                rng = np.random.RandomState(SEED)
                obs[s] = mae(amps[s], pin)
                nl = np.empty(a.n_perm)
                for b in range(a.n_perm):
                    nl[b] = mae(amps[s][:, rng.permutation(8), :], pin)
                nulls[s] = nl

            hc_obs = np.array([obs[s] for s in HC])
            entry = {"hc_observed_mean": round(float(hc_obs.mean()), 2),
                     "hc_observed_sd": round(float(hc_obs.std(ddof=1)), 2),
                     "subjects": {}}
            for s in ALL:
                nl = nulls[s]
                entry["subjects"][s] = {
                    "group": CVD.get(s, "HC"),
                    "observed": round(obs[s], 2),
                    "null_mean": round(float(nl.mean()), 2),
                    "null_sd": round(float(nl.std(ddof=1)), 2),
                    "p_perm_better": round(float((nl <= obs[s]).mean()), 4),
                    "z_vs_null": round(float((obs[s] - nl.mean()) / nl.std(ddof=1)), 2)}
            for s in CVD:
                t, p = ch(obs[s], hc_obs)
                entry["subjects"][s]["ch_t_vs_hc"] = round(t, 2)
                entry["subjects"][s]["ch_p_worse_than_hc"] = round(p, 4)
            out["rois"][roi][arm] = entry

            print(f"\n=== {roi} · {arm} ===", flush=True)
            print(f"  HC 관측 {entry['hc_observed_mean']:.1f}±{entry['hc_observed_sd']:.1f} deg")
            print(f"  {'sub':6s} {'grp':7s} {'obs':>7s} {'null':>7s} {'z':>6s} {'p_perm':>7s} {'CH p':>7s}")
            for s in ALL:
                d = entry["subjects"][s]
                chp = f"{d['ch_p_worse_than_hc']:.4f}" if "ch_p_worse_than_hc" in d else "-"
                print(f"  {s:6s} {d['group']:7s} {d['observed']:7.1f} {d['null_mean']:7.1f} "
                      f"{d['z_vs_null']:+6.2f} {d['p_perm_better']:7.3f} {chp:>7s}")

    with open(OUT / "perm_mae_arm.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\nwrote perm_mae_arm.json")


if __name__ == "__main__":
    main()
