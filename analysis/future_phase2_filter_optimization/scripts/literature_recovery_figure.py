"""literature_recovery_figure.py — Neural recovery of literature anchors + tier classification.

기존 neural fits (Phase 2 cone-shift v2, 2-component bootstrap, R+C)에서
literature anchors (Emery, Machado, Brettel, Tregillus)가 얼마나 recover되는지 시각화.

**Tier classification** (2026-05-13 추가):
  - Emery       = ★★★  ESSENTIAL  (both subjects strong recovery, β_s anchor)
  - Machado     = ★★★  ESSENTIAL  (severity classification matches, axis grounding)
  - Tregillus   = ★★   ESSENTIAL  (β_c amplitude anchor — simplification sweep 확인,
                                   제거 시 sub-08 P2a −0.088, sub-09 P2a −0.100)
  - Brettel     = ★    UNDER VERIFICATION  (sub-08 deutan β_c=-18° DISAGREES with Brettel
                                            under all axis conventions — see reconciliation)

Output:
  results/literature_recovery/
    fig_literature_recovery_combined.{png,pdf}
    recovery_table.md
    recovery_data.json
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent.parent / 'results' / 'literature_recovery'
OUT.mkdir(parents=True, exist_ok=True)

TIER_COLORS = {
    'ESSENTIAL_3': '#1B7C3D',  # ★★★ green
    'ESSENTIAL_2': '#5DA34D',  # ★★ light green
    'UNDER_VERIF': '#D9831A',  # ★  orange (검증중)
}

NEURAL_RECOVERY = {
    'emery_bs': {
        'tier': '★★★ ESSENTIAL',
        'tier_color': TIER_COLORS['ESSENTIAL_3'],
        'rationale': 'β_s 21.4° anchor — V1 ΔRDM β_s 20°/23° 양 피험자 독립 복원',
        'literature': {'name': 'Emery 2021', 'value': 21.4, 'ci_low': 17.0, 'ci_high': 25.8,
                       'desc': 'AT group mean β_s (B-Y rotation toward S-axis)'},
        'sub-08': {'value': 20.0, 'ci_low': 12.0, 'ci_high': 39.0, 'sd': 8.0,
                   'source': 'V1 ΔRDM bootstrap (2-component)',
                   'family': 'deutan', 'color': '#E07B2C'},
        'sub-09': {'value': 23.0, 'ci_low': 2.0, 'ci_high': 36.0, 'sd': 10.0,
                   'source': 'V1 ΔRDM bootstrap (2-component)',
                   'family': 'protan', 'color': '#2D8E8B'},
    },
    'machado_dlambda': {
        'tier': '★★★ ESSENTIAL',
        'tier_color': TIER_COLORS['ESSENTIAL_3'],
        'rationale': 'Δλ severity — Phase 2 cone-shift v2 sub-08 mild / sub-09 severe 둘 다 p<0.05',
        'literature': {'name': 'Machado 2009',
                       'mild_low': 5.0, 'mild_high': 10.0,
                       'moderate_low': 10.0, 'moderate_high': 18.0,
                       'severe_low': 18.0, 'severe_high': 25.0,
                       'desc': 'Severity classification (anomaloscope-typed)'},
        'sub-08': {'value': 8.64, 'p': 0.036,
                   'source': 'Phase 2 cone-shift v2 (shift_at_both, V4)',
                   'classification': 'mild',
                   'family': 'deutan', 'color': '#E07B2C'},
        'sub-09': {'value': 25.20, 'p': 0.009,
                   'source': 'Phase 2 cone-shift v2 (shift_at_both, V4)',
                   'classification': 'severe',
                   'family': 'protan', 'color': '#2D8E8B'},
        'sub-10': {'value': 43.76, 'p': 0.561,
                   'source': 'null control (near-normal)',
                   'classification': 'NS (correct null)',
                   'family': 'normal', 'color': '#888888'},
    },
    'tregillus_overshoot': {
        'tier': '★★ ESSENTIAL (revised)',
        'tier_color': TIER_COLORS['ESSENTIAL_2'],
        'rationale': '제거 시 β_c→0 collapse, BEST P2a 감소 (sub-08: -0.088, sub-09: -0.100). '
                     'simplification_sweep으로 확인 (2026-05-13)',
        'literature': {'name': 'Tregillus 2021',
                       'range_low': 20.0, 'range_high': 40.0,
                       'desc': 'Suprathreshold compensation overshoot %'},
        'sub-08': {'g': -2.25, 'overshoot_pct': 125,
                   'source': 'R+C model',
                   'note': 'non-physiological outlier (cortical model 한계)',
                   'family': 'deutan', 'color': '#E07B2C'},
        'sub-09': {'g': -1.10, 'overshoot_pct': 10,
                   'source': 'R+C model',
                   'note': 'partial recovery (lower bound)',
                   'family': 'protan', 'color': '#2D8E8B'},
    },
    'brettel_sign': {
        'tier': '★ UNDER VERIFICATION',
        'tier_color': TIER_COLORS['UNDER_VERIF'],
        'rationale': 'sub-08 deutan β_c=−18° (CI excl 0) — OLD/Stockman/CIELab 모든 axis '
                     '규약에서 Brettel expected sign과 DISAGREE. sub-09 protan β_c=+3° CI '
                     'incl 0 (marginal). brettel_reconciliation.json 참조',
        'literature': {'name': 'Brettel 1997',
                       'deutan_expected_old': '+ (β_c>0)',
                       'protan_expected_old': '− (β_c<0)',
                       'desc': 'Confusion-axis sign per family — depends on axis convention'},
        'sub-08': {'value': -18.0, 'ci_low': -32.0, 'ci_high': -11.0,
                   'consistent_old_axis': False,
                   'consistent_stockman': False,
                   'consistent_cielab': False,
                   'source': 'V1 ΔRDM bootstrap (2-component)',
                   'family': 'deutan', 'color': '#E07B2C'},
        'sub-09': {'value': 3.0, 'ci_low': -2.0, 'ci_high': 6.0,
                   'consistent_old_axis': None,
                   'consistent_stockman': None,
                   'consistent_cielab': None,
                   'note': 'CI includes 0 → cannot assess sign',
                   'source': 'V1 ΔRDM bootstrap (2-component)',
                   'family': 'protan', 'color': '#2D8E8B'},
    },
}


def _tier_badge(ax, tier, color, x=0.98, y=0.98):
    ax.text(x, y, tier, transform=ax.transAxes, fontsize=10, fontweight='bold',
            ha='right', va='top',
            bbox=dict(boxstyle='round,pad=0.4', facecolor=color, alpha=0.85,
                      edgecolor='black', linewidth=1.0),
            color='white')


def fig_emery_bs(ax):
    d = NEURAL_RECOVERY['emery_bs']
    emery = d['literature']
    ax.axvspan(emery['ci_low'], emery['ci_high'], alpha=0.20, color='#FFD700',
               label=f'Emery 2021 AT mean ±SD ({emery["value"]}°)')
    ax.axvline(emery['value'], color='#FFA500', lw=2, ls='--')
    for i, sid in enumerate(['sub-08', 'sub-09']):
        s = d[sid]
        y = i + 0.5
        ax.errorbar(s['value'], y,
                    xerr=[[s['value']-s['ci_low']], [s['ci_high']-s['value']]],
                    fmt='o', color=s['color'], ms=12, capsize=6, lw=2,
                    label=f'{sid} ({s["family"]}): {s["value"]}° ±{s["sd"]}°')
    ax.set_ylim(0, 2)
    ax.set_yticks([0.5, 1.5])
    ax.set_yticklabels(['sub-08\n(deutan)', 'sub-09\n(protan)'])
    ax.set_xlabel('β_s — S-axis rotation amplitude (degrees)')
    ax.set_xlim(-5, 50)
    ax.set_title('(A) Emery 21.4° anchor — V1 ΔRDM β_s recovery',
                 fontsize=11, fontweight='bold')
    ax.legend(loc='lower right', fontsize=8)
    ax.spines[['top', 'right']].set_visible(False)
    _tier_badge(ax, d['tier'], d['tier_color'])


def fig_machado_dlambda(ax):
    d = NEURAL_RECOVERY['machado_dlambda']
    lit = d['literature']
    ax.axvspan(lit['mild_low'], lit['mild_high'], alpha=0.15, color='green',
               label=f'Machado mild ({lit["mild_low"]}-{lit["mild_high"]} nm)')
    ax.axvspan(lit['moderate_low'], lit['moderate_high'], alpha=0.15, color='orange',
               label=f'Machado moderate ({lit["moderate_low"]}-{lit["moderate_high"]} nm)')
    ax.axvspan(lit['severe_low'], lit['severe_high'], alpha=0.15, color='red',
               label=f'Machado severe ({lit["severe_low"]}-{lit["severe_high"]} nm)')
    for i, sid in enumerate(['sub-08', 'sub-09', 'sub-10']):
        if sid not in d: continue
        s = d[sid]
        y = i + 0.5
        ax.scatter(s['value'], y, color=s['color'], s=200, edgecolor='black', zorder=5,
                   label=f'{sid}: {s["value"]:.2f} nm, p={s["p"]:.3f} → {s["classification"]}')
    ax.set_ylim(0, 3)
    ax.set_yticks([0.5, 1.5, 2.5])
    ax.set_yticklabels(['sub-08\n(deutan)', 'sub-09\n(protan)', 'sub-10\n(normal)'])
    ax.set_xlabel('Δλ — cone spectral shift (nm)')
    ax.set_xlim(-2, 50)
    ax.set_title('(B) Machado severity anchor — Phase 2 cone-shift v2 Δλ recovery',
                 fontsize=11, fontweight='bold')
    ax.legend(loc='lower right', fontsize=7)
    ax.spines[['top', 'right']].set_visible(False)
    _tier_badge(ax, d['tier'], d['tier_color'])


def fig_tregillus(ax):
    d = NEURAL_RECOVERY['tregillus_overshoot']
    lit = d['literature']
    ax.axvspan(lit['range_low'], lit['range_high'], alpha=0.20, color='#9370DB',
               label=f'Tregillus 2021 range ({lit["range_low"]}-{lit["range_high"]}%)')
    for i, sid in enumerate(['sub-08', 'sub-09']):
        s = d[sid]
        y = i + 0.5
        col = s['color']
        if s['overshoot_pct'] < 0 or s['overshoot_pct'] > 60:
            col = '#888888'
        ax.scatter(s['overshoot_pct'], y, color=col, s=200, edgecolor='black', zorder=5,
                   label=f'{sid}: g={s["g"]} → {s["overshoot_pct"]}% ({s["note"]})')
    ax.set_ylim(0, 2)
    ax.set_yticks([0.5, 1.5])
    ax.set_yticklabels(['sub-08\n(deutan)', 'sub-09\n(protan)'])
    ax.set_xlabel('Overshoot (%) — R+C model g')
    ax.set_xlim(-10, 150)
    ax.set_title('(C) Tregillus 2021 anchor — R+C g overshoot',
                 fontsize=11, fontweight='bold')
    ax.legend(loc='upper right', fontsize=7)
    ax.spines[['top', 'right']].set_visible(False)
    _tier_badge(ax, d['tier'], d['tier_color'])


def fig_brettel_sign(ax):
    d = NEURAL_RECOVERY['brettel_sign']
    ax.axvline(0, color='black', lw=1.0, ls=':')
    ax.axvspan(0, 50, alpha=0.10, color='red',
               label='Brettel deutan expected (β_c>0, OLD axis)')
    ax.axvspan(-50, 0, alpha=0.10, color='blue',
               label='Brettel protan expected (β_c<0, OLD axis)')
    for i, sid in enumerate(['sub-08', 'sub-09']):
        s = d[sid]
        y = i + 0.5
        consist = s.get('consistent_old_axis')
        marker = 's' if consist is False else ('o' if consist else '^')
        ax.errorbar(s['value'], y,
                    xerr=[[s['value']-s['ci_low']], [s['ci_high']-s['value']]],
                    fmt=marker, color=s['color'], ms=12, capsize=6, lw=2,
                    label=f'{sid} ({s["family"]}): β_c={s["value"]}° CI[{s["ci_low"]},{s["ci_high"]}]')
        # mark disagreement
        if consist is False:
            ax.annotate('✗ DISAGREE', xy=(s['value'], y), xytext=(s['value']+5, y+0.15),
                        fontsize=9, color='darkred', fontweight='bold')
    ax.set_ylim(0, 2)
    ax.set_yticks([0.5, 1.5])
    ax.set_yticklabels(['sub-08\n(deutan)', 'sub-09\n(protan)'])
    ax.set_xlabel('β_c — confusion-axis amplitude (degrees, OLD axis 150°)')
    ax.set_xlim(-50, 30)
    ax.set_title('(D) Brettel 1997 anchor — V1 ΔRDM β_c sign recovery',
                 fontsize=11, fontweight='bold')
    ax.legend(loc='lower left', fontsize=8)
    ax.spines[['top', 'right']].set_visible(False)
    _tier_badge(ax, d['tier'], d['tier_color'])


def main():
    fig, axes = plt.subplots(2, 2, figsize=(15, 10), dpi=140)
    fig_emery_bs(axes[0, 0])
    fig_machado_dlambda(axes[0, 1])
    fig_tregillus(axes[1, 0])
    fig_brettel_sign(axes[1, 1])
    fig.suptitle('Neural data recovery of literature CVD predictions  '
                 '(★★★ essential / ★★ essential / ★ under verification)\n'
                 'V1 ΔRDM β_s, V4 cone-shift Δλ, R+C g, V1 ΔRDM β_c — individual subjects',
                 fontsize=12, fontweight='bold', y=0.995)
    plt.tight_layout()
    out_combined = OUT / 'fig_literature_recovery_combined.png'
    plt.savefig(out_combined, dpi=140, bbox_inches='tight')
    plt.savefig(str(out_combined).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close()
    print(f'wrote {out_combined.name}')

    with open(OUT / 'recovery_data.json', 'w') as f:
        json.dump(NEURAL_RECOVERY, f, indent=2)

    # Recovery table with tier classification
    md = []
    md.append('# Neural recovery of literature CVD predictions — Tier classification\n')

    md.append('## Tier 정의\n')
    md.append('- **★★★ ESSENTIAL**: Loss에서 제거 시 BEST 좌표 붕괴 + literature value와 신경 데이터 양 피험자 일치')
    md.append('- **★★ ESSENTIAL (revised)**: Loss 제거 시 BEST 붕괴 확인 (literature 일치는 부분)')
    md.append('- **★ UNDER VERIFICATION**: Literature value와 신경 데이터 부분 불일치, 추가 검증 필요\n')

    md.append('## Tier table\n')
    md.append('| Anchor | Tier | Rationale |')
    md.append('|---|---|---|')
    md.append('| **Emery 2021** β_s ≈ 21.4° | ★★★ ESSENTIAL | V1 ΔRDM β_s sub-08=20°/sub-09=23° 양 피험자 독립 복원 |')
    md.append('| **Machado 2009** Δλ severity | ★★★ ESSENTIAL | Phase 2 cone-shift v2 sub-08 mild (p=0.036) / sub-09 severe (p=0.009) |')
    md.append('| **Tregillus 2021** 20-40% overshoot | ★★ ESSENTIAL | Loss 제거 시 β_c→0 collapse (sub-08 P2a −0.088, sub-09 P2a −0.100). literature 일치는 sub-09 부분, sub-08 outlier |')
    md.append('| **Brettel 1997** β_c sign | ★ UNDER VERIFICATION | sub-08 β_c=−18° (CI excl 0) — OLD/Stockman/CIELab 모든 규약에서 Brettel expected sign과 DISAGREE; sub-09 CI incl 0 (assessable 안 됨) |\n')

    md.append('## Empirical recovery values\n')
    md.append('| Anchor (literature) | sub-08 deutan (neural) | sub-09 protan (neural) | Source |')
    md.append('|---|---|---|---|')
    md.append('| Emery β_s 21.4° | **20°** ±8 [12, 39] | **23°** ±10 [2, 36] | V1 ΔRDM bootstrap 2-comp |')
    md.append('| Machado severity Δλ | **8.6 nm** mild, p=0.036 | **25.2 nm** severe, p=0.009 | Phase 2 cone-shift v2 (V4) |')
    md.append('| Tregillus 20-40% | g=−2.25 → 125% (outlier) | g=−1.10 → **10%** (partial) | R+C model |')
    md.append('| Brettel β_c sign | **−18°** CI[−32, −11] (DISAGREE) | **+3°** CI[−2, +6] (NS) | V1 ΔRDM bootstrap 2-comp |\n')

    md.append('## Loss simplification finding (2026-05-13)\n')
    md.append('초기 가설("Tregillus = Emery의 중복")은 simplification sweep으로 **기각**:\n')
    md.append('| Loss variant | sub-08 (β_s, β_c) | sub-09 (β_s, β_c) | P2a (sub-08, sub-09) |')
    md.append('|---|---|---|---|')
    md.append('| FULL (Emery+Tregillus+Brettel+Tikh) | (22, +12) | (22, −10) | 0.550, 0.887 |')
    md.append('| SIMPLE (Emery+Brettel+Tikh, Tregillus 제거) | (20, **0**) | (20, **+2**) | 0.463, 0.787 |')
    md.append('| Emery only + CCC + Tikh | (20, −4) | (20, +4) | 0.425, 0.787 |\n')
    md.append('→ **Tregillus는 β_c amplitude를 유지하는 essential 항.** Emery는 β_s anchor, Tregillus는 norm anchor, 두 anchor 모두 필요.\n')

    md.append('## Brettel sign reconciliation (2026-05-13)\n')
    md.append('| Axis convention | sub-08 deutan expected | sub-08 observed β_c | sub-09 protan expected | sub-09 observed β_c |')
    md.append('|---|---|---|---|---|')
    md.append('| OLD 150° both | + (β_c>0) | −18° ✗ | − (β_c<0) | +3° (CI incl 0) |')
    md.append('| Stockman 163° / 16° | + (sign STAY) | −17.5° ✗ | + (sign FLIP) | −2.1° (CI incl 0) |')
    md.append('| CIELab 175.7° / 11.8° | + (sign STAY) | −16.2° ✗ | + (sign FLIP) | −2.2° (CI incl 0) |\n')
    md.append('→ **sub-08 deutan은 모든 axis 규약에서 Brettel 예측과 DISAGREE.** Brettel sign penalty를 loss에 포함시키는 것은 신경 데이터로 정당화되지 않음.\n')

    md.append('## Loss equations\n')
    md.append('Forward model:\n')
    md.append('```')
    md.append('δθ(θ) = β_s · cos(θ − 90°) + β_c · cos(θ − θ_conf)')
    md.append('θ_perceived = (θ + δθ(θ)) mod 360')
    md.append('```\n')
    md.append('Composite loss (current Bayesian BEST):\n')
    md.append('```')
    md.append('L_total = α · L_ccc(V4)  +  (1 − α) · L_lit  +  ε · Tikh')
    md.append('')
    md.append('  α = 0.3,  ε = 0.1 (scaled ×50 for parity with L_lit terms)')
    md.append('')
    md.append('L_ccc(V4)     = 1 − CCC(vuln_sim, vuln_cvd)         [neural likelihood]')
    md.append('                CCC = 2·ρ·σ_x·σ_y / (σ_x² + σ_y² + (μ_x − μ_y)²)')
    md.append('')
    md.append('L_lit         = w_E·L_Emery  +  w_T·L_Tregillus  +  w_B·L_Brettel')
    md.append('  w_E = 0.5,  w_T = 0.5,  w_B = 0.3')
    md.append('')
    md.append('L_Emery       = ((β_s − 21.4) / 10)²                [β_s anchor]')
    md.append('L_Tregillus   = ((√(β_s² + β_c²) − 21.4·1.3) / 15)²  [norm anchor; 1.3 = 30% overshoot]')
    md.append('L_Brettel     = max(0, −β_c · s_fam / 50)²           [sign-only penalty]')
    md.append('                s_fam = +1 (deutan), −1 (protan)  under OLD axis 150°')
    md.append('')
    md.append('Tikh          = (β_s² + β_c²) / 32400                [L2 regularizer]')
    md.append('```\n')

    md.append('## Implication for filter design\n')
    md.append('Bayesian framework uses literature anchors as prior. Neural recovery analysis:\n')
    md.append('- **★★★ Emery + ★★★ Machado**: literature priors가 신경 데이터로 독립 검증됨 → '
              '필터 파라미터의 anchor 선택을 정당화.\n')
    md.append('- **★★ Tregillus**: literature value 자체는 신경 부분 일치이나, '
              'loss에서 제거 시 β_c→0 collapse → empirically essential (정량적으로 확인됨).\n')
    md.append('- **★ Brettel**: sub-08에서 모든 axis 규약 하 DISAGREE → '
              '추가 검증 또는 alternative formulation 필요. '
              '현재는 weak weight (0.3) + Tikh로 stabilize. Loss에서 제거 가능성 검토 권고.\n')

    (OUT / 'recovery_table.md').write_text('\n'.join(md))
    print(f'wrote {OUT / "recovery_table.md"}')


if __name__ == '__main__':
    main()
