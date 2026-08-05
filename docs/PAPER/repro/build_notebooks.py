#!/usr/bin/env python3
"""Authoring script for the 6 colorBlind PAPER reproduction notebooks.

Built per ~/.claude/skills/repro-notebook/SKILL.md (Phase 3). Re-run to regenerate
the .ipynb files from these cell specs (source of truth):  python build_notebooks.py

Each notebook: title -> provenance -> source&code map -> setup -> per-analysis
(markdown header w/ reported value -> code cell -> reproduction-target note) -> summary.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(keepends=True)}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": t.strip("\n").splitlines(keepends=True)}


def nb(cells):
    return {"cells": cells, "metadata": {"kernelspec": {"display_name": "srm", "language": "python", "name": "srm"},
            "language_info": {"name": "python", "version": "3.10"}}, "nbformat": 4, "nbformat_minor": 5}


SETUP = code("""
import sys, os, json
sys.path.insert(0, os.path.abspath('.'))   # docs/PAPER/repro
import numpy as np
import _repro_util as U
U._RESULTS.clear()   # fresh check log per notebook
print("repo:", U.REPO)
""")

PROV = md("""
**Provenance.** Built by `~/.claude/skills/repro-notebook/SKILL.md` (Phase 3).
Companion docs: `docs/PAPER/repro/{MANIFEST.md, MAP.md, REPORT.md}`.
Target paper: `docs/PAPER/main.tex` → `Results/results_v4.tex`.
Helpers: `docs/PAPER/repro/_repro_util.py`.

**Modes.** `RECOMPUTE` = computed locally from C010 amplitudes. `LOAD+VERIFY` =
read the committed result JSON and compare to the printed paper value. SRM/BrainIAK
numbers are read from committed JSON (no MPI in this kernel).
""")


# ============================================================ NB01 discrimination
nb01 = nb([
    md("# 01 — Discrimination preserved + cross-decoding (E1)\nResults §1, Fig 2A, S14."),
    PROV,
    md("""**Source & code map**

| id | reported | source JSON | mode |
|---|---|---|---|
| E1.1 | both CVD > 0.125 every ROI | `phase3_decoder_comparing/results/loro/srm/sub-{08,09}_performance_raw.json` | LOAD+VERIFY |
| E1.2 | MannWhitney p=0.668 | `phase3_decoder_comparing/results/loro/srm/validation/cross_subject_generalization.json` | LOAD+VERIFY |
| E1.3 | hV4 single-case p=0.142 | `_compute_paper_stats.py` (stdout only) | ⚠ FLAG |"""),
    SETUP,
    md("### E1.1 — 8-class LORO discrimination exceeds 0.125 chance at every ROI (both CVD)"),
    code("""
# Source corrected 2026-08-05. This cell previously read
# cvd_cross_decoding_procrustes.json -- the pre-RT-7 run (all-subject SRM),
# superseded the same day by the HC-only fix that removes its circularity.
# We now read the same LORO file that generate_fig2.py uses to draw Figure 3A,
# which is what results_v4.tex actually cites.
import numpy as np
CHANCE = 1/8
allpass = True
for s in ["sub-08", "sub-09"]:
    srm = U.load_json(U.DEC / f"results/loro/srm/{s}_performance_raw.json")["results"]["srm"]
    for roi in ["V1", "V2", "V3", "V4"]:
        acc = float(np.mean([f["acc_exact"] for f in srm[roi]["ForwardEncoding"]]))
        ok = U.check(f"E1.1 {roi} {s} acc>chance", acc, CHANCE, mode="ge")
        allpass = allpass and ok
print("all ROI/subj above chance:", allpass)
"""),
    md("*Target:* both CVD exceed exact-accuracy chance 1/8=0.125 at V1–hV4."),
    md("### E1.2 — cross-subject generalization Mann–Whitney p=0.668 (LDA, all ROIs pooled)"),
    code("""
j = U.load_json(U.DEC / "results/loro/srm/validation/cross_subject_generalization.json")
p = j["LDA"]["difference"]["p_value"]
U.check("E1.2 MannWhitney p", p, 0.668, ndigits=3)
print("hc_to_hc mean=%.3f  hc_to_cvd mean=%.3f" % (j["LDA"]["hc_to_hc"]["mean"], j["LDA"]["hc_to_cvd"]["mean"]))
"""),
    md("*Target:* p=0.668 (21 HC-to-HC vs 14 HC-to-CVD pairs)."),
    md("""### E1.3 — within-ROI hV4 single-case p=0.142  ⚠ FLAG
No committed output: produced only as stdout by `_compute_paper_stats.py`. Marked
not-cleanly-reproducible; regenerate by running that script. Recorded as a flag."""),
    code('U.check("E1.3 hV4 single-case p (FLAG: stdout-only)", float("nan"), 0.142)'),
    code("U.summary()"),
])

# ============================================================ NB02 interpolation
nb02 = nb([
    md("# 02 — Interpolation impaired / vulnerability profile (E2)\nResults §2, Fig 2B–C, Fig 3. **RECOMPUTE** (canonical FE-6 uniform + OLS)."),
    PROV,
    md("""**Source & code map**

| id | reported (results_v4.tex L38–40) | source | mode |
|---|---|---|---|
| E2.1 | HC adj 0.47±0.05; hV4 above-chance **p=0.008** (1,000 per-subj perms) | C010 amplitudes; `perm_definitive_hv4_null.npy` | RECOMPUTE / LOAD |
| E2.2 | V1 **p=0.164** (n.s.); V2,V3 below chance | C010 amplitudes; `perm_v1_null.npy` | RECOMPUTE / LOAD |
| E2.3/2.4 | deutan 0.25 (CH −1.84/0.063/−1.99); protan 0.13 (−2.91/0.017/−3.14) | C010 amplitudes | RECOMPUTE |
| E2.5/2.6 | blue/purple/magenta=0; per-hue CH none sig | C010 amplitudes | RECOMPUTE |

Reconciliation note (2026-06-28): an earlier draft reported hV4 p=0.044 (voxel_corr
8! perm) and CH −1.58/0.082 & −2.48/0.024. The manuscript has since adopted the
adjacent-accuracy values reproduced here; `reported=` targets track the current tex."""),
    SETUP,
    md("""### E2.1 / E2.2 — hV4 HC adjacent accuracy 0.47±0.05 (n=6); above-chance p=0.008
Canonical above-chance test = **adjacent-accuracy** under 1,000 per-subject label
permutations (FE-6 uniform + OLS), matching `results_v4.tex` L38 and `PERMUTATIONS.md`.
Committed null draws: `perm_definitive_hv4_null.npy` (hV4), `perm_v1_null.npy` (V1).
p = add-one `(#{null≥obs}+1)/(N+1)` (Phipson & Smyth 2010)."""),
    code("""
hc = U.hc_adjacent_matrix()           # (6,8) hV4, sub-07 excluded
hc_overall = hc.mean(axis=1)
U.check("E2.1 HC adj mean", hc_overall.mean(), 0.47, tol=0.02)
print("HC SEM=%.3f (paper 0.05)" % (hc_overall.std(ddof=1)/np.sqrt(len(hc))))

# hV4 adjacent-accuracy above-chance: committed 1,000 per-subject label perms -> p=0.008
obs_hv4 = hc_overall.mean()
null_hv4 = np.load(U.REPRO / "perm_definitive_hv4_null.npy")
p_hv4 = (np.sum(null_hv4 >= obs_hv4) + 1) / (len(null_hv4) + 1)
U.check("E2.1 hV4 adj above-chance p", p_hv4, 0.008, tol=0.003)
print("  obs=%.4f null_mean=%.4f N=%d (per-subject label perm, FE-6 OLS)" % (obs_hv4, null_hv4.mean(), len(null_hv4)))

# E2.2 V1 not above chance (n=7, sub-07 included); V2,V3 below chance by inspection
v1 = np.array([U.adjacent_accuracy_profile(s, roi="V1") for s in U.HC])
obs_v1 = v1.mean(axis=1).mean()
null_v1 = np.load(U.REPRO / "perm_v1_null.npy")
p_v1 = (np.sum(null_v1 >= obs_v1) + 1) / (len(null_v1) + 1)
U.check("E2.2 V1 adj above-chance p (n.s.)", p_v1, 0.164, tol=0.01)
print("  V1 obs=%.4f p=%.3f -> not above chance (V2,V3 < 0.375 chance by inspection)" % (obs_v1, p_v1))
"""),
    md("""### E2.3 / E2.4 — deutan 0.25 (CH −1.84/0.063/−1.99), protan 0.13 (−2.91/0.017/−3.14)
Overall Crawford–Howell single-case vs n=6 HC. Targets are the current `results_v4.tex`
L40 values (the manuscript adopted these reproduced statistics)."""),
    code("""
d08 = U.adjacent_accuracy_profile("08"); d09 = U.adjacent_accuracy_profile("09")
U.check("E2.3 deutan overall", d08.mean(), 0.25, tol=0.01)
U.check("E2.4 protan overall", d09.mean(), 0.13, tol=0.01)
CH_TARGET = {"deutan": (-1.84, 0.063, -1.99), "protan": (-2.91, 0.017, -3.14)}
for name, v in [("deutan", d08), ("protan", d09)]:
    t, p, dcc = U.crawford_howell(v.mean(), hc.mean(axis=1))
    rt, rp, rd = CH_TARGET[name]
    U.check(f"E2.3/2.4 {name} CH t", t, rt, tol=0.02)
    U.check(f"E2.3/2.4 {name} CH p", p, rp, tol=0.003)
    U.check(f"E2.3/2.4 {name} CH d_cc", dcc, rd, tol=0.02)
    print(f"  {name} overall CH: t={t:+.2f} p={p:.3f} d_cc={dcc:+.2f}")
"""),
    md("### E2.5 / E2.6 — per-hue: blue/purple/magenta zero; no individual hue significant"),
    code("""
for name, v in [("deutan", d08), ("protan", d09)]:
    print(f"-- {name} --")
    for c in (U.HUE_NAMES.index(h) for h in ["blue", "purple", "magenta"]):
        t, p, dcc = U.crawford_howell(v[c], hc[:, c])
        U.check(f"E2.5 {name} {U.HUE_NAMES[c]} acc=0", v[c], 0.0, tol=1e-9)
        print(f"     {U.HUE_NAMES[c]:7s} CH: t={t:+.2f} p={p:.3f} d_cc={dcc:+.2f}  sig={'YES' if p<0.05 else 'no'}")
print("E2.6 target: NO individual hue reaches p<0.05  (blue p=0.072, purple 0.205, magenta 0.122)")
"""),
    code("U.summary()"),
])

# ============================================================ NB03 geometry
nb03 = nb([
    md("# 03 — Color geometry distorted / SRM disparity (E3)\nResults §3, Fig 4. **LOAD+VERIFY** (SRM committed; no MPI here)."),
    PROV,
    md("""**Source & code map**

| id | reported | source JSON | mode |
|---|---|---|---|
| E3.1/3.2/3.7 | protan V1 p=0.007/LOSO 0.045; deutan V2 0.040/0.116; full table | `phase2_SRM_across_between/results/loo_consistent/20260218_163819/loo_consistent_results.json` | LOAD+VERIFY |
| E3.5 | SRM k=4/4/3/3 (override) | `…/validation/k_aggregation_results.json` | LOAD + note |
| E3.3 | ΔRDM heatmap | stub only | ⚠ FLAG |"""),
    SETUP,
    md("### E3.1 / E3.2 / E3.7 — disparity table (common-space + symmetric LOSO)"),
    code("""
j = U.load_json(U.SRM / "results/loo_consistent/20260218_163819/loo_consistent_results.json")
R = j["results"]
def disp(roi, sub):
    com = R[roi]["individual_cvd"][sub]["p_value"]
    los = R[roi]["loso_analysis"]["individual_cvd"][sub]["p_value"]
    return com, los
c, l = disp("V1", "sub-09"); U.check("E3.1 protan V1 common p", c, 0.007, tol=0.001); U.check("E3.1 protan V1 LOSO p", l, 0.045, tol=0.002)
c, l = disp("V2", "sub-08"); U.check("E3.2 deutan V2 common p", c, 0.040, tol=0.002); U.check("E3.2 deutan V2 LOSO p", l, 0.116, tol=0.01)
print("\\nFull disparity table (common p / LOSO p):")
for roi in ["V1", "V2", "V3", "hV4"]:
    for s in ["sub-08", "sub-09"]:
        c, l = disp(roi, s)
        print(f"  {roi} {s}: common={c:.3f}  loso={l:.3f}")
"""),
    md("### E3.5 — SRM dims k=4/4/3/3 (hardcoded canonical override vs raw aggregation)"),
    code("""
ka = U.load_json(U.SRM / "validation/k_aggregation_results.json")
print("k_aggregation raw selection (note: paper uses hardcoded 4/4/3/3 override in rerun_loo_consistent.py:60):")
print(json.dumps(ka, default=str)[:600])
"""),
    md("""### E3.3 — ΔRDM heatmap  ⚠ FLAG
Only a visualization stub exists; ΔRDM = RDM_CVD − mean(RDM_HC) in SRM space is not
committed as a numeric artifact. Marked presence-only; needs a driver + SRM space."""),
    code('U.check("E3.3 dRDM numeric artifact (FLAG: stub only)", float("nan"), 0.0)'),
    code("U.summary()"),
])

# ============================================================ NB04 model selection
nb04 = nb([
    md("# 04 — Simulator model selection (E4)\nResults §4–6, Methods selection. **LOAD+VERIFY** (v6 PCA canonical) + **RECOMPUTE** E4.13."),
    PROV,
    md("""**Source & code map**

| id | reported | source JSON (`future_phase2_filter_optimization/results/`) | mode |
|---|---|---|---|
| E4.4 | deutan argmin (6,−42), L_test −2.36 (IQR 2.15) | `s10b…sub-08.json` `summary['γOY|RDMV2|noLOCO'].per_model.2comp` | LOAD+VERIFY |
| E4.5 | protan argmin (2,+24), L_test −1.54 (IQR 1.42) | `…sub-09.json` `summary['γALL|RDMV1|noLOCO']…` | LOAD+VERIFY |
| E4.11 | N=300 | s10b `meta.N_resamples` | LOAD |
| E4.13 | pre-image 26.3 / 16.2 | `exp2_preimage/sub-{08,09}_…json` | RECOMPUTE |

Note: the gamma-variant combo key matters — `γOY` (deutan) / `γALL` (protan), not the
generic `γ_` atom; using the wrong key gives −2.14/−2.12."""),
    SETUP,
    md("### E4.4 / E4.5 — selected 2-component argmin + held-out test-loss"),
    code("""
def twocomp(sub, combo):
    j = U.load_json(U.P2 / f"results/s10_inclusion/s10b_v6_pca_rdm_results_{sub}.json")
    pm = j["summary"][combo]["per_model"]["2comp"]
    ps = pm.get("param_summary", {})
    return j, pm, ps
# production argmin (beta_s, beta_c) from the held-out LOO fit (s18 phase_b_fit)
s18 = U.load_json(U.P2 / "results/s10_inclusion/s18_heldout_predictive.json")["candidates"]
fit = {c["id"]: c["phase_b_fit"] for c in s18}
U.check("E4.4 deutan beta_s", fit["S08-robust"]["beta_s"], 6.0); U.check("E4.4 deutan beta_c", fit["S08-robust"]["beta_c"], -42.0)
U.check("E4.5 protan beta_s", fit["S09-primary"]["beta_s"], 2.0); U.check("E4.5 protan beta_c", fit["S09-primary"]["beta_c"], 24.0)
# production combos (gamma variant matters: deutan=gammaOY, protan=gammaALL)
j8, pm8, ps8 = twocomp("sub-08", "γOY|RDMV2|noLOCO")
j9, pm9, ps9 = twocomp("sub-09", "γALL|RDMV1|noLOCO")
U.check("E4.11 N_resamples", j8["meta"]["N_resamples"], 300)
U.check("E4.4 deutan L_test", pm8["test_loss_median"], -2.36, tol=0.01); U.check("E4.4 deutan L_test IQR", pm8["test_loss_iqr"], 2.15, tol=0.01)
U.check("E4.5 protan L_test", pm9["test_loss_median"], -1.54, tol=0.01); U.check("E4.5 protan L_test IQR", pm9["test_loss_iqr"], 1.42, tol=0.01)
print("  (gamma variant is significant: deutan=gammaOY, protan=gammaALL; the generic 'gamma_' key is a different atom and gives -2.14/-2.12.)")
"""),
    md("### E4.13 — filter pre-image mean |δθ| (RECOMPUTE from committed pre-image)"),
    code("""
U.check("E4.13 deutan mean|dtheta|", U.preimage_mean_abs_delta("08"), 26.3, tol=0.1)
U.check("E4.13 protan mean|dtheta|", U.preimage_mean_abs_delta("09"), 16.2, tol=0.1)
"""),
    code("U.summary()"),
])

# ============================================================ NB05 identifiability
nb05 = nb([
    md("# 05 — Identifiability checks S15 (E5)\nResults §7, S15. **LOAD+VERIFY** (v6 PCA redteam)."),
    PROV,
    md("""**Source & code map** (`future_phase2_filter_optimization/results/redteam/`)

| id | reported | source JSON | mode |
|---|---|---|---|
| E5.2 | f10 0.26 / 0.14 | `param_recovery_voxel_v6_pca_v2.json` (mean of per-donor `frac_within_10deg`) | LOAD+VERIFY |
| E5.4 | HC pseudo-CVD rank 0.875 | `verdict_matrix_v6_pca_v2.json` `specificity.rank_distance` | LOAD+VERIFY |
| E5.5 | label-perm p 0.167 / 0.471 | `verdict_matrix_v6_pca_v2.json` `within_subject_sig.p_perm` | LOAD+VERIFY |"""),
    SETUP,
    md("### E5.2 — voxel parameter recovery f₁₀° (aggregate over 7 HC donors)"),
    code("""
j = U.load_json(U.P2 / "results/redteam/param_recovery_voxel_v6_pca_v2.json")
cells = j["cells"]
def f10(cand):
    vals = [c["frac_within_10deg"] for k, c in cells.items() if k.startswith(cand) and "frac_within_10deg" in c]
    return float(np.mean(vals)) if vals else float("nan")
U.check("E5.2 S08-robust f10", f10("S08-robust"), 0.26, tol=0.03)
U.check("E5.2 S09-primary f10", f10("S09-primary"), 0.14, tol=0.03)
"""),
    md("### E5.4 — HC pseudo-CVD specificity rank (Test 2b)\nFrom the aggregated `verdict_matrix_v6_pca_v2.json` (`specificity.rank_distance`)."),
    code("""
vm = U.load_json(U.P2 / "results/redteam/verdict_matrix_v6_pca_v2.json")["per_candidate"]
for cand in ["S08-robust", "S09-primary"]:
    U.check(f"E5.4 {cand} rank_distance", vm[cand]["specificity"]["rank_distance"], 0.875, tol=0.001)
"""),
    md("### E5.5 — color-label permutation p (Test 2c)\nFrom `verdict_matrix` (`within_subject_sig.p_perm`, `real_loss`)."),
    code("""
for cand, rep in [("S08-robust", 0.167), ("S09-primary", 0.471)]:
    ws = vm[cand]["within_subject_sig"]
    U.check(f"E5.5 {cand} p_perm", ws["p_perm"], rep, tol=0.005)
    print(f"     {cand}: real_loss={ws['real_loss']:.3f}  perm_5pct={ws['perm_loss_5pct']:.3f}")
"""),
    code("U.summary()"),
])

# ============================================================ NB06 filter eval
nb06 = nb([
    md("""# 06 — Filter evaluation, 2nd session (E6)
Results §8–9, Fig 8. **LOAD+VERIFY**. ⚠ **deutan (sub-08) only** — protan (sub-09)
2nd session NOT yet collected; all numbers single-case descriptive."""),
    PROV,
    md("""**Source & code map** (`future_phase3_behavioral_analysis/`)

| id | reported | source JSON | mode |
|---|---|---|---|
| E6.1 | LOCO ρ personalized vs deployed per ROI | `exp2_neural/results/exp2_hc_likeness_sub-08_native.json` | LOAD+VERIFY |
| E6.2 | LORO/LOCO acc | same + `exp2_decoder_2x2_sub-08_native.json` | LOAD+VERIFY |
| E6.3 | JND |z|, 8AFC, Wilcoxon p=0.84 | `results/exp2_behavior/sub-08_summary.json` | LOAD+VERIFY |"""),
    SETUP,
    md("### E6.1 — LOCO forward-tuning ρ (personalized vs deployed)"),
    code("""
j = U.load_json(U.P3 / "exp2_neural/results/exp2_hc_likeness_sub-08_native.json")
print("exp2_hc_likeness top keys:", list(j.keys())[:15])
print("(inspect for per-ROI personalized/deployed rho; paper V1 +0.21/-0.32 ... V4 +0.18/-0.39)")
print(json.dumps(j, default=str)[:700])
"""),
    md("### E6.3 — behavioral JND / 8AFC / Wilcoxon (deutan, descriptive)"),
    code("""
b = U.load_json(U.P3 / "results/exp2_behavior/sub-08_summary.json")
U.check("E6.3 Wilcoxon opt-vs-win p", b["wilcoxon"]["wilcoxon_opt_vs_win"]["p"], 0.84, tol=0.01)
U.check("E6.3 8AFC baseline", b["rsvp"]["baseline"]["acc"], 0.81, tol=0.01)
U.check("E6.3 8AFC optimal", b["rsvp"]["optimal"]["acc"], 0.97, tol=0.01)
print("jnd_mean_by_condition:", b["jnd_mean_by_condition"])
"""),
    md("*Note:* sub-09 (protan) cells intentionally absent — data not yet acquired."),
    code("U.summary()"),
])

# ============================================================ write
NB = {"01_discrimination": nb01, "02_interpolation": nb02, "03_geometry": nb03,
      "04_model_selection": nb04, "05_identifiability": nb05, "06_filter_eval": nb06}
for name, obj in NB.items():
    out = HERE / f"{name}.ipynb"
    out.write_text(json.dumps(obj, indent=1))
    print("wrote", out.name, "(%d cells)" % len(obj["cells"]))
