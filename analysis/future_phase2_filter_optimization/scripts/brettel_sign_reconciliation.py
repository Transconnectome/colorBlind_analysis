"""brettel_sign_reconciliation.py — Brettel β_c 부호 규약별 재계산.

분석 대상:
  Forward model:   δθ = β_s·cos(θ - 90°) + β_c·cos(θ - θ_conf)
  Three axis conventions:
    - OLD:    θ_conf = 150° for BOTH families
    - Stockman: θ_conf = 16° (protan), 163° (deutan)
    - CIELab: θ_conf = 11.8° (protan), 175.7° (deutan)

Key insight:
  Stockman 16° vs 163°는 167° 떨어진 거의 antipodal pair.
  cos(θ - 16°) = cos(θ - 196°) ≈ -cos(θ - 16°+180°) = -cos(θ - 196°)
  but |163 - 196| = 33° → not strictly antipodal.

  CIELab 11.8° vs 175.7°: 163.9° 떨어짐 → 정확히 ~180° antipodal에 더 가까움.

V1 ΔRDM bootstrap β_c (OLD axis 150° 기반):
  sub-08 deutan: β_c = -18° ± 6° [CI excl 0]
  sub-09 protan: β_c = +3° ± 2° [CI incl 0]

이 부호를 새 axis convention에서 어떻게 해석하는가?
"""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path

_THIS = Path(__file__).resolve().parent
OUT = _THIS.parent / 'results' / 'brettel_reconciliation'
OUT.mkdir(parents=True, exist_ok=True)

HUE_8 = np.array([0, 45, 90, 135, 180, 225, 270, 315])

AXES = {
    'OLD (150° both)':      {'protan': 150.0, 'deutan': 150.0},
    'Stockman 16/163':      {'protan':  16.0, 'deutan': 163.0},
    'CIELab 11.8/175.7':    {'protan':  11.8, 'deutan': 175.7},
}

V1_DRDM_BETA_C_OLD = {
    'sub-08': {'family': 'deutan', 'bc': -18.0, 'ci_low': -32.0, 'ci_high': -11.0,
               'excludes_zero': True},
    'sub-09': {'family': 'protan', 'bc':  +3.0, 'ci_low':  -2.0, 'ci_high':  +6.0,
               'excludes_zero': False},
}


def project_bc(bc_old, axis_old, axis_new):
    """β_c·cos(θ - axis_old) → equivalent (β_c', ..) representation under axis_new.

    Use least-squares projection: find β_c' s.t.
        β_c'·cos(θ - axis_new) ≈ β_c·cos(θ - axis_old)  over all θ
    """
    theta = HUE_8
    target = bc_old * np.cos(np.radians(theta - axis_old))
    basis = np.cos(np.radians(theta - axis_new))
    # Best fit: bc' = <target, basis> / <basis, basis>
    bc_new = np.dot(target, basis) / np.dot(basis, basis)
    # Residual energy
    res = target - bc_new * basis
    res_norm = np.linalg.norm(res) / np.linalg.norm(target) if np.linalg.norm(target) > 1e-9 else 0
    return bc_new, res_norm


def brettel_expected_sign(family, axis_conf, axis_old=150.0):
    """OLD convention: deutan +, protan - (memory).
    Under new axis, expected sign rotates by the cos sign difference.

    If both axes are within 90° of each other, expected sign STAYS.
    If they differ by ~180°, expected sign FLIPS.
    """
    sign_old = +1 if family == 'deutan' else -1
    # Sign of cos(axis_new - axis_old) determines whether sign flips
    cos_align = np.cos(np.radians(axis_conf - axis_old))
    # If cos_align > 0: same direction, sign STAYS
    # If cos_align < 0: opposite direction, sign FLIPS
    sign_new = sign_old * (1 if cos_align > 0 else -1)
    return sign_new, float(cos_align)


def main():
    print('=' * 90)
    print('Brettel β_c sign reconciliation across axis conventions')
    print('=' * 90)
    print('\nV1 ΔRDM bootstrap β_c (under OLD 150° axis):')
    for sid, d in V1_DRDM_BETA_C_OLD.items():
        ci_marker = '★ excludes 0' if d['excludes_zero'] else '  includes 0'
        print(f'  {sid} {d["family"]:7s}  β_c = {d["bc"]:+5.1f}° '
              f'CI [{d["ci_low"]:+5.1f}, {d["ci_high"]:+5.1f}]  {ci_marker}')

    out = {}
    for axis_name, axes in AXES.items():
        print(f'\n{"="*90}\nAxis convention: {axis_name}\n{"="*90}')
        out[axis_name] = {}
        for sid, d in V1_DRDM_BETA_C_OLD.items():
            fam = d['family']
            axis_new = axes[fam]
            bc_old = d['bc']
            # Project β_c from OLD axis to new axis
            bc_new, res_norm = project_bc(bc_old, 150.0, axis_new)
            # Expected sign under Brettel
            sign_exp, cos_align = brettel_expected_sign(fam, axis_new)
            # Observed sign under new axis
            sign_obs = +1 if bc_new > 0 else (-1 if bc_new < 0 else 0)
            agree = (sign_obs == sign_exp) if d['excludes_zero'] else None
            agree_str = ('✓ AGREE' if agree else '✗ DISAGREE') if agree is not None else '~ CI includes 0'

            print(f'  {sid} {fam:7s}  axis: 150° → {axis_new:6.1f}°  '
                  f'β_c: {bc_old:+5.1f}° → {bc_new:+5.1f}°  '
                  f'expected sign: {sign_exp:+d}  agreement: {agree_str}')
            print(f'    cos(axis_new - 150°)={cos_align:+.3f}, projection residual={res_norm:.2f}')

            out[axis_name][sid] = {
                'family': fam, 'axis_old': 150.0, 'axis_new': axis_new,
                'bc_old': bc_old, 'bc_new': bc_new,
                'expected_sign': sign_exp, 'observed_sign': sign_obs,
                'agreement': agree, 'cos_align': cos_align,
                'projection_residual': res_norm,
            }

    print(f'\n{"="*90}\n해석 요약\n{"="*90}')
    print("""
  - Stockman 163° (deutan)는 OLD 150°에 가까움 (cos(13°)=+0.97 → 부호 STAY)
    Stockman 16° (protan)는 OLD 150°와 ~134° 차이 (cos(-134°)=-0.69 → 부호 FLIP)
  - CIELab 175.7° (deutan)는 OLD 150°와 25.7° (cos=+0.90 → 부호 STAY)
    CIELab 11.8° (protan)는 OLD 150°와 138° (cos=-0.74 → 부호 FLIP)

  V1 ΔRDM 데이터 해석:
  - sub-08 deutan β_c=-18° (excl 0): OLD 규약 expected +, OBSERVED - → DISAGREE
    Stockman/CIELab 규약에서도 deutan은 부호 STAY → 여전히 DISAGREE
  - sub-09 protan β_c=+3° (incl 0): OLD 규약 expected -, OBSERVED ~0
    Stockman/CIELab 규약에서 protan은 부호 FLIP → expected +, OBSERVED ~0 (marginal AGREE)

  결론:
  - V1 ΔRDM β_c는 sub-08 deutan에서 어떤 axis 규약 하에서도 Brettel 예측과 DISAGREE
  - V1 ΔRDM β_c는 sub-09 protan에서 marginal (CI includes 0)
  - "Brettel sign 강력 복원" 주장은 ★★★ → ★~★★ (검증중)으로 격하 필요
""")

    with open(OUT / 'brettel_reconciliation.json', 'w') as f:
        json.dump(out, f, indent=2)
    print(f'Wrote {OUT / "brettel_reconciliation.json"}')


if __name__ == '__main__':
    main()
