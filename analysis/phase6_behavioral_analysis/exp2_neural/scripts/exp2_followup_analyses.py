#!/usr/bin/env python3
"""exp2 FOLLOW-UP analyses (autonomous session) — strengthen/clarify the neural
validation given: behavior Optimal≈Window, sub-09 hV4 floored, N=2, run confound.

Computes (per subject sub-08/09, per ROI V1-V4):
  A) n=4-run RELIABILITY of LOCO adjacent accuracy: enumerate all C(6,4)=15 four-run
     subsets of this subject's exp1 no-filter, compute adj for each -> mean/sd/min/max
     /values. Bounds whether the Optimal(0.0625)-Window(0.1875) gap is within run-subset
     noise. Same for the HC group (pooled subset distribution).
  B) Per-condition LOO-run stability: drop each run in turn (->3-run), adj distribution.
  C) Voxel-space corr-distance RDM (28-vec) per condition + HC-mean; Spearman(cond,HC)
     = MODEL-FREE geometry (complements the SRM-space RDM already computed).
  D) 8 JND-pair neural dissimilarities extracted from the voxel RDM (reduced
     neural-behavioral correspondence; full 8x8 behavioral RDM not available).
  E) LOCO adj per condition (record) + per-color adj.

Output: results/exp2_followup_native.json   (pull locally, combine with behavior).
"""
import sys
import json
import itertools
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr

ROOT = Path("/scratch/connectome/haba6030/colorBlind")
sys.path.insert(0, str(ROOT / "analysis" / "phase4_forward_model" / "scripts"))
from utils_forward_model import create_basis_matrix, HUE_ANGLES
from loco_canonical import loco_forward_readouts

HC_C010 = ROOT / "derivatives" / "full_dataset_C010"
EXP2 = ROOT / "derivatives" / "full_dataset_C010_exp2"
HC_SUBJS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
ROIS = ['V1', 'V2', 'V3', 'V4']
K = 6
N4 = 4
C8 = create_basis_matrix(HUE_ANGLES, K, basis_type='fe')          # (8,K)
B360 = create_basis_matrix(np.arange(360), K, basis_type='fe')     # (360,K)

# JND-measured pairs (0-indexed; color_1=red..color_8=magenta, 45 deg steps)
JND_PAIRS = [('orange-yellow', (1, 2)), ('yellow-green', (2, 3)), ('green-blue', (3, 5)),
             ('red-orange', (0, 1)), ('blue-purple', (5, 6)), ('yellow-purple', (2, 6)),
             ('cyan-magenta', (4, 7)), ('red-cyan', (0, 4))]
_IU = np.triu_indices(8, k=1)
_PAIR2POS = {(_IU[0][k], _IU[1][k]): k for k in range(len(_IU[0]))}


def load(p):
    p = Path(p)
    return np.load(p) if p.exists() else None


def adj_acc(amp):
    """Mean LOCO adjacent accuracy (ols decoder), full run set."""
    r = loco_forward_readouts(amp, C8, B360, decoder='ols', tasks=('adj',))
    return float(r['adj'].mean()), r['adj']


def voxel_rdm(amp):
    """corr-distance RDM (28-vec) of run-mean (8,V) pattern."""
    m = amp.mean(0)
    rdm = 1.0 - np.corrcoef(m)
    return rdm[_IU]


def subset_n4_distribution(amp):
    """adj over all C(n_runs,4) four-run subsets."""
    nr = amp.shape[0]
    vals = [adj_acc(amp[list(idx)])[0] for idx in itertools.combinations(range(nr), N4)]
    return vals


def loo_run_stability(amp):
    """adj dropping each run in turn."""
    nr = amp.shape[0]
    return [adj_acc(np.delete(amp, i, axis=0))[0] for i in range(nr)]


def main():
    subs = sys.argv[1:] or ['08', '09']
    out = {}
    # --- HC reference RDMs + subset distribution (per ROI) ---
    hc_cache = {}
    for roi in ROIS:
        hc_rdms, hc_subset_vals = [], []
        for s in HC_SUBJS:
            amp = load(HC_C010 / s / roi / "amplitudes_procrustes.npy")
            if amp is None or (roi == 'V4' and amp.shape[2] < 20):
                continue
            hc_rdms.append(voxel_rdm(amp))
            hc_subset_vals += subset_n4_distribution(amp)
        hc_cache[roi] = {
            'rdm_mean': np.mean(hc_rdms, axis=0),
            'subset_vals': hc_subset_vals,
        }

    for sid in subs:
        subj = f"sub-{sid}"
        out[subj] = {}
        for roi in ROIS:
            r = {}
            nf = load(HC_C010 / subj / roi / "amplitudes_procrustes.npy")
            win = load(EXP2 / subj / "window" / roi / "amplitudes_procrustes.npy")
            opt = load(EXP2 / subj / "optimal" / roi / "amplitudes_procrustes.npy")
            conds = {'nofilter': nf, 'window': win, 'optimal': opt}

            # A) n=4 reliability from this subject's exp1 no-filter
            if nf is not None:
                sv = subset_n4_distribution(nf)
                r['nofilter_subset_n4'] = {
                    'mean': float(np.mean(sv)), 'sd': float(np.std(sv, ddof=1)),
                    'min': float(np.min(sv)), 'max': float(np.max(sv)),
                    'values': [round(x, 4) for x in sv]}
            hcsv = hc_cache[roi]['subset_vals']
            r['hc_subset_n4'] = {'mean': float(np.mean(hcsv)), 'sd': float(np.std(hcsv, ddof=1)),
                                 'min': float(np.min(hcsv)), 'max': float(np.max(hcsv)), 'n': len(hcsv)}

            # B) LOO-run stability per condition
            r['loo_run_stability'] = {}
            # E) adj per condition + per color
            r['loco_adj'] = {}
            r['loco_adj_per_color'] = {}
            # C/D) voxel RDM geometry + JND-pair dissimilarities
            r['voxel_rdm_spearman_to_hc'] = {}
            r['jnd_pair_neural_dissim'] = {'_pairs': [p[0] for p in JND_PAIRS]}
            hc_rdm = hc_cache[roi]['rdm_mean']
            r['jnd_pair_neural_dissim']['hc_mean'] = [round(float(hc_rdm[_PAIR2POS[p[1]]]), 4) for p in JND_PAIRS]
            r['voxel_rdm_spearman_hc_self_floor'] = None  # filled below
            for name, amp in conds.items():
                if amp is None:
                    continue
                m, vec = adj_acc(amp)
                r['loco_adj'][name] = round(m, 4)
                r['loco_adj_per_color'][name] = [round(float(x), 3) for x in vec]
                r['loo_run_stability'][name] = [round(x, 4) for x in loo_run_stability(amp)]
                rdm = voxel_rdm(amp)
                r['voxel_rdm_spearman_to_hc'][name] = round(float(spearmanr(rdm, hc_rdm)[0]), 4)
                r['jnd_pair_neural_dissim'][name] = [round(float(rdm[_PAIR2POS[p[1]]]), 4) for p in JND_PAIRS]
            out[subj][roi] = r

    # HC self-consistency floor for voxel RDM (LOO)
    out['_hc_voxel_rdm_self'] = {}
    for roi in ROIS:
        rdms = []
        for s in HC_SUBJS:
            amp = load(HC_C010 / s / roi / "amplitudes_procrustes.npy")
            if amp is None or (roi == 'V4' and amp.shape[2] < 20):
                continue
            rdms.append(voxel_rdm(amp))
        rdms = np.array(rdms)
        self_r = [float(spearmanr(rdms[i], np.delete(rdms, i, axis=0).mean(0))[0]) for i in range(len(rdms))]
        out['_hc_voxel_rdm_self'][roi] = {'spearman_self_loo_mean': float(np.mean(self_r)), 'n': len(rdms)}

    outpath = ROOT / "analysis/phase6_behavioral_analysis/exp2_neural/results/exp2_followup_native.json"
    outpath.write_text(json.dumps(out, indent=1))
    print(f"SAVED {outpath}")
    # quick console summary
    for sid in subs:
        subj = f"sub-{sid}"
        print(f"\n=== {subj} ===")
        for roi in ROIS:
            r = out[subj][roi]
            lab = {'V4': 'hV4'}.get(roi, roi)
            nfs = r.get('nofilter_subset_n4', {})
            print(f"  {lab}: adj NF/Win/Opt = "
                  f"{r['loco_adj'].get('nofilter')}/{r['loco_adj'].get('window')}/{r['loco_adj'].get('optimal')}"
                  f" | NF n4-subset mean={nfs.get('mean')} sd={nfs.get('sd')} range=[{nfs.get('min')},{nfs.get('max')}]"
                  f" | voxRDM->HC NF/Win/Opt = {r['voxel_rdm_spearman_to_hc'].get('nofilter')}"
                  f"/{r['voxel_rdm_spearman_to_hc'].get('window')}/{r['voxel_rdm_spearman_to_hc'].get('optimal')}"
                  f" (HCself={out['_hc_voxel_rdm_self'][roi]['spearman_self_loo_mean']:.3f})")


if __name__ == "__main__":
    main()
