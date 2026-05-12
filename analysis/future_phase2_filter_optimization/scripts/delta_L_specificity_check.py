"""delta_L_specificity_check.py — Δ_L specificity diagnostic (descriptive only).

Loss: L = 1·L_ccc + 0.5·l_topk(V4, K=3) + 0.1·L_smooth
      L_smooth = (β_s² + β_c²) / 32400      (Tikhonov, recomputed identically
                                              for HC and CVD to remove the
                                              0.5008 factor mismatch found in
                                              cached HC sanity l_smooth)

Δ_L = L(β_s=0, β_c=0) − L(argmin)

For each subject we look up the (0,0) cell and the argmin cell of L_combined
under the subject's own vuln_obs target. No simulator rerun — vuln_sim is
cached in both CVD V4-CCC landscape and HC sanity landscape.

§0 compliance: this is a DESCRIPTIVE diagnostic, not a new selection rule.
The Δ_L number summarises "how much loss improvement does the fit buy over
the no-shift baseline", complementary to the norm metric.

Outputs (under results/CANDIDATE/v4ccc_ltopk/):
  - delta_L_per_subject.csv
  - delta_L_specificity.csv
  - delta_L_specificity_summary.md
  - delta_L_distribution.png
"""
from __future__ import annotations
import json
import sys
import csv
from pathlib import Path
import numpy as np
from scipy.stats import pearsonr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from old_formula_refit import load_cvd_loco_target

_PHASE2 = _THIS_DIR.parent
CVD_LSCAPE_DIR = _PHASE2 / 'results' / 'old_formula'
HC_SANITY_DIR = _PHASE2 / 'results' / 'fits' / 'phase_a_2component_hc_sanity'
OUT = _PHASE2 / 'results' / 'CANDIDATE' / 'v4ccc_ltopk'
OUT.mkdir(parents=True, exist_ok=True)

HC_SUBJECTS = ['01', '02', '03', '04', '05', '06']  # sub-07 V4 16 voxels → nan
CVD_SUBJECTS = [('08', 'deutan'), ('09', 'protan')]

LAMBDA_TOPK = 0.5
K_TOPK = 3
TIKH_NORM = 32400.0
N_BOOT = 10000
RNG_SEED = 42


# ----- loss components -------------------------------------------------------

def ccc_value(sim, obs):
    sim = np.asarray(sim, dtype=float)
    obs = np.asarray(obs, dtype=float)
    if np.std(sim) < 1e-10 or np.std(obs) < 1e-10:
        return 0.0
    r, _ = pearsonr(sim, obs)
    if not np.isfinite(r):
        return 0.0
    msim, mobs = sim.mean(), obs.mean()
    ssim, sobs = sim.std(), obs.std()
    denom = ssim**2 + sobs**2 + (msim - mobs)**2
    if denom < 1e-10:
        return 0.0
    return 2.0 * r * ssim * sobs / denom


def l_topk_jaccard(sim, obs, K=K_TOPK):
    s = np.asarray(sim); o = np.asarray(obs)
    top_s = set(np.argsort(s)[:K].tolist())
    top_o = set(np.argsort(o)[:K].tolist())
    inter = len(top_s & top_o); union = len(top_s | top_o)
    return 1.0 - (inter / union)


def L_smooth_norm(bs, bc):
    return (float(bs)**2 + float(bc)**2) / TIKH_NORM


def L_combined(vuln_sim, vuln_obs, bs, bc):
    ccc = ccc_value(vuln_sim, vuln_obs)
    l_ccc = (1.0 - ccc) / 2.0
    lt = l_topk_jaccard(vuln_sim, vuln_obs, K=K_TOPK)
    ls = L_smooth_norm(bs, bc)
    return 1.0 * l_ccc + LAMBDA_TOPK * lt + 0.1 * ls, l_ccc, lt, ls, ccc


# ----- landscape loaders -----------------------------------------------------

def load_cvd_cells(sid):
    fn = CVD_LSCAPE_DIR / f'sub-{sid}_V4_V4ccc_landscape.json'
    d = json.load(open(fn))
    cells = d['cells']
    out = []
    for c in cells:
        out.append({
            'bs': float(c['bs']),
            'bc': float(c['bc']),
            'vuln_sim': np.asarray(c['vuln_sim'], dtype=float),
        })
    return out


def load_hc_cells(hc_id):
    fn = HC_SANITY_DIR / f'sub-{hc_id}_V4_2component.json'
    d = json.load(open(fn))
    out = []
    for c in d['landscape']:
        bs, bc = c['params']
        out.append({
            'bs': float(bs),
            'bc': float(bc),
            'vuln_sim': np.asarray(c['vuln_sim'], dtype=float),
        })
    return out


def find_cell(cells, bs, bc, tol=1e-6):
    for c in cells:
        if abs(c['bs'] - bs) < tol and abs(c['bc'] - bc) < tol:
            return c
    return None


def compute_landscape_L(cells, vuln_obs):
    """Return list of dicts {bs, bc, L_combined, l_ccc, l_topk, l_smooth, ccc}."""
    out = []
    for c in cells:
        L, l_ccc, lt, ls, ccc = L_combined(c['vuln_sim'], vuln_obs, c['bs'], c['bc'])
        out.append({
            'bs': c['bs'], 'bc': c['bc'],
            'L_combined': L,
            'l_ccc': l_ccc, 'l_topk': lt, 'l_smooth': ls, 'ccc': ccc,
        })
    return out


# ----- main ------------------------------------------------------------------

def main():
    print(f'OUTDIR: {OUT}')
    print(f'Loss: L = 1·L_ccc + {LAMBDA_TOPK}·l_topk + 0.1·L_smooth')
    print(f'L_smooth = (bs² + bc²)/{TIKH_NORM:.0f}   (recomputed for both HC and CVD)')
    print()

    # Per-subject Δ_L records
    per_subj_rows = []
    hc_argmin_deltaL = {}
    cvd_argmin_deltaL = {}
    hc_landscapes = {}   # for candidate lookup
    cvd_landscapes = {}

    # --- HC ---
    for hc_id in HC_SUBJECTS:
        print(f'=== HC sub-{hc_id} V4 ===')
        cells = load_hc_cells(hc_id)
        try:
            vuln_obs = np.asarray(load_cvd_loco_target(hc_id, 'V4'), dtype=float)
        except Exception as e:
            print(f'  WARN failed to load vuln_obs for HC sub-{hc_id}: {e}')
            continue
        ls = compute_landscape_L(cells, vuln_obs)
        # argmin
        argmin_cell = min(ls, key=lambda r: r['L_combined'])
        # baseline (0,0)
        baseline_cell = next((r for r in ls if abs(r['bs']) < 1e-6 and abs(r['bc']) < 1e-6), None)
        assert baseline_cell is not None, f'no (0,0) in HC sub-{hc_id}'
        delta_L = baseline_cell['L_combined'] - argmin_cell['L_combined']
        print(f'  L_baseline={baseline_cell["L_combined"]:.4f}  '
              f'argmin=({argmin_cell["bs"]:.0f},{argmin_cell["bc"]:+.0f}) '
              f'L_min={argmin_cell["L_combined"]:.4f}  Δ_L={delta_L:.4f}')
        hc_argmin_deltaL[hc_id] = delta_L
        hc_landscapes[hc_id] = (ls, vuln_obs)
        per_subj_rows.append({
            'subject': f'sub-{hc_id}',
            'role': 'HC',
            'bs_argmin': argmin_cell['bs'],
            'bc_argmin': argmin_cell['bc'],
            'L_baseline': baseline_cell['L_combined'],
            'L_min': argmin_cell['L_combined'],
            'delta_L': delta_L,
        })

    # --- CVD ---
    for sid, cvd_type in CVD_SUBJECTS:
        print(f'=== CVD sub-{sid} {cvd_type} V4 ===')
        cells = load_cvd_cells(sid)
        vuln_obs = np.asarray(load_cvd_loco_target(sid, 'V4'), dtype=float)
        ls = compute_landscape_L(cells, vuln_obs)
        argmin_cell = min(ls, key=lambda r: r['L_combined'])
        baseline_cell = next((r for r in ls if abs(r['bs']) < 1e-6 and abs(r['bc']) < 1e-6), None)
        assert baseline_cell is not None, f'no (0,0) in CVD sub-{sid}'
        delta_L = baseline_cell['L_combined'] - argmin_cell['L_combined']
        print(f'  L_baseline={baseline_cell["L_combined"]:.4f}  '
              f'argmin=({argmin_cell["bs"]:.0f},{argmin_cell["bc"]:+.0f}) '
              f'L_min={argmin_cell["L_combined"]:.4f}  Δ_L={delta_L:.4f}')
        cvd_argmin_deltaL[sid] = delta_L
        cvd_landscapes[sid] = (ls, vuln_obs, baseline_cell)
        per_subj_rows.append({
            'subject': f'sub-{sid}',
            'role': f'CVD ({cvd_type})',
            'bs_argmin': argmin_cell['bs'],
            'bc_argmin': argmin_cell['bc'],
            'L_baseline': baseline_cell['L_combined'],
            'L_min': argmin_cell['L_combined'],
            'delta_L': delta_L,
        })

    # save per-subject CSV
    csv1 = OUT / 'delta_L_per_subject.csv'
    with open(csv1, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['subject', 'role', 'bs_argmin', 'bc_argmin',
                    'L_baseline', 'L_min', 'delta_L'])
        for r in per_subj_rows:
            w.writerow([r['subject'], r['role'],
                        round(r['bs_argmin'], 1), round(r['bc_argmin'], 1),
                        round(r['L_baseline'], 4),
                        round(r['L_min'], 4),
                        round(r['delta_L'], 4)])
    print(f'Wrote {csv1}')

    # --- Bootstrap HC Δ_L (argmin-based) ---
    hc_dL = np.array([hc_argmin_deltaL[h] for h in HC_SUBJECTS])
    print(f'\n=== HC Δ_L (argmin) ===')
    print(f'  values: {hc_dL.round(4).tolist()}')
    print(f'  mean={hc_dL.mean():.4f}  std={hc_dL.std(ddof=1):.4f}  '
          f'range [{hc_dL.min():.4f}, {hc_dL.max():.4f}]')

    rng = np.random.default_rng(RNG_SEED)
    boot_means = rng.choice(hc_dL, size=(N_BOOT, len(hc_dL)), replace=True).mean(axis=1)
    ci_lo, ci_hi = np.percentile(boot_means, [2.5, 97.5])
    print(f'  bootstrap mean Δ_L 95% CI: [{ci_lo:.4f}, {ci_hi:.4f}]')

    # --- Candidate specificity table ---
    # candidates: (name, sid, bs, bc)
    # For each, evaluate L_combined under V4-CCC + l_topk loss using the subject's
    # OWN vuln_obs, then Δ_L_candidate = L_baseline - L_at_candidate.
    # boot_frac = P(HC bootstrap mean Δ_L < CVD candidate Δ_L) — i.e. the CVD
    # filter must produce an improvement larger than HC's BEST-possible improvement
    # (conservative bar).
    candidates = [
        # (label, sid, bs, bc, note)
        ('BEST V4-CCC+l_topk', '08', 44, 28, 'argmin of subject under primary loss'),
        ('BEST V4-CCC+l_topk', '09', 30, 46, 'argmin of subject under primary loss'),
        ('V4-CCC alone argmin', '08', 16, 40, 'V4-CCC alone (λ_topk=0)'),
        ('V4-CCC alone argmin', '09', 30, 46, 'V4-CCC alone (λ_topk=0)'),
        ('Phase A LOCO canonical', '08', 38, -14, '§3 canonical, behav-PASS for sub-08'),
        ('Phase A LOCO canonical', '09', 6, -22, 'Phase A LOCO V4 2-component'),
        ('Tier 2 V4-CCC+SRM RDM', '08', 50, 24, 'Tier 2 argmin (V4-CCC+SRM RDM)'),
        ('Tier 2 V4-CCC+SRM RDM', '09', 34, 44, 'Tier 2 argmin (V4-CCC+SRM RDM)'),
        ('Cycle 14 cross-ROI',  '08', 58, -36,
         'OUT OF GRID (bs∈[0,50]); using nearest (50,-36) as proxy'),
        ('Cycle 14 cross-ROI',  '09', 32, 22, 'cycle 14 cross-ROI RDM'),
    ]

    spec_rows = []
    for label, sid, bs_target, bc_target, note in candidates:
        ls, vuln_obs, baseline_cell = cvd_landscapes[sid]
        # in-grid handling
        bs_eff, bc_eff, used_proxy = bs_target, bc_target, False
        # CVD V4-CCC grid bs∈[0,50] step 2; bc∈[-50,50] step 2
        if bs_target > 50.0:
            bs_eff = 50.0
            used_proxy = True
        if bs_target < 0.0:
            bs_eff = 0.0
            used_proxy = True
        # snap to grid
        cell = find_cell([{'bs': r['bs'], 'bc': r['bc'], 'L_combined': r['L_combined']}
                          for r in ls], bs_eff, bc_eff)
        if cell is None:
            print(f'  WARN candidate ({bs_eff},{bc_eff}) not found in grid for sub-{sid}; skipping')
            continue
        # candidate L is the L_combined at (bs_eff, bc_eff)
        cand_row = next(r for r in ls if abs(r['bs']-bs_eff)<1e-6 and abs(r['bc']-bc_eff)<1e-6)
        delta_L_cand = baseline_cell['L_combined'] - cand_row['L_combined']
        boot_frac = float((boot_means < delta_L_cand).mean())
        if boot_frac >= 0.975:
            verdict = '✓✓ both sig'
        elif boot_frac >= 0.90:
            verdict = '~~ marginal'
        else:
            verdict = '✗ inside HC CI'
        spec_rows.append({
            'filter': label,
            'subject': f'sub-{sid}',
            'bs_requested': bs_target, 'bc_requested': bc_target,
            'bs_used': bs_eff, 'bc_used': bc_eff,
            'L_baseline': baseline_cell['L_combined'],
            'L_at_candidate': cand_row['L_combined'],
            'delta_L_cand': delta_L_cand,
            'boot_frac': boot_frac, 'verdict': verdict,
            'used_proxy': used_proxy, 'note': note,
        })
        proxy_tag = ' [PROXY]' if used_proxy else ''
        print(f'  {label:28s} sub-{sid} β=({bs_target:+.0f},{bc_target:+.0f})'
              f'{proxy_tag}  Δ_L={delta_L_cand:+.4f}  boot_frac={boot_frac:.4f}  {verdict}')

    csv2 = OUT / 'delta_L_specificity.csv'
    with open(csv2, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['filter', 'subject', 'bs_requested', 'bc_requested',
                    'bs_used', 'bc_used',
                    'L_baseline', 'L_at_candidate', 'delta_L_cand',
                    'hc_mean_dL', 'hc_std_dL', 'boot_frac', 'verdict',
                    'used_proxy', 'note'])
        for r in spec_rows:
            w.writerow([r['filter'], r['subject'],
                        r['bs_requested'], r['bc_requested'],
                        r['bs_used'], r['bc_used'],
                        round(r['L_baseline'], 4),
                        round(r['L_at_candidate'], 4),
                        round(r['delta_L_cand'], 4),
                        round(float(hc_dL.mean()), 4),
                        round(float(hc_dL.std(ddof=1)), 4),
                        round(r['boot_frac'], 4),
                        r['verdict'], r['used_proxy'], r['note']])
    print(f'Wrote {csv2}')

    # --- Distribution figure ---
    fig, ax = plt.subplots(figsize=(7.5, 4.5), dpi=150)
    ax.hist(boot_means, bins=60, color='#7a7a7a', alpha=0.55,
            edgecolor='white', linewidth=0.4,
            label=f'HC bootstrap mean Δ_L (n={N_BOOT})')
    ax.axvline(hc_dL.mean(), color='black', lw=1.2, linestyle='--',
               label=f'HC mean Δ_L = {hc_dL.mean():.3f}')
    ax.axvline(ci_lo, color='gray', lw=0.8, linestyle=':',
               label=f'HC bootstrap 95% CI [{ci_lo:.3f}, {ci_hi:.3f}]')
    ax.axvline(ci_hi, color='gray', lw=0.8, linestyle=':')

    # per-HC argmin Δ_L tick marks
    for h, dL in zip(HC_SUBJECTS, hc_dL):
        ax.axvline(dL, color='#bbbbbb', lw=0.7, alpha=0.7)
        ax.text(dL, ax.get_ylim()[1]*0.92, f'HC{h}',
                fontsize=6, ha='center', color='#666666', rotation=90)

    cvd_colors = {'08': '#E07B2C', '09': '#2D8E8B'}
    for sid in ['08', '09']:
        dL = cvd_argmin_deltaL[sid]
        ax.axvline(dL, color=cvd_colors[sid], lw=2.0,
                   label=f'sub-{sid} argmin Δ_L = {dL:.3f}')

    ax.set_xlabel('Δ_L = L(0,0) − L(argmin)')
    ax.set_ylabel('bootstrap count')
    ax.set_title('HC Δ_L bootstrap distribution vs CVD argmin Δ_L\n'
                 'Loss = 1·L_ccc + 0.5·l_topk(K=3) + 0.1·L_smooth (wretrained, V4)',
                 fontsize=10)
    ax.legend(fontsize=7, loc='upper right')
    plt.tight_layout()
    fig_path = OUT / 'delta_L_distribution.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.savefig(str(fig_path).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close(fig)
    print(f'Wrote {fig_path}')

    # --- Summary markdown (Korean narrative) ---
    md = []
    md.append('# Δ_L specificity — V4-CCC + l_topk (descriptive diagnostic)')
    md.append('')
    md.append(f'**Loss**: `L = 1·L_ccc + {LAMBDA_TOPK}·l_topk(V4, K={K_TOPK}) + 0.1·L_smooth`  ')
    md.append(f'**L_smooth normalization**: `(β_s² + β_c²) / {TIKH_NORM:.0f}` '
              '(HC sanity의 cached `l_smooth`는 ~0.5008 factor 차이 — 양쪽을 '
              '같은 공식으로 재계산함)  ')
    md.append('**Simulator**: wretrained (vuln_sim cached per cell, 재시뮬레이션 없음)  ')
    md.append('**HC pool**: sub-01..06 (sub-07 V4 16 voxels → nan 위험으로 제외)  ')
    md.append('')
    md.append('## 1. 정의')
    md.append('')
    md.append('`Δ_L = L(β_s=0, β_c=0) − L(argmin)` — fitting이 baseline 대비')
    md.append('얼마나 loss를 줄였는지. norm metric (parameter magnitude)이 random walk')
    md.append('편향에 취약했던 한계를 보완하기 위한 보조 지표.')
    md.append('')
    md.append('**§0 compliance**: 이 metric은 *descriptive diagnostic*이며,')
    md.append('selection criterion이나 새 specificity claim의 근거가 아니다.')
    md.append('HC FPR 100% (`hc_specificity/`)와 baseline_ρ confound (Cycle 13)는')
    md.append('measurement family 한계로 확정되어 있다.')
    md.append('')
    md.append('## 2. 피험자별 Δ_L (argmin 기준)')
    md.append('')
    md.append('| subject | role | argmin (β_s, β_c) | L_baseline | L_min | Δ_L |')
    md.append('|---|---|---|---|---|---|')
    for r in per_subj_rows:
        md.append(f"| {r['subject']} | {r['role']} | "
                  f"({r['bs_argmin']:.0f}, {r['bc_argmin']:+.0f}) | "
                  f"{r['L_baseline']:.4f} | {r['L_min']:.4f} | "
                  f"**{r['delta_L']:.4f}** |")
    md.append('')
    md.append(f'**HC Δ_L 분포 (n=6, argmin)**: '
              f'mean={hc_dL.mean():.4f}, std={hc_dL.std(ddof=1):.4f}, '
              f'range [{hc_dL.min():.4f}, {hc_dL.max():.4f}]  ')
    md.append(f'**HC bootstrap mean Δ_L 95% CI** (n_boot={N_BOOT}): '
              f'[{ci_lo:.4f}, {ci_hi:.4f}]  ')
    md.append('')
    md.append(f'**CVD argmin Δ_L**:')
    for sid in ['08', '09']:
        md.append(f'- sub-{sid}: Δ_L = {cvd_argmin_deltaL[sid]:.4f}')
    md.append('')
    md.append('## 3. Candidate filter Δ_L vs HC bootstrap')
    md.append('')
    md.append('Δ_L_candidate = L_baseline − L(β_s, β_c). boot_frac = '
              'P(HC bootstrap mean Δ_L < CVD candidate Δ_L), CVD가 HC의 '
              'best-possible improvement 분포를 얼마나 초과하는지 (conservative bar).')
    md.append('')
    md.append('| Filter | subject | β=(β_s, β_c) | Δ_L_cand | boot_frac | Verdict | note |')
    md.append('|---|---|---|---|---|---|---|')
    for r in spec_rows:
        beta_str = f"({r['bs_requested']:+.0f}, {r['bc_requested']:+.0f})"
        if r['used_proxy']:
            beta_str += f" → ({r['bs_used']:+.0f}, {r['bc_used']:+.0f}) [PROXY]"
        md.append(f"| {r['filter']} | {r['subject']} | {beta_str} | "
                  f"{r['delta_L_cand']:+.4f} | {r['boot_frac']:.4f} | "
                  f"{r['verdict']} | {r['note']} |")
    md.append('')
    md.append('## 4. 해석')
    md.append('')
    # Generate descriptive interpretation
    sub08_argmin_dL = cvd_argmin_deltaL['08']
    sub09_argmin_dL = cvd_argmin_deltaL['09']
    sub08_frac_argmin = float((boot_means < sub08_argmin_dL).mean())
    sub09_frac_argmin = float((boot_means < sub09_argmin_dL).mean())
    hc_max = float(hc_dL.max())

    md.append(f'- **sub-08 (deutan) argmin Δ_L = {sub08_argmin_dL:.4f}** vs HC range '
              f'[{hc_dL.min():.4f}, {hc_dL.max():.4f}]. '
              f'boot_frac vs HC bootstrap mean = {sub08_frac_argmin:.4f}.')
    md.append(f'- **sub-09 (protan) argmin Δ_L = {sub09_argmin_dL:.4f}** vs HC range '
              f'[{hc_dL.min():.4f}, {hc_dL.max():.4f}]. '
              f'boot_frac vs HC bootstrap mean = {sub09_frac_argmin:.4f}.')
    md.append('')

    # Δ_L vs norm metric discussion
    md.append('### 4-1. Δ_L vs norm metric — 어느 쪽이 더 분리적인가?')
    md.append('')
    md.append('이전 norm metric (`hc_specificity.csv`)에서는 BEST 후보들이 모두 '
              '`boot_frac < 0.90`으로 HC CI 내부에 묶였다. Δ_L metric에서는:')
    if sub08_frac_argmin >= 0.90 and sub09_frac_argmin >= 0.90:
        md.append('- **양 CVD 모두 boot_frac ≥ 0.90** — Δ_L이 norm 대비 더 분리적.')
    elif sub08_frac_argmin >= 0.90 or sub09_frac_argmin >= 0.90:
        md.append('- **한 피험자만 boot_frac ≥ 0.90** — '
                  'Δ_L도 부분적 개선에 그침. 피험자별 신호 차이 반영.')
    else:
        md.append('- **양 CVD 모두 boot_frac < 0.90** — Δ_L 역시 HC와 분리에 실패. '
                  '두 metric의 한계는 동일 원인(HC random walk가 V4-CCC + l_topk '
                  '공간의 1326 cell 중 어디든 떨어질 수 있음) 때문일 가능성.')
    md.append('')

    # Per-subject recommendation
    md.append('### 4-2. 피험자별 후보 비교')
    md.append('')
    for sid in ['08', '09']:
        subj_rows = [r for r in spec_rows if r['subject'] == f'sub-{sid}']
        subj_rows = sorted(subj_rows, key=lambda r: -r['delta_L_cand'])
        md.append(f'**sub-{sid}** (Δ_L 큰 순):')
        for r in subj_rows:
            beta_str = f"({r['bs_requested']:+.0f}, {r['bc_requested']:+.0f})"
            md.append(f'- `{r["filter"]}` β={beta_str}: Δ_L={r["delta_L_cand"]:+.4f}, '
                      f'boot_frac={r["boot_frac"]:.4f}, {r["verdict"]}')
        md.append('')

    md.append('### 4-3. 행동 검증 권고 (descriptive)')
    md.append('')
    md.append('§0에 따라 Δ_L은 model class / filter selection을 결정하지 않는다. '
              '아래는 *descriptive* 해석으로, ground truth는 행동 검증이다 (§A4, §A9).')
    md.append('')
    # rank candidates per subject
    for sid in ['08', '09']:
        subj_rows = [r for r in spec_rows if r['subject'] == f'sub-{sid}']
        top = max(subj_rows, key=lambda r: r['delta_L_cand'])
        cvd_type = 'deutan' if sid == '08' else 'protan'
        md.append(f'- **sub-{sid} ({cvd_type})**: Δ_L 상위 후보는 '
                  f'`{top["filter"]}` β=({top["bs_requested"]:+.0f}, '
                  f'{top["bc_requested"]:+.0f})  '
                  f'(Δ_L={top["delta_L_cand"]:+.4f}, boot_frac={top["boot_frac"]:.4f}).')
    md.append('')
    md.append('## 5. Files')
    md.append('')
    md.append('- `delta_L_per_subject.csv` — 8 피험자(HC 6 + CVD 2) argmin Δ_L 원자료')
    md.append('- `delta_L_specificity.csv` — candidate filter별 Δ_L_cand + boot_frac')
    md.append('- `delta_L_distribution.png/.pdf` — HC bootstrap 분포 + CVD 수직선')
    md.append('- 본 문서')
    md.append('')
    md.append('## 6. Caveats')
    md.append('')
    md.append('- **L_smooth normalization 통일**: HC sanity landscape의 cached '
              '`l_smooth`는 사용하지 않고 `(β_s² + β_c²)/32400`로 양쪽 재계산. '
              'cached 값은 ~0.5008 factor 차이로 두 그룹 간 비교가 비뚤어졌었음.')
    md.append('- **Out-of-grid candidate**: Cycle 14 sub-08 (58, -36)은 V4-CCC '
              '그리드 (bs∈[0,50]) 밖. 가장 가까운 그리드점 (50, -36)을 proxy로 사용.')
    md.append('- **Discrete top-K**: l_topk Jaccard는 K=3에서 4개의 이산값만 가짐. '
              'HC도 1326 cell 중 어디선가 우연히 top-3을 맞출 수 있어 random-walk '
              'sensitivity가 norm metric과 유사할 가능성.')
    md.append('- **HC pool n=6**: bootstrap CI는 작은 표본으로 wide. '
              'sub-04 outlier 효과는 6×6 resample에서 평탄화됨.')
    md.append('')
    (OUT / 'delta_L_specificity_summary.md').write_text('\n'.join(md))
    print(f'Wrote {OUT / "delta_L_specificity_summary.md"}')


if __name__ == '__main__':
    main()
