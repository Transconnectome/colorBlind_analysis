"""
save_extended_metrics_patch.py
-------------------------------
Patch to add PCA coordinates and channel responses to results.pkl

이 코드를 fir_reconstruction_*.py의 "Save Results" 섹션에 추가하세요.

위치: results dict를 pickle로 저장하기 전 (Line ~1385-1390)
"""

# ============================================================================
# PATCH: Save Extended Metrics for CVD Analysis
# ============================================================================

# 이 코드를 results dict 정의 직후에 추가:

# 1. Save PCA coordinates (if PCA was used)
if USE_PCA:
    print("Saving PCA coordinates for CVD analysis...")

    # Reconstruct PCA coordinates for each color (averaged across runs)
    pca_coordinates_per_color = []  # (n_colors, n_components)

    for color_idx in range(N_COLORS):
        # Get data for this color across all runs
        color_data = all_betas[:, color_idx, :]  # (n_runs, n_voxels)

        # Average across runs
        color_data_mean = color_data.mean(axis=0)  # (n_voxels,)

        # Standardize (same as during analysis)
        scaler = StandardScaler()
        color_data_scaled = scaler.fit_transform(color_data_mean.reshape(1, -1))

        # Apply PCA
        pca = PCA(n_components=N_PCA_COMPONENTS)
        # Fit on all data (all colors, all runs) to get same transformation
        X_all = all_betas.reshape(-1, n_voxels)
        scaler_all = StandardScaler()
        X_all_scaled = scaler_all.fit_transform(X_all)
        pca.fit(X_all_scaled)

        # Transform this color
        color_pca = pca.transform(color_data_scaled)  # (1, n_components)
        pca_coordinates_per_color.append(color_pca[0])

    pca_coordinates_per_color = np.array(pca_coordinates_per_color)  # (n_colors, n_components)

    results['pca_coordinates'] = {
        'coordinates': pca_coordinates_per_color,  # (n_colors, n_components)
        'n_components': N_PCA_COMPONENTS,
        'color_names': [f'color_{i+1}' for i in range(N_COLORS)],
        'component_names': [f'PC{i+1}' for i in range(N_PCA_COMPONENTS)],
    }

    print(f"  Saved PCA coordinates: {pca_coordinates_per_color.shape}")

# 2. Save channel responses (from forward model)
print("Saving channel responses for CVD analysis...")

# Extract channel responses for each color (averaged across runs)
# This requires re-running forward model on averaged data

# Create basis functions (6 channels)
def create_basis_functions(n_channels=6):
    hues = np.linspace(0, 360, n_channels, endpoint=False)
    basis = np.zeros((360, n_channels))
    for i, center_hue in enumerate(hues):
        for h in range(360):
            dist = np.abs(h - center_hue)
            if dist > 180:
                dist = 360 - dist
            response = np.cos(np.deg2rad(dist))
            if response > 0:
                basis[h, i] = response ** 2
            else:
                basis[h, i] = 0
    return basis

basis_functions = create_basis_functions(n_channels=6)

def hue_to_channels(hue_deg):
    hue_idx = int(np.round(hue_deg)) % 360
    return basis_functions[hue_idx]

# Get channel outputs for each color
channel_responses_per_color = []  # (n_colors, 6)

for color_idx in range(N_COLORS):
    color_name = f'color_{color_idx+1}'
    true_hue = LABEL2HUE_DEG[color_name]
    channels = hue_to_channels(true_hue)
    channel_responses_per_color.append(channels)

channel_responses_per_color = np.array(channel_responses_per_color)  # (n_colors, 6)

results['channel_responses'] = {
    'responses': channel_responses_per_color,  # (n_colors, 6)
    'n_channels': 6,
    'color_names': [f'color_{i+1}' for i in range(N_COLORS)],
    'channel_names': [f'Ch{i}' for i in range(6)],
    'channel_centers_deg': [0, 60, 120, 180, 240, 300],  # Channel center hues
}

print(f"  Saved channel responses: {channel_responses_per_color.shape}")

# 3. Save color pair distances (in reconstruction space)
print("Saving color pair distances for CVD analysis...")

# Extract mean reconstructed hues for each color
mean_reconstructed_hues = []
for result in novel_color_results:
    reconstructed_hues = result['reconstructed_hues']
    mean_hue = circular_mean_deg(reconstructed_hues)
    mean_reconstructed_hues.append(mean_hue)

# Compute pairwise distances
color_pair_distances = []
for i in range(N_COLORS):
    for j in range(i+1, N_COLORS):
        hue_i = mean_reconstructed_hues[i]
        hue_j = mean_reconstructed_hues[j]
        distance = circular_diff_deg(hue_i, hue_j)

        color_pair_distances.append({
            'color1': f'color_{i+1}',
            'color2': f'color_{j+1}',
            'distance': distance,
        })

results['color_pair_distances'] = color_pair_distances

print(f"  Saved {len(color_pair_distances)} color pair distances")

# ============================================================================
# END OF PATCH
# ============================================================================

# 이제 기존 코드의 pickle.dump(results, f) 실행
# results dict에 다음이 추가됨:
#   - results['pca_coordinates']
#   - results['channel_responses']
#   - results['color_pair_distances']
