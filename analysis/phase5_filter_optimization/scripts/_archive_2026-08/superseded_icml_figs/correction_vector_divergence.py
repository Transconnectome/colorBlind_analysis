"""Correction-vector divergence: R+C vs 2-component (Sub-08).

Reproduces the paper's §S16 divergence statistic and recomputes it for the
ADOPTED L_fit fit. The original ad-hoc computation was not preserved; this
script is the durable source of record.

Method (validated against published value):
  - vectors  : FORWARD per-hue distortion delta-theta over the 8 canonical hues
  - R+C      : Tregillus convention delta_RC = (1+g) * delta_Machado(Delta-lambda)
               Sub-08: Delta-lambda = 2.0 nm, g = +2.25
  - metrics  : cosine similarity, sign agreement (count of hues with same sign)

Validation: R+C vs 2-comp (38, -10) [historical rho-argmax fit] ->
  cos = -0.19, sign = 3/8  == published -0.18, 3/8 (to rounding; sign exact).

Result (this script): R+C vs 2-comp (6, -42) [adopted L_fit fit] ->
  cos = -0.54, sign = 1/8.

Run: conda activate srm; python scripts/correction_vector_divergence.py
"""
import json
import sys
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from two_comp import forward_2comp           # noqa: E402
from rc_1dof import delta_machado            # noqa: E402

FAMILY = "deutan"          # Sub-08
RC_DLAMBDA, RC_G = 2.0, 2.25
FITS = {
    "adopted_Lfit": (6.0, -42.0),       # main-text adopted fit
    "historical_rho_argmax": (38.0, -10.0),  # reproduces published -0.18/3/8
}


def cos(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def sign_agreement(a, b):
    return int(np.sum(np.sign(np.round(a, 6)) == np.sign(np.round(b, 6))))


def main():
    rc = (1.0 + RC_G) * np.asarray(delta_machado(RC_DLAMBDA, FAMILY), float)
    out = {
        "subject": "sub-08",
        "rc": {"delta_lambda_nm": RC_DLAMBDA, "g_tregillus": RC_G,
               "forward_deg": [round(float(x), 3) for x in rc]},
        "comparisons": {},
    }
    for name, (bs, bc) in FITS.items():
        v = np.asarray(forward_2comp(bs, bc, FAMILY), float)
        out["comparisons"][name] = {
            "beta_s": bs, "beta_c": bc,
            "twocomp_forward_deg": [round(float(x), 3) for x in v],
            "cosine": round(cos(rc, v), 3),
            "sign_agreement_of_8": sign_agreement(rc, v),
        }
        print(f"{name:24s} (bs={bs:+.0f}, bc={bc:+.0f}):  "
              f"cos={cos(rc, v):+.3f}  sign={sign_agreement(rc, v)}/8")

    dest = SCRIPT_DIR.parent / "results" / "correction_vector_divergence.json"
    dest.write_text(json.dumps(out, indent=2))
    print(f"\nsaved -> {dest}")


if __name__ == "__main__":
    main()
