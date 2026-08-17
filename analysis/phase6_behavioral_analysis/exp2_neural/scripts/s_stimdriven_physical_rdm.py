#!/usr/bin/env python3
"""
s_stimdriven_physical_rdm.py -- Review idea #2 (§A / ResearchNOTE §6.5.5),
Path B: does the OPTIMAL-condition V1/V2 neural RDM track the *physical* colour
remap the filter imposes, rather than reflecting damage to colour geometry?

Stimulus-driven hypothesis: V1/V2 faithfully encode the physically-displayed
colour. The Optimal filter rotates each stimulus in the CIELab a*-b* plane by a
known delta (preimage delta_theta_apply). So the Optimal-condition physical colour
geometry differs from the original-hue geometry in a KNOWN way. If V1/V2 are
stimulus-driven, their neural RDM should move FROM the original geometry TOWARD
the Optimal-physical geometry -- i.e. the neural displacement (optimal - nofilter)
should align with the physical displacement (optimal - original).

SCOPE / HONESTY:
- OPTIMAL arm only. WINDOW = macOS system colour filter (proprietary daltonisation)
  -> its displayed colorimetry is NOT analytically computable; it needs measured
  screenshots (Path A). Window is reported for reference only, never in the
  physical test.
- N=2 (sub-08 deutan, sub-09 protan) -> corroborative / descriptive, NOT a powered
  confirmation. No significance claims.
- Physical colour = measured STIM_LAB rotated by delta_theta_apply in the a*-b*
  plane (L*, chroma preserved). Ignores sRGB gamut clipping; a round-trip
  lab->rgb(clip)->lab sensitivity RDM is reported when skimage is available.

Output (flat): results/exp2_stimdriven_physical.json  (+ optional figure)
"""
import json
import argparse
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr, spearmanr

import sys
HERE = Path(__file__).resolve().parent
EXP2_RES = HERE.parent / "results"
FILTER_RES = (HERE.parents[2]
              / "future_phase2_filter_optimization/results/exp2_preimage")
sys.path.insert(0, str(HERE.parents[2]
                       / "future_phase2_filter_optimization/scripts"))
from stim_lab_render import STIM_LAB_ARR, lab2rgb  # measured CIELab of 8 colours

TRIU = np.triu_indices(8, k=1)          # 28 upper-triangle pairs
ROIS = ["V1", "V2", "V3", "V4"]
ROI_LABEL = {"V1": "V1", "V2": "V2", "V3": "V3", "V4": "hV4"}
EMB = ["srm", "procrustes", "fe_latent"]

try:
    from skimage.color import rgb2lab
    HAVE_SKIMAGE = True
except Exception:
    HAVE_SKIMAGE = False


def rotate_ab(lab, delta_deg):
    """Rotate each colour's (a*, b*) by its delta (deg) in the a*-b* plane;
    keep L* and chroma. lab: (8,3) [L,a,b]; delta_deg: (8,)."""
    out = lab.copy().astype(float)
    for i in range(len(lab)):
        r = np.deg2rad(delta_deg[i])
        a, b = lab[i, 1], lab[i, 2]
        out[i, 1] = a * np.cos(r) - b * np.sin(r)
        out[i, 2] = a * np.sin(r) + b * np.cos(r)
    return out


def gamut_roundtrip(lab):
    """lab -> sRGB(clipped) -> lab, to approximate the colour the monitor can
    actually show. Falls back to identity if skimage is missing."""
    if not HAVE_SKIMAGE:
        return lab
    out = np.zeros_like(lab)
    for i in range(len(lab)):
        rgb = np.clip(lab2rgb(lab[i, 0], lab[i, 1], lab[i, 2], clip=True), 0, 1)
        out[i] = rgb2lab(rgb.reshape(1, 1, 3)).reshape(3)
    return out


def rdm(lab):
    """28-vec upper-triangle Euclidean (=CIE76 dE) RDM over 8 Lab colours."""
    d = np.linalg.norm(lab[:, None, :] - lab[None, :, :], axis=2)
    return d[TRIU]


def corr_pair(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if np.std(a) < 1e-12 or np.std(b) < 1e-12:
        return {"pearson": None, "spearman": None}
    return {"pearson": float(pearsonr(a, b)[0]),
            "spearman": float(spearmanr(a, b)[0])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", nargs="+", default=["08", "09"])
    ap.add_argument("--variant", default="matched")
    ap.add_argument("--out", default=str(EXP2_RES / "exp2_stimdriven_physical.json"))
    args = ap.parse_args()

    result = {"method": "Path B (Optimal arm, analytic physical remap)",
              "n_subjects": len(args.subjects),
              "have_skimage_gamut_check": HAVE_SKIMAGE,
              "subjects": {}}

    for subj in args.subjects:
        pre = json.loads((FILTER_RES / f"sub-{subj}_2component_preimage.json").read_text())
        delta = np.array(pre["delta_theta_apply_deg"], float)   # (8,) rotation per colour

        # ---- physical colour geometry ----
        orig_lab = STIM_LAB_ARR.astype(float)                   # original displayed
        opt_lab = rotate_ab(orig_lab, delta)                    # Optimal displayed
        phys_orig = rdm(orig_lab)
        phys_opt = rdm(opt_lab)
        d_phys = phys_opt - phys_orig                           # physical displacement (28,)
        # gamut-clipped sensitivity
        phys_orig_g = rdm(gamut_roundtrip(orig_lab))
        phys_opt_g = rdm(gamut_roundtrip(opt_lab))
        d_phys_g = phys_opt_g - phys_orig_g

        emb_all = json.loads(
            (EXP2_RES / f"exp2_embeddings_sub-{subj}_{args.variant}.json").read_text())

        subj_out = {"cvd_type": pre.get("cvd_type"),
                    "delta_theta_apply_deg": delta.tolist(),
                    "physical_remap_magnitude_meanabs_deg": float(np.mean(np.abs(delta))),
                    "rois": {}}

        for roi in ROIS:
            if roi not in emb_all["rois"]:
                continue
            roi_out = {}
            for emb in EMB:
                E = emb_all["rois"][roi]["embeddings"].get(emb)
                if E is None:
                    continue
                cond = E["conditions"]
                nf = np.array(cond["nofilter"]["dist_eucl"], float)
                op = np.array(cond["optimal"]["dist_eucl"], float)
                d_neur = op - nf                                # neural displacement (28,)

                roi_out[emb] = {
                    # (1) does each condition's neural RDM match its OWN physical RDM?
                    "match_nofilter_vs_physOrig": corr_pair(nf, phys_orig),
                    "match_optimal_vs_physOpt": corr_pair(op, phys_opt),
                    "match_optimal_vs_physOrig": corr_pair(op, phys_orig),
                    # (2) KEY: does neural displacement track physical displacement?
                    "displacement_alignment": corr_pair(d_neur, d_phys),
                    "displacement_alignment_gamutclipped": corr_pair(d_neur, d_phys_g),
                }
            subj_out["rois"][ROI_LABEL[roi]] = roi_out
        result["subjects"][f"sub-{subj}"] = subj_out

        # ---- console summary: SRM V1/V2 (the §6.5.5 target) ----
        print(f"\n=== sub-{subj} ({pre.get('cvd_type')}) — physical remap |delta| mean "
              f"{np.mean(np.abs(delta)):.1f}deg ===")
        for roi in ["V1", "V2"]:
            r = subj_out["rois"].get(ROI_LABEL[roi], {}).get("srm")
            if not r:
                continue
            da = r["displacement_alignment"]
            mo = r["match_optimal_vs_physOpt"]["spearman"]
            mn = r["match_optimal_vs_physOrig"]["spearman"]
            print(f"  {ROI_LABEL[roi]:>3} SRM: displacement align rho="
                  f"{da['spearman']}, r={da['pearson']:.3f} | "
                  f"opt-neural vs physOpt rho={mo} vs physOrig rho={mn}")

    out = Path(args.out)
    out.write_text(json.dumps(result, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
