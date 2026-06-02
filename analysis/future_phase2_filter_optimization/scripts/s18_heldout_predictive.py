"""S18: Held-out-HC predictive evaluation + neural/behavioral STANDALONE fits.

Two user requests (2026-06-02 discussion):

  Q1  Parameter STABILITY (s17 HC-LOO argmin IQR) shows the fit is reproducible,
      not that the value is CORRECT (s17 line 90 / RQ3: "stability != correctness").
      -> Add a held-out (leave-one-HC-out) PREDICTIVE-performance axis.

  Q2  Production reports the neural-INCLUSION increment over behavioral (RQ4).
      -> Also report neural(RDM)-ONLY and behav(gamma)-ONLY STANDALONE fits and
         their held-out performance, not just the increment.

User-agreed asymmetry (2026-06-02) in how each term uses the held-out HC:

  L_gamma : held-out HC enters as the JND *baseline input*; the target is the
            CVD subject's own JND (fixed across folds). => "reference-robustness".
            (0,0) baseline IS meaningful (pred = held-out-HC JND, undistorted).
            Normalize by TRAIN (6-HC) per-pair SD to avoid the degenerate
            single-HC SD. Metric: dLgamma = L(delta*) - L(0,0); <0 = the fitted
            perceptual shift explains CVD's JND anomaly better than no-shift.

  L_RDM   : held-out HC defines the *target* delta-RDM (CVD-vs-that-HC geometry).
            => genuine held-out prediction. BUT (0,0) is DEGENERATE here:
            delta_rdm_sim(0)=0 -> loss floored to 1.0 ALWAYS, so "beats (0,0)" is
            trivially true and meaningless. Baseline replaced by a random-delta
            GRID NULL: percentile of L_RDM_test(delta*) within the held-out grid
            loss distribution. Low percentile = the train-chosen value is also
            good on the held-out HC (generalizes / specific), ~0.5 = no better
            than an arbitrary shift. (0,0) value is still recorded to document
            the degeneracy.

Reuses s17_hc_loo.py (fold/atom machinery) via importlib; no re-fitting sprint.

Output:
  results/s10_inclusion/s18_heldout_predictive.json
  results/s10_inclusion/s18_heldout_predictive.md
"""
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

# Import s17 as a module to reuse ALL of its machinery (main() is __main__-guarded)
_S17_PATH = SCRIPT_DIR / "s17_hc_loo.py"
_spec = importlib.util.spec_from_file_location("s17_hc_loo", _S17_PATH)
s17 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(s17)

# Reused machinery
preload_data        = s17.preload_data
make_gamma_pair_atom = s17.make_gamma_pair_atom
make_rdm_atom        = s17.make_rdm_atom
make_rdm_atom_n1ok   = s17.make_rdm_atom_n1ok
grid_eval_2comp      = s17.grid_eval_2comp
zscore_grid          = s17.zscore_grid
argmin_2comp         = s17.argmin_2comp
forward_2comp        = s17.forward_2comp
jnd_baseline_from_pool = s17.jnd_baseline_from_pool
load_jnd_per_pair    = s17.load_jnd_per_pair
BS_GRID = s17.BS_GRID
BC_GRID = s17.BC_GRID
HUES    = s17.HUES
HC_SUBJS     = s17.HC_SUBJS
HC_JND_SUBJS = s17.HC_JND_SUBJS
PAIR_HUES = s17.PAIR_HUES
PAIR_KEYS = s17._v6.PAIR_KEYS

OUT_DIR = SCRIPT_DIR.parent / "results" / "s10_inclusion"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------------------
# Production 2-component candidates (closure.md). R+C excluded here: closure
# verification is 2-component; Q1/Q2 are about the production filters.
# ------------------------------------------------------------------------------
CANDIDATES = [
    # S08-stable dropped per user (2026-06-02): keep one production candidate per
    # subject — S08-robust (sub-08) + S09-primary (sub-09).
    {'id': 'S08-robust', 'subject': 'sub-08', 'family': 'deutan',
     'gamma_pairs': ['OY'], 'rdm_rois': ['V2'],
     'phase_b_fit': {'beta_s': 6.0, 'beta_c': -42.0},
     'combo_label': 'gammaOY|RDMV2|noLOCO'},
    {'id': 'S09-primary', 'subject': 'sub-09', 'family': 'protan',
     'gamma_pairs': ['ALL'], 'rdm_rois': ['V1'],
     'phase_b_fit': {'beta_s': 2.0, 'beta_c': 24.0},
     'combo_label': 'gammaALL|RDMV1|noLOCO'},
]

VARIANTS = ['combined', 'gamma', 'rdm']  # gamma = behav-only, rdm = neural-only


# ------------------------------------------------------------------------------
# Atom building + composite argmin (2-component only)
# ------------------------------------------------------------------------------
def build_atoms(variant, cand, hc_subset, cvd_amps, hc_amps_by_roi,
                K_by_roi, C_by_roi, cvd_jnd):
    """Build the loss atoms for a variant using a given HC subset as reference."""
    atoms = {}
    jnd_pool = [h for h in hc_subset if h in HC_JND_SUBJS]
    if variant in ('combined', 'gamma') and cvd_jnd is not None:
        for p in cand['gamma_pairs']:
            fn = make_gamma_pair_atom(p, cvd_jnd, jnd_pool)
            if fn is not None:
                atoms[f'gamma_{p}'] = fn
    if variant in ('combined', 'rdm'):
        for roi in cand['rdm_rois']:
            if roi in cvd_amps:
                pool = {h: hc_amps_by_roi[roi][h] for h in hc_subset
                        if h in hc_amps_by_roi[roi]}
                if len(pool) >= 2:
                    fn = make_rdm_atom(roi, cvd_amps[roi], pool,
                                       C_by_roi[roi], K_by_roi[roi])
                    if fn is not None:
                        atoms[f'rdm_{roi}'] = fn
    return atoms


def composite_argmin(atoms, family):
    """z-sum composite over atoms -> 2-component argmin (beta_s, beta_c)."""
    if not atoms:
        return None
    z_sum = None
    for name, fn in atoms.items():
        z = zscore_grid(grid_eval_2comp(fn, family))
        if np.all(np.isnan(z)):
            return None
        z_sum = z if z_sum is None else z_sum + z
    comp = z_sum / np.sqrt(len(atoms))
    return argmin_2comp(comp)


# ------------------------------------------------------------------------------
# Held-out term evaluators
# ------------------------------------------------------------------------------
def gamma_heldout_loss(delta_8vec, gamma_pairs, cvd_jnd, heldout_jnd, train_sd):
    """L_gamma on held-out HC: baseline=held-out HC JND, SD=train(6-HC) SD.

    pred = heldout_HC_JND(pair) * (d_phys / d_perceived(delta)); target = CVD JND.
    """
    if cvd_jnd is None or heldout_jnd is None:
        return None
    perceived = (HUES + delta_8vec) % 360.0
    names = (list(PAIR_HUES.keys()) if gamma_pairs == ['ALL']
             else [PAIR_KEYS[p] for p in gamma_pairs])
    total = 0.0
    n = 0
    for pn in names:
        if pn not in PAIR_HUES:
            continue
        ta, tb = PAIR_HUES[pn]
        obs = cvd_jnd.get(pn)
        base = heldout_jnd.get(pn)
        sd = train_sd.get(pn)
        if obs is None or base is None or sd is None:
            continue
        sd = max(sd, 1e-3)
        i = int(round(ta / 45.0)) % 8
        j = int(round(tb / 45.0)) % 8
        d_phys = min(abs(ta - tb) % 360, 360 - abs(ta - tb) % 360)
        d_perc_raw = abs(perceived[i] - perceived[j]) % 360
        d_perc = max(min(d_perc_raw, 360 - d_perc_raw), 1e-3)
        pred = base * (d_phys / d_perc)
        total += ((pred - obs) / sd) ** 2
        n += 1
    return (total / n) if n > 0 else None


def rdm_heldout_eval(fit, roi, cvd_amp, heldout_hc, hc_amps_by_roi, C, K, family):
    """L_RDM on held-out single HC + random-delta grid-null percentile."""
    if heldout_hc not in hc_amps_by_roi[roi]:
        return None
    test_pool = {heldout_hc: hc_amps_by_roi[roi][heldout_hc]}
    atom = make_rdm_atom_n1ok(roi, cvd_amp, test_pool, C, K)
    if atom is None:
        return None
    grid = grid_eval_2comp(atom, family)  # 26 x 51 of L_RDM_test
    bi = int(np.argmin(np.abs(BS_GRID - fit['beta_s'])))
    bj = int(np.argmin(np.abs(BC_GRID - fit['beta_c'])))
    val = float(grid[bi, bj])
    flat = grid[np.isfinite(grid)]
    if flat.size == 0 or not np.isfinite(val):
        return None
    pct = float(np.mean(flat < val))  # fraction of grid BETTER than fitted; low = good
    test_argmin = argmin_2comp(grid)
    return {
        'L_rdm_test': val,
        'grid_null_percentile': pct,       # low = fitted generalizes / specific
        'L_rdm_test_min': float(np.nanmin(grid)),  # oracle (test-fold best)
        'gen_gap': float(val - np.nanmin(grid)),   # val - oracle; 0 = perfect transfer
        'L_rdm_test_at_00': float(atom(np.zeros(8))),  # ~1.0 degenerate (documented)
        'test_argmin': test_argmin,
    }


# ------------------------------------------------------------------------------
# Per-candidate run
# ------------------------------------------------------------------------------
def run_candidate(cand, cvd_amps, hc_amps_by_roi, K_by_roi, C_by_roi, cvd_jnd):
    family = cand['family']
    rec = {'id': cand['id'], 'subject': cand['subject'], 'family': family,
           'combo_label': cand['combo_label'], 'phase_b_fit': cand['phase_b_fit']}

    # ---- (Q2) STANDALONE full-pool (7 HC) fits per variant ----
    standalone = {}
    for v in VARIANTS:
        atoms = build_atoms(v, cand, HC_SUBJS, cvd_amps, hc_amps_by_roi,
                            K_by_roi, C_by_roi, cvd_jnd)
        fit = composite_argmin(atoms, family) if atoms else None
        standalone[v] = {
            'atoms': list(atoms.keys()),
            'fit': ({'beta_s': fit['beta_s'], 'beta_c': fit['beta_c'],
                     'boundary': fit['boundary']} if fit else None),
        }
    rec['standalone_full_pool'] = standalone

    # ---- (Q1) Held-out HC-LOO predictive eval per variant ----
    loo = {}
    for v in VARIANTS:
        folds = []
        for held in HC_SUBJS:
            train_hcs = [h for h in HC_SUBJS if h != held]
            atoms = build_atoms(v, cand, train_hcs, cvd_amps, hc_amps_by_roi,
                                K_by_roi, C_by_roi, cvd_jnd)
            fit = composite_argmin(atoms, family) if atoms else None
            if fit is None:
                folds.append({'held_out_hc': held, 'fit': None})
                continue
            delta_star = forward_2comp(fit['beta_s'], fit['beta_c'], family)
            fold = {'held_out_hc': held,
                    'fit': {'beta_s': fit['beta_s'], 'beta_c': fit['beta_c']}}

            # gamma term (reference-robustness): only if variant has gamma
            if v in ('combined', 'gamma') and cand['gamma_pairs']:
                train_jnd = [h for h in train_hcs if h in HC_JND_SUBJS]
                _, train_sd = jnd_baseline_from_pool(train_jnd)
                heldout_jnd = (load_jnd_per_pair(held)
                               if held in HC_JND_SUBJS else None)
                Lg_fit = gamma_heldout_loss(delta_star, cand['gamma_pairs'],
                                            cvd_jnd, heldout_jnd, train_sd)
                Lg_00 = gamma_heldout_loss(np.zeros(8), cand['gamma_pairs'],
                                           cvd_jnd, heldout_jnd, train_sd)
                fold['gamma'] = {
                    'L_gamma_test': Lg_fit,
                    'L_gamma_test_at_00': Lg_00,
                    'delta': ((Lg_fit - Lg_00)
                              if (Lg_fit is not None and Lg_00 is not None)
                              else None),
                }

            # rdm term (held-out prediction vs grid null): only if variant has rdm
            if v in ('combined', 'rdm') and cand['rdm_rois']:
                roi = cand['rdm_rois'][0]
                rr = rdm_heldout_eval(fit, roi, cvd_amps[roi], held,
                                      hc_amps_by_roi, C_by_roi[roi],
                                      K_by_roi[roi], family)
                fold['rdm'] = rr
            folds.append(fold)

        loo[v] = {'folds': folds, 'summary': summarize_loo(folds)}
    rec['heldout_loo'] = loo

    # ---- (Q1, decisive) does held-out RDM prediction IDENTIFY the value? ----
    rec['rdm_identifiability'] = rdm_identifiability(
        cand, cvd_amps, hc_amps_by_roi, K_by_roi, C_by_roi)
    return rec


def rdm_identifiability(cand, cvd_amps, hc_amps_by_roi, K_by_roi, C_by_roi):
    """IN-SAMPLE aggregation-sensitivity of the RDM surface (NOT a held-out CV).

    Surface = mean over the 7 single-HC loss grids (mean-of-cosines). This is a
    DIFFERENT estimator than production (cosine-of-the-mean-HC-RDM) and is
    evaluated in-sample (no train/test split). Its argmin vs the production-style
    rdm-only fit (cosine-of-mean, also in-sample) isolates AGGREGATION sensitivity:
    if the two argmins disagree, the optimum is fragile to how HCs are pooled.
    The genuine held-out identifiability signal is the per-fold oracle beta_c in
    heldout_loo (estimator-clean). A low-loss SET spanning a wide beta range
    (esp. crossing beta_c=0) flags a broad in-sample optimum.
    """
    roi = cand['rdm_rois'][0]
    fam = cand['family']
    if roi not in cvd_amps:
        return None
    cvd_amp = cvd_amps[roi]
    grids = []
    for h in HC_SUBJS:
        if h not in hc_amps_by_roi[roi]:
            continue
        atom = make_rdm_atom_n1ok(roi, cvd_amp, {h: hc_amps_by_roi[roi][h]},
                                  C_by_roi[roi], K_by_roi[roi])
        if atom is None:
            continue
        grids.append(grid_eval_2comp(atom, fam))
    if not grids:
        return None
    G = np.nanmean(np.stack(grids, axis=0), axis=0)
    gmin = float(np.nanmin(G)); gmax = float(np.nanmax(G)); rng = gmax - gmin
    mask = G <= (gmin + 0.05 * rng)
    bi, bj = np.where(mask)
    ai = np.unravel_index(np.nanargmin(G), G.shape)
    bc_lo, bc_hi = float(BC_GRID[bj].min()), float(BC_GRID[bj].max())
    return {
        'roi': roi,
        'estimator': 'in-sample mean-of-single-HC-cosines (NOT held-out CV)',
        'meancos_surface_min': gmin, 'meancos_surface_range': rng,
        'meancos_argmin': {'beta_s': float(BS_GRID[ai[0]]), 'beta_c': float(BC_GRID[ai[1]])},
        'lowset_frac_grid': float(mask.sum() / G.size),
        'lowset_beta_s_span': [float(BS_GRID[bi].min()), float(BS_GRID[bi].max())],
        'lowset_beta_c_span': [bc_lo, bc_hi],
        'beta_c_sign_ambiguous': bool(bc_lo < 0 and bc_hi > 0),
    }


def summarize_loo(folds):
    s = {}
    # gamma: delta (fitted - (0,0)); negative = explains CVD anomaly
    dgs = [f['gamma']['delta'] for f in folds
           if f.get('gamma') and f['gamma'].get('delta') is not None]
    if dgs:
        dgs = np.array(dgs)
        s['gamma_delta_median'] = float(np.median(dgs))
        s['gamma_delta_iqr'] = float(np.percentile(dgs, 75) - np.percentile(dgs, 25))
        s['gamma_delta_neg_frac'] = float(np.mean(dgs < 0))  # fraction of folds beating (0,0)
        s['n_gamma_folds'] = int(dgs.size)
    # rdm PRIMARY metric: ΔL vs (0,0) no-correction baseline (same treatment as gamma).
    # "Is the stable value GOOD?" = does it beat no-correction on held-out HC.
    # (0,0) for rdm = no-structure floor (loss≡1.0); grid percentile de-confounds the win.
    Lt = [f['rdm']['L_rdm_test'] for f in folds
          if f.get('rdm') and f['rdm'].get('L_rdm_test') is not None]
    L00 = [f['rdm'].get('L_rdm_test_at_00', 1.0) for f in folds
           if f.get('rdm') and f['rdm'].get('L_rdm_test') is not None]
    if Lt:
        Lt = np.array(Lt); L00 = np.array(L00); dL = Lt - L00
        s['rdm_L_test_median'] = float(np.median(Lt))
        s['rdm_dL_vs00_median'] = float(np.median(dL))
        s['rdm_dL_vs00_neg_frac'] = float(np.mean(dL < 0))  # folds beating no-correction
    # rdm de-confounder: grid-null percentile (low = beats arbitrary shift, not just (0,0))
    pcts = [f['rdm']['grid_null_percentile'] for f in folds
            if f.get('rdm') and f['rdm'].get('grid_null_percentile') is not None]
    gaps = [f['rdm']['gen_gap'] for f in folds
            if f.get('rdm') and f['rdm'].get('gen_gap') is not None]
    if pcts:
        pcts = np.array(pcts)
        s['rdm_percentile_median'] = float(np.median(pcts))
        s['rdm_percentile_iqr'] = float(np.percentile(pcts, 75) - np.percentile(pcts, 25))
        s['rdm_low_frac'] = float(np.mean(pcts < 0.25))  # folds where fitted in best quartile
        s['n_rdm_folds'] = int(pcts.size)
    if gaps:
        s['rdm_gen_gap_median'] = float(np.median(gaps))  # footnote only (closeness-to-oracle)
    # ESTIMATOR-CLEAN held-out identifiability: per-fold oracle argmin (each fold
    # = argmin of a genuinely held-out single-HC RDM surface). Wandering / sign-
    # flipping oracle beta_c => value not identified by held-out prediction.
    obc = [f['rdm']['test_argmin']['beta_c'] for f in folds
           if f.get('rdm') and f['rdm'].get('test_argmin')]
    obs_ = [f['rdm']['test_argmin']['beta_s'] for f in folds
            if f.get('rdm') and f['rdm'].get('test_argmin')]
    if obc:
        obc = np.array(obc); obs_ = np.array(obs_)
        s['oracle_bc_values'] = [float(x) for x in obc]
        s['oracle_bc_neg_frac'] = float(np.mean(obc < 0))
        s['oracle_bc_iqr'] = float(np.percentile(obc, 75) - np.percentile(obc, 25))
        s['oracle_bs_iqr'] = float(np.percentile(obs_, 75) - np.percentile(obs_, 25))
    return s


# ------------------------------------------------------------------------------
def make_md(results):
    L = ["# S18 — Held-out-HC predictive eval + standalone fits", "",
         f"_generated: {results['meta'].get('elapsed_sec')}s, "
         f"{results['meta']['n_candidates']} candidates_", "",
         "## Q2 — Standalone full-pool (7 HC) fits  (beta_s, beta_c)", "",
         "| Candidate | combined (prod) | gamma-only (behav) | rdm-only (neural) |",
         "|---|---|---|---|"]
    for c in results['candidates']:
        sa = c['standalone_full_pool']
        def fmt(v):
            f = sa[v]['fit']
            return f"({f['beta_s']:.0f}, {f['beta_c']:.0f})" if f else "—"
        pb = c['phase_b_fit']
        L.append(f"| {c['id']} (prod ({pb['beta_s']:.0f},{pb['beta_c']:.0f})) "
                 f"| {fmt('combined')} | {fmt('gamma')} | {fmt('rdm')} |")
    L += ["", "## Q1 — Held-out HC-LOO predictive performance: does the stable value "
          "beat no-correction (0,0)?", "",
          "Primary metric = **ΔL vs (0,0)** (test-loss improvement over no-correction), "
          "applied uniformly to gamma and rdm. For rdm, (0,0) = no-structure floor "
          "(loss≡1.0); the grid percentile de-confounds the (0,0) win (LOW pct = beats "
          "arbitrary shift, not just the floor). gen_gap (vs held-out oracle) demoted to "
          "footnote — answers 'close to best', not 'good'.", "",
          "| Candidate | variant | gamma ΔL med (neg_frac) | rdm L_test med | rdm ΔL vs(0,0) med (folds<00) | rdm grid pct med |",
          "|---|---|---|---|---|---|"]
    for c in results['candidates']:
        for v in VARIANTS:
            s = c['heldout_loo'][v]['summary']
            g = ("—" if 'gamma_delta_median' not in s
                 else f"{s['gamma_delta_median']:+.2f} ({s['gamma_delta_neg_frac']:.2f})")
            lt = ("—" if 'rdm_L_test_median' not in s
                  else f"{s['rdm_L_test_median']:.3f}")
            dl = ("—" if 'rdm_dL_vs00_median' not in s
                  else f"{s['rdm_dL_vs00_median']:+.3f} ({s['rdm_dL_vs00_neg_frac']:.2f})")
            r = ("—" if 'rdm_percentile_median' not in s
                 else f"{s['rdm_percentile_median']:.2f}")
            L.append(f"| {c['id']} | {v} | {g} | {lt} | {dl} | {r} |")
    L += ["", "## Q1 (caveat, NOT the headline) — per-fold oracle β_c spread", "",
          "The headline is the ΔL-vs-(0,0) table above (stable value beats no-correction). "
          "The quantity below is the per-fold ORACLE β_c (each held-out *single*-HC's own "
          "argmin) — single-HC target noise + broad-basin shallowness (closure Test 2a "
          "~20° width). It is NOT the test-loss and NOT a basis for an identifiability "
          "verdict on the (stable) train fit (s17: S08 β_c[-46,-38]; S09 (2,24) det.).", "",
          "| Candidate | prod beta_c | per-fold oracle beta_c | neg_frac | oracle bc IQR | note |",
          "|---|---|---|---|---|---|"]
    for c in results['candidates']:
        pb = c['phase_b_fit']
        s = c['heldout_loo']['combined']['summary']
        if 'oracle_bc_values' not in s:
            L.append(f"| {c['id']} | {pb['beta_c']:.0f} | — | — | — | — |")
            continue
        vals = ",".join(f"{v:.0f}" for v in s['oracle_bc_values'])
        nf = s['oracle_bc_neg_frac']; iqr = s['oracle_bc_iqr']
        L.append(f"| {c['id']} | {pb['beta_c']:.0f} | {vals} | {nf:.2f} | {iqr:.0f} | single-HC noise / basin width |")
    L += ["", "**(b) In-sample aggregation sensitivity** — mean-of-cosines argmin "
          "vs production-style cosine-of-mean (rdm-only standalone). Both in-sample; "
          "disagreement = optimum fragile to HC pooling (NOT a generalization claim).", "",
          "| Candidate | cosine-of-mean (rdm-only) | mean-of-cosines | low-set beta_c | beta_c sign amb? | aggregation |",
          "|---|---|---|---|---|---|"]
    for c in results['candidates']:
        idf = c.get('rdm_identifiability')
        if not idf:
            L.append(f"| {c['id']} | — | — | — | — | — |")
            continue
        rstd = c['standalone_full_pool']['rdm']['fit']
        com = f"({rstd['beta_s']:.0f},{rstd['beta_c']:.0f})" if rstd else "—"
        mc = idf['meancos_argmin']
        bc_sp = idf['lowset_beta_c_span']
        robust = (rstd is not None and abs(mc['beta_c'] - rstd['beta_c']) <= 12)
        L.append(f"| {c['id']} | {com} | ({mc['beta_s']:.0f},{mc['beta_c']:.0f}) "
                 f"| [{bc_sp[0]:.0f},{bc_sp[1]:.0f}] "
                 f"| {'YES' if idf['beta_c_sign_ambiguous'] else 'no'} "
                 f"| {'robust' if robust else 'FRAGILE'} |")
    L += ["", "## Interpretation guardrails", "",
          "- gamma dL < 0 = fitted shift explains CVD JND anomaly on held-out HC "
          "ref better than no-shift; neg_frac near 1.0 = consistent.",
          "- rdm percentile near 0 = train-fitted shift is also (near-)optimal for "
          "held-out HC's CVD-vs-HC geometry = generalizes. Near 0.5 = the specific "
          "value does not transfer (any shift comparable).",
          "- These are GENERALIZATION numbers, not specificity (§0). Expected outcome "
          "given closure verification (~20-25deg floor): most cells near null. "
          "A non-circular reportable metric is the deliverable, not a rescue."]
    return "\n".join(L)


def main():
    t0 = time.time()
    print("=" * 90, flush=True)
    print("S18 — held-out-HC predictive eval + standalone neural/behav fits", flush=True)
    print("=" * 90, flush=True)

    subjects = sorted({c['subject'] for c in CANDIDATES})
    cvd_amps_by_subj, hc_amps_by_roi, K_by_roi, C_by_roi, cvd_jnd_by_subj = \
        preload_data(subjects)

    results = {'candidates': [], 'meta': {
        'design': 'leave-one-HC-out (7-fold) held-out predictive + 7-HC standalone',
        'variants': VARIANTS,
        'gamma_handling': 'baseline=held-out HC JND, SD=train 6-HC SD; dL vs (0,0) meaningful',
        'rdm_handling': 'held-out single-HC target; (0,0) DEGENERATE -> grid-null percentile',
        'asymmetry': 'gamma=reference-robustness, rdm=held-out prediction (user-agreed 2026-06-02)',
    }}

    for cand in CANDIDATES:
        tc = time.time()
        print(f"\n[{cand['id']}] {cand['subject']} {cand['combo_label']}", flush=True)
        rec = run_candidate(
            cand, cvd_amps_by_subj[cand['subject']], hc_amps_by_roi,
            K_by_roi, C_by_roi, cvd_jnd_by_subj[cand['subject']])
        results['candidates'].append(rec)
        sa = rec['standalone_full_pool']
        for v in VARIANTS:
            f = sa[v]['fit']
            fit_s = f"({f['beta_s']:.0f},{f['beta_c']:.0f})" if f else "None"
            s = rec['heldout_loo'][v]['summary']
            print(f"  {v:9s} standalone={fit_s:12s} "
                  f"gamma_dL_med={s.get('gamma_delta_median')} "
                  f"rdm_pct_med={s.get('rdm_percentile_median')}", flush=True)
        print(f"  elapsed {time.time()-tc:.1f}s", flush=True)

    results['meta']['elapsed_sec'] = round(time.time() - t0, 1)
    results['meta']['n_candidates'] = len(CANDIDATES)

    out_json = OUT_DIR / "s18_heldout_predictive.json"
    with open(out_json, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    out_md = OUT_DIR / "s18_heldout_predictive.md"
    with open(out_md, 'w') as f:
        f.write(make_md(results))
    print(f"\n[done] {results['meta']['elapsed_sec']}s  saved={out_json.name}, {out_md.name}",
          flush=True)


if __name__ == "__main__":
    main()
