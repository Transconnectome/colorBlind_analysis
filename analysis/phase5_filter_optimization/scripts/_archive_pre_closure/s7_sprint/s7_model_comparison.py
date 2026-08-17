"""S7 model comparison — R+C 1-DOF vs 2-Component (사용자 directive 2026-05-24).

Fair comparison at λ=0 (L_γ only) — same data, same loss function, different parameterization:
  R+C:    k=1 (g), Δλ fixed prior
  2-comp: k=2 (β_s, β_c)

Metrics (per cell × subject):
  ΔAIC = 2·(k_2c − k_RC) + (loss_2c − loss_RC) median
  ΔBIC = log(n)·(k_2c − k_RC) + (loss_2c − loss_RC) median,  n = 8 hue pairs
  ΔTestLoss = test_loss_2c − test_loss_RC median  (generalization gap)

Convention: positive Δ → R+C favored (lower complexity wins or fits comparably)
            negative Δ → 2-comp favored (extra parameter justified)

Caveat: comparison at λ=0 assumes L_γ stable. For sub-08 (L_γ alone bimodal), the
selected configuration uses λ=0.25, but model comparison at λ=0.25 mixes z-scored
composite — not strictly interpretable as deviance. We therefore report:
  (1) primary comparison at λ=0 (L_γ-only deviance, interpretable)
  (2) optimal-config generalization (test loss) at the per-model best λ
"""

import json
import sys
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR.parent / "results" / "s7_loss_combo_subset"

COMBO_K = 5
N_PAIRS = 8           # # JND pairs (effective sample size for L_γ)
K_RC = 1              # R+C free params
K_2C = 2              # 2-comp free params


def extract_at_lambda(subsets, lam_key, probe, src='DPS_lit'):
    """Return list of (train_loss, test_loss, boundary) for R+C and 2-comp per subset."""
    rc_train = []
    rc_test = []
    rc_bdy = []
    tc_train = []
    tc_test = []
    tc_bdy = []
    for s in subsets:
        if s['k'] != COMBO_K:
            continue
        lf = s.get('lambda_fits', {}).get(probe, {}).get(lam_key)
        if lf is None:
            rc_train.append(None); rc_test.append(None); rc_bdy.append(None)
            tc_train.append(None); tc_test.append(None); tc_bdy.append(None)
            continue

        rc_fit = lf.get('rc', {}).get(src)
        if rc_fit:
            rc_train.append(rc_fit.get('loss_best'))
            rc_bdy.append(bool(rc_fit.get('boundary_low') or rc_fit.get('boundary_high')))
        else:
            rc_train.append(None); rc_bdy.append(None)

        tc_fit = lf.get('2comp')
        if tc_fit:
            tc_train.append(tc_fit.get('loss_best'))
            tc_bdy.append(bool(tc_fit.get('boundary_bs') or tc_fit.get('boundary_bc')))
        else:
            tc_train.append(None); tc_bdy.append(None)

        # Test
        tr = s.get('test_results', {}).get('lambda', {}).get(probe, {}).get(lam_key, {})
        if tr:
            rc_test.append(tr.get('rc', {}).get(src))
            tc_test.append(tr.get('2comp'))
        else:
            rc_test.append(None); tc_test.append(None)

    return rc_train, rc_test, rc_bdy, tc_train, tc_test, tc_bdy


def median_safe(arr):
    valid = [v for v in arr if v is not None and np.isfinite(v)]
    return float(np.median(valid)) if valid else None


def boundary_rate(arr):
    valid = [b for b in arr if b is not None]
    return float(np.mean(valid)) if valid else None


def aic_bic(loss, k, n):
    """AIC = 2k + deviance; BIC = k·log(n) + deviance, where deviance = -2 log L = loss."""
    if loss is None or not np.isfinite(loss):
        return None, None
    aic = 2 * k + loss
    bic = k * np.log(n) + loss
    return aic, bic


def main():
    cell_files = sorted(RESULTS_DIR.glob("cell_*.json"))
    print("=" * 92)
    print(f"S7 Model Comparison — R+C vs 2-Component (Behavioral-only, λ=0)")
    print(f"  N pairs (effective sample size) = {N_PAIRS}")
    print(f"  Probe = gamma_plus_RDM (used for λ=0 lookup; equivalent to L_γ alone at λ=0)")
    print("=" * 92)
    print()
    print(f"{'Cell':14s} | {'loss_RC':>8s} | {'loss_2c':>8s} | {'Δloss':>7s} | "
          f"{'ΔAIC':>7s} | {'ΔBIC':>7s} | {'TestΔ':>8s} | bdy_RC | bdy_2c | Verdict")
    print("-" * 110)

    summary = {}
    for fp in cell_files:
        with open(fp) as f:
            cell = json.load(f)
        key = f"{cell['subject']}_{cell['roi']}"

        # λ=0 = L_γ alone (probe gamma_plus_RDM with weight 0 on RDM)
        rc_tr, rc_te, rc_bdy, tc_tr, tc_te, tc_bdy = extract_at_lambda(
            cell['subsets'], '0.00', 'gamma_plus_RDM', src='DPS_lit',
        )
        loss_rc = median_safe(rc_tr)
        loss_2c = median_safe(tc_tr)
        test_rc = median_safe(rc_te)
        test_2c = median_safe(tc_te)
        br_rc = boundary_rate(rc_bdy)
        br_2c = boundary_rate(tc_bdy)

        if loss_rc is None or loss_2c is None:
            print(f"{key:14s} | NA — missing fit")
            continue

        d_loss = loss_2c - loss_rc
        d_aic = 2 * (K_2C - K_RC) + d_loss          # > 0 → R+C wins
        d_bic = np.log(N_PAIRS) * (K_2C - K_RC) + d_loss
        d_test = (test_2c - test_rc) if (test_2c is not None and test_rc is not None) else None

        # Verdict
        if d_aic > 2:
            v_aic = "R+C"
        elif d_aic < -2:
            v_aic = "2C"
        else:
            v_aic = "tie"
        if d_bic > 2:
            v_bic = "R+C"
        elif d_bic < -2:
            v_bic = "2C"
        else:
            v_bic = "tie"

        # Mark degenerate
        deg = ""
        if br_rc is not None and br_rc > 0.5: deg += " RCbdy"
        if br_2c is not None and br_2c > 0.5: deg += " 2Cbdy"

        verdict = f"AIC:{v_aic}/BIC:{v_bic}{deg}"

        d_test_s = f"{d_test:+7.3f}" if d_test is not None else "    NA "
        print(f"{key:14s} | {loss_rc:8.3f} | {loss_2c:8.3f} | {d_loss:+7.3f} | "
              f"{d_aic:+7.3f} | {d_bic:+7.3f} | {d_test_s} |  {br_rc:.2f}  |  {br_2c:.2f}  | {verdict}")

        summary[key] = {
            'loss_rc_median': loss_rc,
            'loss_2c_median': loss_2c,
            'delta_loss': d_loss,
            'delta_aic': d_aic,
            'delta_bic': d_bic,
            'delta_test': d_test,
            'test_rc_median': test_rc,
            'test_2c_median': test_2c,
            'boundary_rate_rc': br_rc,
            'boundary_rate_2c': br_2c,
            'verdict_aic': v_aic,
            'verdict_bic': v_bic,
            'caveat': deg.strip() if deg else None,
        }

    print()
    print("Verdict convention: Δ > +2 → R+C favored, Δ < −2 → 2-comp favored, |Δ| < 2 → tie")
    print(f"  ΔAIC penalty for extra param k=1 → 2: 2·1 = 2")
    print(f"  ΔBIC penalty: log({N_PAIRS}) = {np.log(N_PAIRS):.3f}")
    print()
    print("INTERPRETATION:")
    print("  positive Δloss: 2-comp loss is HIGHER (worse fit), R+C strongly wins")
    print("  Δloss in [-2, 0]: 2-comp marginally better fit, but complexity cost ≥ improvement → R+C wins")
    print("  Δloss < -2: 2-comp's extra parameter justified, 2-comp wins")
    print("  ΔTest > 0: 2-comp generalizes worse, R+C wins on held-out HC")

    out_json = RESULTS_DIR / "model_comparison_aic_bic.json"
    with open(out_json, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nSaved: {out_json}")


if __name__ == "__main__":
    main()
