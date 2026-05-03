#!/usr/bin/env python3
"""
rot_vs_dilation_sim.py — Cycle math framework, smoke run.

Goal:
    1) Numerically express three CVD-simulator models (Machado 1-way,
       R+C, 2-component) as hue-circle maps theta -> theta'.
    2) Quantify mathematical relations:
       (a) infinitesimal generators (rotation vs axial dilation),
       (b) commutator [R, S] != 0 in 2D,
       (c) forward simulation of Emery-style B-Y phase shift from
           the 2-component map, comparing beta_s vs phi_BY.
    3) Recover an "equivalent g" or "equivalent Delta-lambda" that
       best matches a target 2-component map (and vice-versa).
    4) Identifiability/Fisher analysis on the LOCO-style L_fit Hessian
       to test if g = +/-2.25, large Delta-lambda, etc., are within a
       degenerate / under-identified region of parameter space.

This is a stand-alone, dependency-light script (numpy, scipy,
matplotlib only). It imports the project's machado_simulator and
retinal_cortical helpers when available; otherwise falls back to
local lightweight implementations so the smoke run can execute on
laptops without the full data tree.

Outputs:
    results/diagnostics/cycle_math_framework/
        hue_maps.csv            -- numerical theta -> theta' for all models
        commutator_norms.json   -- ||[R,S]||_F at varying scales
        fisher_loco.json        -- Hessian eigenvalues / cond. number
        equiv_param_table.csv   -- (beta_s, beta_c) <-> (g, Delta-lambda)
        emery_phi_recovery.json -- phi_BY recovered under varying assumptions
        fig_hue_maps.png        -- visualization of three models
        fig_emery.png           -- B-Y response simulated from 2-comp
        fig_fisher.png          -- L_fit landscape and curvature

Run:
    conda activate srm
    python scripts/cycle_math_framework/rot_vs_dilation_sim.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Locate project scripts (best effort; OK if missing for smoke run)
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PHASE2_SCRIPTS = SCRIPT_DIR.parent
PHASE2_DIR = PHASE2_SCRIPTS.parent
PROJECT_ROOT = PHASE2_DIR.parent.parent

for p in (PHASE2_SCRIPTS, PROJECT_ROOT / "analysis" / "future_phase1_forward_model" / "scripts"):
    if str(p) not in sys.path and p.exists():
        sys.path.insert(0, str(p))

OUT_DIR = PHASE2_DIR / "results" / "cycle_math_framework"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Machado fallback (linear protan/deutan hue compression in opponent space)
# ---------------------------------------------------------------------------
try:
    from machado_simulator import machado_shifted_hue_at  # type: ignore
    HAS_MACHADO = True
except Exception:
    HAS_MACHADO = False


def _machado_fallback(delta_lambda: float, family: str,
                      theta_deg: np.ndarray) -> np.ndarray:
    """Lightweight fallback that captures the structural property of
    Machado: increasing Delta-lambda compresses the hue circle along
    the family-specific confusion axis.

    This is NOT bit-exact with machado_shifted_hue_at, but is
    sufficient for the structural / Lie-algebra / commutator analysis
    in this script. The full pipeline always goes through the real
    Machado simulator; this fallback is only for laptop smoke runs.
    """
    theta = np.deg2rad(theta_deg)
    # Confusion axis (radians)
    if family == "protan":
        phi_conf = np.deg2rad(16.0)
    elif family == "deutan":
        phi_conf = np.deg2rad(150.0)
    else:
        phi_conf = np.deg2rad(83.0)
    # Severity-driven compression along the confusion axis
    # alpha in [0, 1]; alpha = delta_lambda / 30 nm is a coarse
    # caricature in line with machado_simulator.alpha_at_delta_lambda
    alpha = float(np.clip(delta_lambda / 30.0, 0.0, 1.0))
    # Project onto (e_par, e_perp) where e_par is the confusion axis
    x = np.cos(theta) * np.cos(phi_conf) + np.sin(theta) * np.sin(phi_conf)
    y = -np.cos(theta) * np.sin(phi_conf) + np.sin(theta) * np.cos(phi_conf)
    # Compress y axis (perpendicular to confusion line): standard
    # dichromacy reduction
    y_new = (1.0 - alpha) * y
    # Rotate back to original frame
    cx = x * np.cos(phi_conf) - y_new * np.sin(phi_conf)
    cy = x * np.sin(phi_conf) + y_new * np.cos(phi_conf)
    theta_new = np.arctan2(cy, cx)
    return np.rad2deg(theta_new) % 360.0


def machado_map(delta_lambda: float, family: str,
                theta_deg: np.ndarray) -> np.ndarray:
    if HAS_MACHADO:
        try:
            _, hue_final, _ = machado_shifted_hue_at(
                delta_lambda, family, theta_deg)
            return np.asarray(hue_final) % 360.0
        except Exception:
            pass
    return _machado_fallback(delta_lambda, family, theta_deg)


# ---------------------------------------------------------------------------
# 2. R+C model (Machado retinal + cortical opponent gain)
# ---------------------------------------------------------------------------

def rc_map(delta_lambda: float, g: float, family: str,
           theta_deg: np.ndarray) -> np.ndarray:
    """rg' = rg_ret + g (rg_ret - rg_base);  by' = by_ret"""
    hue_base = np.asarray(theta_deg) % 360.0
    hue_ret = machado_map(delta_lambda, family, hue_base)
    if delta_lambda == 0.0 or g == 0.0:
        return hue_ret
    rg_base = np.cos(np.deg2rad(hue_base))
    by_base = np.sin(np.deg2rad(hue_base))
    rg_ret = np.cos(np.deg2rad(hue_ret))
    by_ret = np.sin(np.deg2rad(hue_ret))
    rg_final = rg_ret + g * (rg_ret - rg_base)
    by_final = by_ret  # YB unchanged
    return np.rad2deg(np.arctan2(by_final, rg_final)) % 360.0


# ---------------------------------------------------------------------------
# 3. 2-component model (cortical angular dilation)
# ---------------------------------------------------------------------------

CONF_AXIS = {"protan": 16.0, "deutan": 150.0, "normal": 83.0}


def two_component_map(beta_s: float, beta_c: float, family: str,
                      theta_deg: np.ndarray) -> np.ndarray:
    """theta' = theta + beta_s cos(theta-90) + beta_c cos(theta-theta_conf)"""
    theta = np.asarray(theta_deg, dtype=float) % 360.0
    theta_conf = CONF_AXIS[family]
    dt = (beta_s * np.cos(np.deg2rad(theta - 90.0))
          + beta_c * np.cos(np.deg2rad(theta - theta_conf)))
    return (theta + dt) % 360.0


# ---------------------------------------------------------------------------
# 4. Lie generators in (rg, by) plane
# ---------------------------------------------------------------------------

def rotation_generator() -> np.ndarray:
    """Infinitesimal rotation: J = [[0,-1],[1,0]]"""
    return np.array([[0.0, -1.0], [1.0, 0.0]])


def dilation_generator(axis_deg: float) -> np.ndarray:
    """Infinitesimal axial dilation along axis e = (cos a, sin a):
        S = e e^T - (I - e e^T)/something is an over-spec; we use the
        traceless symmetric diagonal in the rotated frame:
            S(a) = R(a) diag(1, -1) R(a)^T
    so that exp(t S) gives sinh/cosh dilation along e and -along
    perpendicular."""
    a = np.deg2rad(axis_deg)
    R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    D = np.diag([1.0, -1.0])
    return R @ D @ R.T


def commutator(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    return A @ B - B @ A


# ---------------------------------------------------------------------------
# 5. Forward Emery-style B-Y phase recovery from 2-component map
# ---------------------------------------------------------------------------

def emery_phi_BY(beta_s: float, beta_c: float, family: str,
                 n_theta: int = 360) -> dict:
    """Simulate Emery 2021's response model under the 2-component map.

    Assumption A (Q6): hue category response peaks at fixed perceptual
    angles phi_k_perc = {0, 90, 180, 270} (R, Y, G, B) and falls off as
    half-rectified cosine on the percept axis theta'.

    We simulate r_k(theta) = max(0, cos(theta'(theta) - phi_k_perc))
    and refit a single-period cosine on theta to recover phi_BY.
    Compare against Emery 21.4 deg (rotation phase shift between
    normal and AT phi_BY).
    """
    theta = np.linspace(0.0, 360.0, n_theta, endpoint=False)
    theta_prime = two_component_map(beta_s, beta_c, family, theta)
    # B-Y opponent response on percept axis (90 = yellow, 270 = blue)
    # half-rectified cosine
    r_y = np.maximum(0.0, np.cos(np.deg2rad(theta_prime - 90.0)))
    r_b = np.maximum(0.0, np.cos(np.deg2rad(theta_prime - 270.0)))
    # Net BY response
    r_by = r_y - r_b  # signed
    # Fit r_by(theta) ~ A cos(theta - phi_BY)
    c = np.cos(np.deg2rad(theta))
    s = np.sin(np.deg2rad(theta))
    X = np.column_stack([c, s])
    coeff, *_ = np.linalg.lstsq(X, r_by, rcond=None)
    A = float(np.hypot(coeff[0], coeff[1]))
    phi_BY = float(np.rad2deg(np.arctan2(coeff[1], coeff[0])) % 360.0)
    # The "shift" from normal trichromat is phi_BY itself (because
    # at beta_s=beta_c=0, theta_prime = theta, r_by = cos(theta-90),
    # which fits to phi_BY = 90.
    delta_phi_BY = (phi_BY - 90.0 + 180.0) % 360.0 - 180.0
    # Small-angle prediction (from Q6 derivation):
    pred_small_angle = -beta_s - beta_c * np.sin(np.deg2rad(CONF_AXIS[family]))
    return {
        "beta_s": beta_s,
        "beta_c": beta_c,
        "family": family,
        "phi_BY_deg": phi_BY,
        "delta_phi_BY_deg": delta_phi_BY,
        "pred_small_angle_deg": float(pred_small_angle),
        "A": A,
        "n_theta": n_theta,
    }


# ---------------------------------------------------------------------------
# 6. Equivalence: find g* (and Delta-lambda*) that minimizes L2 distance
#    between rc_map(delta_lambda, g, family, .) and two_component_map(b_s, b_c, family, .)
# ---------------------------------------------------------------------------

def fit_rc_to_2comp(beta_s: float, beta_c: float, family: str) -> dict:
    """Brute-force grid: for each (delta_lambda, g) compute MSE(theta',
    rc_theta') over theta in [0, 360). Returns the minimizer."""
    theta = np.linspace(0.0, 360.0, 360, endpoint=False)
    target = two_component_map(beta_s, beta_c, family, theta)
    target_rad = np.deg2rad(target)
    dl_grid = np.linspace(0.0, 30.0, 31)  # nm
    g_grid = np.linspace(-3.0, 3.0, 61)
    best_mse = np.inf
    best_dl = None
    best_g = None
    for dl in dl_grid:
        for gv in g_grid:
            cand = rc_map(dl, gv, family, theta)
            d = np.deg2rad(cand) - target_rad
            d = (d + np.pi) % (2 * np.pi) - np.pi
            mse = float(np.mean(d ** 2))
            if mse < best_mse:
                best_mse = mse
                best_dl = float(dl)
                best_g = float(gv)
    return {
        "target_beta_s": beta_s,
        "target_beta_c": beta_c,
        "family": family,
        "best_delta_lambda": best_dl,
        "best_g": best_g,
        "best_mse_rad2": best_mse,
        "rmse_deg": float(np.sqrt(best_mse) * 180.0 / np.pi),
    }


# ---------------------------------------------------------------------------
# 7. Fisher / curvature: numerically Hessian of L_fit at fitted point
# ---------------------------------------------------------------------------

def loco_loss_2comp(beta_s: float, beta_c: float,
                    target_dt: np.ndarray, family: str,
                    theta_deg: np.ndarray) -> float:
    """L_fit = mean( (delta_theta_sim - delta_theta_obs)^2 )"""
    theta_prime = two_component_map(beta_s, beta_c, family, theta_deg)
    dt_sim = np.deg2rad((theta_prime - theta_deg + 180.0) % 360.0 - 180.0)
    diff = dt_sim - target_dt
    diff = (diff + np.pi) % (2 * np.pi) - np.pi
    return float(np.mean(diff ** 2))


def loco_loss_rc(delta_lambda: float, g: float,
                 target_dt: np.ndarray, family: str,
                 theta_deg: np.ndarray) -> float:
    theta_prime = rc_map(delta_lambda, g, family, theta_deg)
    dt_sim = np.deg2rad((theta_prime - theta_deg + 180.0) % 360.0 - 180.0)
    diff = dt_sim - target_dt
    diff = (diff + np.pi) % (2 * np.pi) - np.pi
    return float(np.mean(diff ** 2))


def hessian_2d(loss_fn, x0: np.ndarray, h: tuple) -> np.ndarray:
    """Central finite differences for 2D Hessian."""
    H = np.zeros((2, 2))
    f0 = loss_fn(*x0)
    for i in range(2):
        x_p = x0.copy(); x_m = x0.copy()
        x_p[i] += h[i]; x_m[i] -= h[i]
        H[i, i] = (loss_fn(*x_p) - 2 * f0 + loss_fn(*x_m)) / (h[i] ** 2)
    # off-diagonal
    for i, j in [(0, 1)]:
        x_pp = x0.copy(); x_pp[i] += h[i]; x_pp[j] += h[j]
        x_pm = x0.copy(); x_pm[i] += h[i]; x_pm[j] -= h[j]
        x_mp = x0.copy(); x_mp[i] -= h[i]; x_mp[j] += h[j]
        x_mm = x0.copy(); x_mm[i] -= h[i]; x_mm[j] -= h[j]
        H[i, j] = (loss_fn(*x_pp) - loss_fn(*x_pm)
                   - loss_fn(*x_mp) + loss_fn(*x_mm)) / (4 * h[i] * h[j])
        H[j, i] = H[i, j]
    return H


# ---------------------------------------------------------------------------
# 8. Smoke run
# ---------------------------------------------------------------------------

def run_smoke():
    out_log = {}

    # ---- (a) Hue maps for canonical fitted parameters from notion.md
    theta = np.linspace(0.0, 360.0, 360, endpoint=False)

    cases = [
        ("sub-08", "deutan", {"machado": 2.0, "rc": (2.0, +2.25),
                              "two_comp": (38.0, -14.0)}),
        ("sub-09", "protan", {"machado": 13.5, "rc": (13.5, -1.10),
                              "two_comp": (6.0, -22.0)}),
        ("sub-10", "normal", {"machado": 0.0, "rc": (0.0, 0.0),
                              "two_comp": (0.0, 0.0)}),
    ]

    csv_lines = ["theta_deg,subject,family,model,theta_prime_deg"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), sharex=True, sharey=True)
    for ax, (subj, fam, params) in zip(axes, cases):
        m = machado_map(params["machado"], fam, theta)
        r = rc_map(*params["rc"], family=fam, theta_deg=theta)
        c = two_component_map(*params["two_comp"], family=fam, theta_deg=theta)
        for name, vals in [("machado", m), ("rc", r), ("two_comp", c)]:
            for th, vp in zip(theta, vals):
                csv_lines.append(f"{th:.2f},{subj},{fam},{name},{vp:.4f}")
        ax.plot(theta, theta, "k:", label="identity", alpha=0.5)
        ax.plot(theta, m, label=f"Machado dl={params['machado']:.1f}")
        ax.plot(theta, r, label=f"R+C dl={params['rc'][0]:.1f},g={params['rc'][1]:+.2f}")
        ax.plot(theta, c, label=f"2C bs={params['two_comp'][0]:+.0f},bc={params['two_comp'][1]:+.0f}")
        ax.set_title(f"{subj} ({fam})")
        ax.set_xlabel("theta (deg)")
        ax.set_ylabel("theta' (deg)")
        ax.legend(fontsize=8, loc="lower right")
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_hue_maps.png", dpi=120)
    plt.close(fig)
    (OUT_DIR / "hue_maps.csv").write_text("\n".join(csv_lines))
    out_log["hue_maps_csv_rows"] = len(csv_lines) - 1

    # ---- (b) Lie commutator at varying scales
    J = rotation_generator()
    S0 = dilation_generator(0.0)
    S90 = dilation_generator(90.0)
    S45 = dilation_generator(45.0)
    comm = {
        "norm_J_S0": float(np.linalg.norm(commutator(J, S0))),
        "norm_J_S45": float(np.linalg.norm(commutator(J, S45))),
        "norm_J_S90": float(np.linalg.norm(commutator(J, S90))),
        "norm_S0_S90": float(np.linalg.norm(commutator(S0, S90))),
        "interpretation": (
            "[J, S(a)] = 2 R(a)diag(0,-1)... non-zero unless S=0; "
            "[S(a), S(b)] = 0 iff a==b mod 90 (commuting axial dilations); "
            "rotation and dilation generators do NOT commute."
        ),
    }
    (OUT_DIR / "commutator_norms.json").write_text(json.dumps(comm, indent=2))
    out_log["commutator"] = comm

    # ---- (c) Emery phi_BY recovery for fitted (beta_s, beta_c)
    emery_results = []
    for subj, fam, params in cases:
        bs, bc = params["two_comp"]
        em = emery_phi_BY(bs, bc, fam)
        em["subject"] = subj
        emery_results.append(em)
    # Plus pure-beta_s grid
    grid = []
    for bs in [0.0, 5.0, 10.0, 15.0, 20.0, 21.4, 25.0, 30.0]:
        em = emery_phi_BY(bs, 0.0, "protan")
        em["subject"] = f"grid_bs={bs:.1f}"
        grid.append(em)
    emery_block = {
        "fitted_subjects": emery_results,
        "pure_bs_grid_protan": grid,
        "note": (
            "delta_phi_BY is the rotation of the B-Y peak in the "
            "Emery half-rectified cosine basis induced by the "
            "2-component map, computed as deviation from 90 deg. "
            "Comparison with Emery 21.4 deg should track |delta_phi_BY|."
        ),
    }
    (OUT_DIR / "emery_phi_recovery.json").write_text(json.dumps(emery_block, indent=2))

    # Plot Emery curve for sub-08, sub-09
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, (subj, fam, params) in zip(axes, cases[:2]):
        bs, bc = params["two_comp"]
        theta = np.linspace(0.0, 360.0, 360, endpoint=False)
        theta_prime = two_component_map(bs, bc, fam, theta)
        r_by = (np.maximum(0.0, np.cos(np.deg2rad(theta_prime - 90.0)))
                - np.maximum(0.0, np.cos(np.deg2rad(theta_prime - 270.0))))
        ax.plot(theta, r_by, label="r_BY simulated")
        ax.plot(theta, np.cos(np.deg2rad(theta - 90.0)),
                "k:", alpha=0.6, label="normal cos(theta-90)")
        ax.set_title(f"{subj} ({fam}) bs={bs}, bc={bc}")
        ax.set_xlabel("theta (deg)")
        ax.set_ylabel("BY response")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_emery.png", dpi=120)
    plt.close(fig)

    # ---- (d) Equivalent (g, dl) for 2-comp targets
    eq_table = []
    for subj, fam, params in cases:
        if fam == "normal":
            continue
        bs, bc = params["two_comp"]
        eq = fit_rc_to_2comp(bs, bc, fam)
        eq["subject"] = subj
        eq_table.append(eq)
    csv2 = ["subject,family,target_beta_s,target_beta_c,best_delta_lambda,best_g,rmse_deg"]
    for r in eq_table:
        csv2.append(
            f"{r['subject']},{r['family']},{r['target_beta_s']},{r['target_beta_c']},"
            f"{r['best_delta_lambda']},{r['best_g']},{r['rmse_deg']:.3f}"
        )
    (OUT_DIR / "equiv_param_table.csv").write_text("\n".join(csv2))
    out_log["equiv_table"] = eq_table

    # ---- (e) Fisher / Hessian condition number for L_fit (2-comp and R+C)
    # Use sub-08 deutan as the test case. Define "observed" delta_theta as
    # the 2-component model at the fitted (38, -14), and compute the Hessian
    # at that fit point in 2-comp coordinates and also at the equivalent
    # (delta_lambda, g) in R+C coordinates.
    target_subj = "sub-08"
    target_fam = "deutan"
    target_bs, target_bc = 38.0, -14.0
    theta_loco = np.linspace(0.0, 360.0, 360, endpoint=False)
    target_dt = (two_component_map(target_bs, target_bc, target_fam, theta_loco)
                 - theta_loco)
    target_dt = np.deg2rad((target_dt + 180.0) % 360.0 - 180.0)

    H_2c = hessian_2d(
        lambda b1, b2: loco_loss_2comp(b1, b2, target_dt, target_fam, theta_loco),
        np.array([target_bs, target_bc]),
        h=(0.5, 0.5),
    )
    eig_2c = np.linalg.eigvalsh(H_2c)

    # R+C: use minimizer from equiv_table
    rc_match = next(r for r in eq_table if r["subject"] == target_subj)
    H_rc = hessian_2d(
        lambda dl, gv: loco_loss_rc(dl, gv, target_dt, target_fam, theta_loco),
        np.array([rc_match["best_delta_lambda"], rc_match["best_g"]]),
        h=(0.5, 0.05),
    )
    eig_rc = np.linalg.eigvalsh(H_rc)

    fisher = {
        "target": {"subject": target_subj, "family": target_fam,
                   "beta_s": target_bs, "beta_c": target_bc},
        "two_component_hessian": H_2c.tolist(),
        "two_component_eigvals": eig_2c.tolist(),
        "two_component_cond_number": float(eig_2c.max() / max(abs(eig_2c.min()), 1e-12)),
        "rc_match": rc_match,
        "rc_hessian": H_rc.tolist(),
        "rc_eigvals": eig_rc.tolist(),
        "rc_cond_number": float(eig_rc.max() / max(abs(eig_rc.min()), 1e-12)),
        "note": (
            "Large condition number (>1e3) indicates near-degenerate "
            "direction in parameter space at the fit minimum -- a "
            "weakly identifiable parameter."
        ),
    }
    (OUT_DIR / "fisher_loco.json").write_text(json.dumps(fisher, indent=2))
    out_log["fisher"] = {
        "two_comp_cond": fisher["two_component_cond_number"],
        "rc_cond": fisher["rc_cond_number"],
    }

    # Plot: L_fit landscape near R+C minimum (dl, g)
    dl0 = rc_match["best_delta_lambda"]; g0 = rc_match["best_g"]
    dlg = np.linspace(max(0.0, dl0 - 5), dl0 + 5, 41)
    gg = np.linspace(g0 - 1.5, g0 + 1.5, 41)
    Z = np.zeros((len(gg), len(dlg)))
    for i, gv in enumerate(gg):
        for j, dv in enumerate(dlg):
            Z[i, j] = loco_loss_rc(float(dv), float(gv), target_dt, target_fam, theta_loco)
    fig, ax = plt.subplots(figsize=(6.5, 5))
    im = ax.contourf(dlg, gg, np.log10(Z + 1e-8), levels=20, cmap="viridis")
    ax.plot(dl0, g0, "r*", markersize=14, label=f"min ({dl0:.1f}, {g0:+.2f})")
    ax.set_xlabel("Delta_lambda (nm)")
    ax.set_ylabel("g")
    ax.set_title(f"R+C log10(L_fit) landscape, sub-08 (target = 2-comp 38,-14)")
    ax.legend()
    fig.colorbar(im, ax=ax, label="log10 L_fit")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_fisher.png", dpi=120)
    plt.close(fig)

    return out_log


if __name__ == "__main__":
    log = run_smoke()
    print(json.dumps(log, indent=2))
