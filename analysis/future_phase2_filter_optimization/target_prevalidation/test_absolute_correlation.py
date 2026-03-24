#!/usr/bin/env python3
"""
절대값 상관 검증 — 부호 vs 크기

질문:
1. |Cone Δdist| vs |SRM z| 상관? (크기만)
2. RDM (수백 차원) vs SRM (k=3-4) 부호 일치도?
   → 차원 축소가 부호 불일치 원인인가?
"""

import numpy as np
from scipy.stats import pearsonr, spearmanr
import pandas as pd

# Data from compute_cone_opponency_corrected.py output
data = {
    'pair': [
        'red-orange', 'orange-yellow', 'yellow-green', 'green-blue',
        'yellow-purple', 'blue-purple', 'cyan-blue'
    ],
    'cone_delta': [0.026, -0.027, -0.282, 0.039, 0.138, -0.084, -0.037],
    'srm_z': [-0.82, 3.29, 4.14, -0.89, 13.87, 6.15, -0.95],
    'rdm_diff': [-0.605, 0.498, 0.496, -0.158, 0.670, 0.881, 0.452],
}

df = pd.DataFrame(data)

print("="*70)
print("절대값 상관 검증 (Deutan sub-08)")
print("="*70)

# 1. 부호 일치도
print("\n### 1. 부호 (방향) 일치도")

df['cone_sign'] = np.sign(df['cone_delta'])
df['srm_sign'] = np.sign(df['srm_z'])
df['rdm_sign'] = np.sign(df['rdm_diff'])

df['cone_srm_match'] = (df['cone_sign'] == df['srm_sign']).astype(int)
df['cone_rdm_match'] = (df['cone_sign'] == df['rdm_sign']).astype(int)
df['srm_rdm_match'] = (df['srm_sign'] == df['rdm_sign']).astype(int)

print(f"Cone vs SRM: {df['cone_srm_match'].sum()}/7 = {df['cone_srm_match'].mean()*100:.0f}%")
print(f"Cone vs RDM: {df['cone_rdm_match'].sum()}/7 = {df['cone_rdm_match'].mean()*100:.0f}%")
print(f"SRM vs RDM:  {df['srm_rdm_match'].sum()}/7 = {df['srm_rdm_match'].mean()*100:.0f}%")

print("\n부호 불일치 쌍 (Cone vs SRM):")
mismatch = df[df['cone_srm_match'] == 0]
for _, row in mismatch.iterrows():
    print(f"  {row['pair']:15s}: Cone {row['cone_delta']:+.3f} ↔ SRM {row['srm_z']:+.2f}")

# 2. 절대값 상관
print("\n### 2. 절대값 상관 (왜곡 크기)")

df['abs_cone'] = np.abs(df['cone_delta'])
df['abs_srm'] = np.abs(df['srm_z'])
df['abs_rdm'] = np.abs(df['rdm_diff'])

r_cone_srm, p_cone_srm = spearmanr(df['abs_cone'], df['abs_srm'])
r_cone_rdm, p_cone_rdm = spearmanr(df['abs_cone'], df['abs_rdm'])
r_srm_rdm, p_srm_rdm = spearmanr(df['abs_srm'], df['abs_rdm'])

print(f"\n|Cone| vs |SRM|: ρ = {r_cone_srm:.3f}, p = {p_cone_srm:.3f}")
print(f"|Cone| vs |RDM|: ρ = {r_cone_rdm:.3f}, p = {p_cone_rdm:.3f}")
print(f"|SRM|  vs |RDM|: ρ = {r_srm_rdm:.3f}, p = {p_srm_rdm:.3f}")

# 3. 부호 고려한 상관 (원래 값)
print("\n### 3. 부호 고려한 상관 (원래 값)")

r_cone_srm_signed, p_cone_srm_signed = spearmanr(df['cone_delta'], df['srm_z'])
r_cone_rdm_signed, p_cone_rdm_signed = spearmanr(df['cone_delta'], df['rdm_diff'])
r_srm_rdm_signed, p_srm_rdm_signed = spearmanr(df['srm_z'], df['rdm_diff'])

print(f"\nCone vs SRM: ρ = {r_cone_srm_signed:.3f}, p = {p_cone_srm_signed:.3f}")
print(f"Cone vs RDM: ρ = {r_cone_rdm_signed:.3f}, p = {p_cone_rdm_signed:.3f}")
print(f"SRM  vs RDM: ρ = {r_srm_rdm_signed:.3f}, p = {p_srm_rdm_signed:.3f}")

# 4. 차원 축소 효과 검증
print("\n### 4. 차원 축소 효과 검증")
print("\n질문: RDM (수백 차원)에서도 Cone과 부호 불일치면")
print("      → 차원 축소 문제가 아니라 진짜 피질 변환")

print("\nCone vs RDM 부호 불일치 쌍:")
rdm_mismatch = df[df['cone_rdm_match'] == 0]
for _, row in rdm_mismatch.iterrows():
    print(f"  {row['pair']:15s}: Cone {row['cone_delta']:+.3f} ↔ RDM {row['rdm_diff']:+.3f}")

# 5. 상세 표
print("\n### 5. 상세 비교표")
print("\n" + df[['pair', 'cone_delta', 'srm_z', 'rdm_diff',
                 'cone_srm_match', 'cone_rdm_match', 'srm_rdm_match']].to_markdown(index=False))

# 6. 해석
print("\n" + "="*70)
print("결론")
print("="*70)

if df['cone_rdm_match'].mean() < 0.5:
    print("\n❌ 차원 축소 가설 기각:")
    print(f"   RDM (수백 차원)에서도 Cone과 {df['cone_rdm_match'].mean()*100:.0f}% 일치")
    print("   → 부호 불일치는 k=3-4 축소 때문이 아니라")
    print("   → Cone → Voxel 사이의 진짜 비선형 피질 변환")
else:
    print("\n✓ 차원 축소 가설 지지:")
    print(f"   RDM (수백 차원)에서는 Cone과 {df['cone_rdm_match'].mean()*100:.0f}% 일치")
    print(f"   SRM (k=3-4)에서만 {df['cone_srm_match'].mean()*100:.0f}% 일치")
    print("   → 차원 축소가 부호 불일치 주 원인")

if r_cone_srm > 0.5 and p_cone_srm < 0.05:
    print(f"\n✓ 절대값 상관 유의 (ρ={r_cone_srm:.3f}, p={p_cone_srm:.3f}):")
    print("   → Cone model은 왜곡 '크기' 예측에는 유용")
    print("   → 부호(방향)만 문제")
else:
    print(f"\n❌ 절대값 상관도 약함 (ρ={r_cone_srm:.3f}, p={p_cone_srm:.3f}):")
    print("   → Cone model은 크기도 예측 못함")
