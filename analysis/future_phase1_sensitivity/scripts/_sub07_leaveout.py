"""hV4 게이트에서 sub-07 을 뺐을 때 무엇이 달라지는가 (4 arm)."""
import json, sys
from pathlib import Path
import numpy as np
from scipy import stats

SC = Path("/Users/jinilkim/LocalProj/colorBlind_analysis/analysis/future_phase1_sensitivity/scripts")
sys.path.insert(0, str(SC))
import _perm_adjacent_arm as M

ARMS = ["with_residuals", "motreg", "motshift", "hmc_v2"]
ROI, RDIR = "hV4", "V4"
PIN = M.fold_pinvs(6)


def gate(root, subs, n_perm=1000, seed=42):
    amps = [M.load(root, s, RDIR) for s in subs]
    per = [M.loco_adj(a, PIN) for a in amps]
    obs = float(np.mean(per))
    rng = np.random.RandomState(seed)
    null = np.array([np.mean([M.loco_adj(a[:, rng.permutation(8), :], PIN) for a in amps])
                     for _ in range(n_perm)])
    p = float((np.sum(null >= obs) + 1) / (n_perm + 1))
    return obs, p, float(np.std(per, ddof=1)), per, float(null.mean())


def ch(v, m, sd, n):
    t = (v - m) / (sd * np.sqrt((n + 1) / n))
    return float(t), float(stats.t.cdf(t, n - 1)), float((v - m) / sd)


out = {}
for arm in ARMS:
    root = M.arm_root(arm)
    row = {}
    for tag, subs in [("n7", M.HC), ("n6_no07", [s for s in M.HC if s != "07"])]:
        obs, p, sd, per, nm = gate(root, subs)
        cvd = {}
        for s, lab in M.CVD.items():
            v = M.loco_adj(M.load(root, s, RDIR), PIN)
            t, pl, d = ch(v, obs, sd, len(subs))
            cvd[lab] = dict(value=float(v), t=t, p=pl, d_cc=d)
        row[tag] = dict(hc_mean=obs, p_perm=p, hc_sd=sd, null_mean=nm,
                        per_subject=dict(zip(subs, map(float, per))), cvd=cvd)
    out[arm] = row
    a, b = row["n7"], row["n6_no07"]
    print(f"\n=== {arm} ===")
    print(f"  n=7      HC {a['hc_mean']:.4f} (SD {a['hc_sd']:.4f}) p_perm={a['p_perm']:.4f} null={a['null_mean']:.4f}")
    print(f"  n=6 -07  HC {b['hc_mean']:.4f} (SD {b['hc_sd']:.4f}) p_perm={b['p_perm']:.4f} null={b['null_mean']:.4f}")
    for lab in ("deutan", "protan"):
        x, y = a["cvd"][lab], b["cvd"][lab]
        print(f"  {lab:7s} {x['value']:.3f}  CH n7 p={x['p']:.3f} d={x['d_cc']:+.2f}"
              f"   |  n6 p={y['p']:.3f} d={y['d_cc']:+.2f}")

json.dump(out, open(Path(__file__).parent / "sub07_leaveout_hV4.json", "w"), indent=1)
print("\nsaved sub07_leaveout_hV4.json")
