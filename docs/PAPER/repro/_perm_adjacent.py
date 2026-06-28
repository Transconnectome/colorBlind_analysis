"""E2.1 verification on the ADJACENT-ACCURACY basis (paper §2: p=0.044, '8! exact').

Mirrors permutation_test_loco.py's null (shuffle 8 color labels per draw) but uses
the canonical adjacent-accuracy readout (FE-6 uniform + OLS) and HC n=6 (sub-07 excl).
A shared label permutation is applied to all subjects each draw; p = mean(null >= obs).
500 random draws (the paper's 8!=40320 exact enumeration is intractable here; this is a
Monte-Carlo estimate to confirm the above-chance result on the adjacent-accuracy metric).
"""
import sys, numpy as np
sys.path.insert(0, ".")
import _repro_util as U
sys.path.insert(0, str(U.P1 / "scripts"))
from loco_canonical import loco_forward_readouts
from utils_forward_model import create_basis_matrix, HUE_ANGLES

K = 6
hues = np.asarray(HUE_ANGLES, float)
C8 = create_basis_matrix(hues, K, "fe")
bf = create_basis_matrix(np.arange(360), K, "fe")
HC = ["01", "02", "03", "04", "05", "06"]
amps = [np.load(U.C010 / f"sub-{s}/V4/amplitudes_procrustes.npy") for s in HC]


def grp(perm=None):
    return np.mean([
        loco_forward_readouts(a if perm is None else a[:, perm, :], C8, basis_full=bf,
                              decoder="ols", tasks=("adj",))["adj"].mean()
        for a in amps])


obs = grp()
rng = np.random.RandomState(42)
N = 500
null = np.empty(N)
for i in range(N):
    null[i] = grp(rng.permutation(8))
    if (i + 1) % 50 == 0:
        p = float(np.mean(null[:i + 1] >= obs))
        print(f"  {i+1}/{N}  p={p:.3f}  null_mean={null[:i+1].mean():.3f}", flush=True)
p = float(np.mean(null >= obs))
print(f"\nADJACENT-ACCURACY above-chance: observed={obs:.4f}  p_perm={p:.4f}  "
      f"null_mean={null.mean():.4f} null_sd={null.std():.4f}  (paper p=0.044)")
np.save("perm_adjacent_null.npy", null)
