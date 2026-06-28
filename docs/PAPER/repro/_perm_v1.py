import sys, numpy as np
sys.path.insert(0, ".")
import _repro_util as U
sys.path.insert(0, str(U.P1 / "scripts"))
from loco_canonical import loco_forward_readouts
from utils_forward_model import create_basis_matrix, HUE_ANGLES
K=6; hues=np.asarray(HUE_ANGLES,float)
C8=create_basis_matrix(hues,K,"fe"); bf=create_basis_matrix(np.arange(360),K,"fe")
HC=["01","02","03","04","05","06","07"]  # V1: all 7 HC
amps=[np.load(U.C010/f"sub-{s}/V1/amplitudes_procrustes.npy") for s in HC]
def subj_adj(amp, perm=None):
    a = amp if perm is None else amp[:,perm,:]
    return loco_forward_readouts(a,C8,basis_full=bf,decoder="ols",tasks=("adj",))["adj"].mean()
obs=np.mean([subj_adj(a) for a in amps])
rng=np.random.RandomState(42); N=1000; null=np.empty(N)
for i in range(N):
    null[i]=np.mean([subj_adj(a, rng.permutation(8)) for a in amps])
    if (i+1)%200==0: print(f"  V1 {i+1}/{N} p={(np.sum(null[:i+1]>=obs)+1)/(i+2):.4f}", flush=True)
p=(np.sum(null>=obs)+1)/(N+1)
print(f"V1 ADJACENT above-chance (per-subject perm): observed={obs:.4f} p_perm={p:.4f} null_mean={null.mean():.4f} N={N}")
np.save("perm_v1_null.npy", null)
