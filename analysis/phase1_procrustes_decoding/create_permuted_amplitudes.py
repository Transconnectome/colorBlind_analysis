#!/usr/bin/env python3
"""
Create permuted amplitude files for red-green label permutation analysis

핵심 아이디어:
- Run 1-3: Original labels (color_1=red, color_4=green)
- Run 4-6: Swapped labels (color_1=green, color_4=red)
→ Train/Test mismatch 생성
→ CVD가 red-green을 구분하지 못하면 성능 유지, 구분하면 성능 저하

Permutation Scenarios:
1. red_green_primary: color_1 (0°) ↔ color_4 (135°)
2. red_cyan: color_1 (0°) ↔ color_5 (180°)
3. orange_green: color_2 (45°) ↔ color_4 (135°)
4. orange_cyan: color_2 (45°) ↔ color_5 (180°)
"""

import numpy as np
import json
from pathlib import Path
import argparse
import shutil

# Color mappings (hue in degrees)
LABEL2HUE_DEG_ORIGINAL = {
    'color_1': 0.0,    # Red
    'color_2': 45.0,   # Orange
    'color_3': 90.0,   # Yellow
    'color_4': 135.0,  # Green
    'color_5': 180.0,  # Cyan
    'color_6': 225.0,  # Blue
    'color_7': 270.0,  # Violet
    'color_8': 315.0,  # Pinkish
}

PERMUTATION_SCENARIOS = {
    # ========================================================================
    # Level 1: Pairwise Permutation (2 colors, 25% of trials affected)
    # ========================================================================
    'red_green_primary': {
        'swap_pairs': [(0, 3)],  # color_1 ↔ color_4
        'description': 'Swap red (0°) and green (135°)',
        'level': 1,
        'label2hue': {
            'color_1': 135.0,  # color_1 now points to green
            'color_2': 45.0,
            'color_3': 90.0,
            'color_4': 0.0,    # color_4 now points to red
            'color_5': 180.0,
            'color_6': 225.0,
            'color_7': 270.0,
            'color_8': 315.0,
        }
    },
    'red_cyan': {
        'swap_pairs': [(0, 4)],  # color_1 ↔ color_5
        'description': 'Swap red (0°) and cyan (180°)',
        'level': 1,
        'label2hue': {
            'color_1': 180.0,
            'color_2': 45.0,
            'color_3': 90.0,
            'color_4': 135.0,
            'color_5': 0.0,
            'color_6': 225.0,
            'color_7': 270.0,
            'color_8': 315.0,
        }
    },
    'orange_green': {
        'swap_pairs': [(1, 3)],  # color_2 ↔ color_4
        'description': 'Swap orange (45°) and green (135°)',
        'level': 1,
        'label2hue': {
            'color_1': 0.0,
            'color_2': 135.0,
            'color_3': 90.0,
            'color_4': 45.0,
            'color_5': 180.0,
            'color_6': 225.0,
            'color_7': 270.0,
            'color_8': 315.0,
        }
    },
    'orange_cyan': {
        'swap_pairs': [(1, 4)],  # color_2 ↔ color_5
        'description': 'Swap orange (45°) and cyan (180°)',
        'level': 1,
        'label2hue': {
            'color_1': 0.0,
            'color_2': 180.0,
            'color_3': 90.0,
            'color_4': 135.0,
            'color_5': 45.0,
            'color_6': 225.0,
            'color_7': 270.0,
            'color_8': 315.0,
        }
    },

    # ========================================================================
    # Level 2: Half-Space Permutation (4 colors, 50% of trials affected)
    # ========================================================================
    'warm_cool': {
        'swap_pairs': [(0, 3), (1, 4), (2, 6), (7, 5)],  # Red↔Green, Orange↔Cyan, Yellow↔Violet, Pink↔Blue
        'description': 'Swap warm colors (Red, Orange, Yellow, Pink) ↔ cool colors (Green, Cyan, Violet, Blue)',
        'level': 2,
        'label2hue': {
            'color_1': 135.0,  # Red → Green
            'color_2': 180.0,  # Orange → Cyan
            'color_3': 270.0,  # Yellow → Violet
            'color_4': 0.0,    # Green → Red
            'color_5': 45.0,   # Cyan → Orange
            'color_6': 315.0,  # Blue → Pink
            'color_7': 90.0,   # Violet → Yellow
            'color_8': 225.0,  # Pink → Blue
        }
    },
    'opposite_quadrants': {
        'swap_pairs': [(0, 4), (1, 5), (2, 6), (3, 7)],  # Red↔Cyan, Orange↔Blue, Yellow↔Violet, Green↔Pink
        'description': 'Swap opposite color wheel quadrants (180° apart)',
        'level': 2,
        'label2hue': {
            'color_1': 180.0,  # Red → Cyan
            'color_2': 225.0,  # Orange → Blue
            'color_3': 270.0,  # Yellow → Violet
            'color_4': 315.0,  # Green → Pink
            'color_5': 0.0,    # Cyan → Red
            'color_6': 45.0,   # Blue → Orange
            'color_7': 90.0,   # Violet → Yellow
            'color_8': 135.0,  # Pink → Green
        }
    },
    'adjacent_quadrants': {
        'swap_pairs': [(0, 2), (1, 3), (4, 6), (5, 7)],  # Red↔Yellow, Orange↔Green, Cyan↔Violet, Blue↔Pink
        'description': 'Swap adjacent color wheel quadrants (90° apart)',
        'level': 2,
        'label2hue': {
            'color_1': 90.0,   # Red → Yellow
            'color_2': 135.0,  # Orange → Green
            'color_3': 0.0,    # Yellow → Red
            'color_4': 45.0,   # Green → Orange
            'color_5': 270.0,  # Cyan → Violet
            'color_6': 315.0,  # Blue → Pink
            'color_7': 180.0,  # Violet → Cyan
            'color_8': 225.0,  # Pink → Blue
        }
    },

    # ========================================================================
    # Level 3: Full Random Permutation (8 colors, 50% of trials affected)
    # Multiple seeds for robustness testing
    # ========================================================================
    'full_random_seed42': {
        'random_seed': 42,
        'description': 'Full random permutation of all 8 colors (seed=42)',
        'level': 3,
    },
    'full_random_seed123': {
        'random_seed': 123,
        'description': 'Full random permutation of all 8 colors (seed=123)',
        'level': 3,
    },
    'full_random_seed456': {
        'random_seed': 456,
        'description': 'Full random permutation of all 8 colors (seed=456)',
        'level': 3,
    },
    'full_random_seed789': {
        'random_seed': 789,
        'description': 'Full random permutation of all 8 colors (seed=789)',
        'level': 3,
    },
    'full_random_seed999': {
        'random_seed': 999,
        'description': 'Full random permutation of all 8 colors (seed=999)',
        'level': 3,
    },
}


def create_permuted_amplitudes(input_dir, output_dir, scenario='red_green_primary',
                              randomize_runs=False, n_permute_runs=3, seed=None):
    """
    Create permuted amplitudes with partial run swapping

    Args:
        input_dir: GLM 결과 디렉토리 (amplitudes_z.npy 위치)
        output_dir: Permuted amplitudes 저장 디렉토리
        scenario: Permutation scenario name
        randomize_runs: If True, randomly select which runs to permute (default: False)
        n_permute_runs: Number of runs to permute when randomize_runs=True (default: 3)
        seed: Random seed for run selection (default: None, auto-generated from scenario)
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load original amplitudes
    print(f"\n{'='*60}")
    print(f"Creating Permuted Amplitudes")
    print(f"Scenario: {scenario}")
    print(f"{'='*60}\n")

    amplitudes_z = np.load(input_path / "amplitudes_z.npy")  # (6 runs, 8 colors, N voxels)
    n_runs, n_colors, n_voxels = amplitudes_z.shape

    print(f"Input: {input_path}")
    print(f"  Shape: {amplitudes_z.shape}")
    print(f"  Runs: {n_runs}, Colors: {n_colors}, Voxels: {n_voxels}")

    # Get permutation configuration
    if scenario not in PERMUTATION_SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}. Available: {list(PERMUTATION_SCENARIOS.keys())}")

    config = PERMUTATION_SCENARIOS[scenario]
    description = config['description']
    level = config.get('level', 1)

    print(f"\nPermutation Level: {level}")
    print(f"Description: {description}")

    # Determine which runs to permute
    if randomize_runs:
        # Randomized run selection
        if seed is None:
            # Auto-generate seed from scenario for reproducibility
            seed = hash(scenario) % 10000
        np.random.seed(seed)

        # Randomly select n_permute_runs from all 6 runs
        all_run_indices = np.arange(n_runs)
        permute_run_indices = np.random.choice(all_run_indices, size=min(n_permute_runs, n_runs), replace=False)
        permute_run_indices = sorted(permute_run_indices)  # Sort for clarity

        print(f"  Randomized run selection (seed={seed}):")
        print(f"    Permuting runs: {[idx+1 for idx in permute_run_indices]} (indices: {permute_run_indices})")
        print(f"    Original runs: {[idx+1 for idx in all_run_indices if idx not in permute_run_indices]}")
    else:
        # Fixed run selection (original behavior: runs 4-6)
        permute_run_indices = [3, 4, 5]  # Runs 4-6 (0-indexed: 3-5)
        print(f"  Fixed run selection:")
        print(f"    Runs 1-3 (idx 0-2): Original labels")
        print(f"    Runs 4-6 (idx 3-5): Permuted labels")

    # Create permuted version
    amplitudes_permuted = amplitudes_z.copy()

    # Check if this is Level 3 (random permutation)
    if 'random_seed' in config:
        # Level 3: Full random permutation
        random_seed = config['random_seed']
        np.random.seed(random_seed)

        # Generate random permutation of color indices
        color_indices = np.arange(n_colors)
        permuted_indices = np.random.permutation(color_indices)

        print(f"\nRandom seed: {random_seed}")
        print(f"Permutation mapping:")
        for orig_idx, perm_idx in enumerate(permuted_indices):
            print(f"  color_{orig_idx+1} → color_{perm_idx+1}")

        # Apply permutation to selected runs
        for orig_idx in range(n_colors):
            perm_idx = permuted_indices[orig_idx]
            amplitudes_permuted[permute_run_indices, orig_idx, :] = amplitudes_z[permute_run_indices, perm_idx, :]

        # Create label2hue mapping for random permutation
        label2hue_permuted = {}
        for orig_idx in range(n_colors):
            perm_idx = permuted_indices[orig_idx]
            color_key = f'color_{orig_idx+1}'
            # Original color gets the hue of the permuted color
            label2hue_permuted[color_key] = LABEL2HUE_DEG_ORIGINAL[f'color_{perm_idx+1}']

        # Store permutation mapping for metadata
        swap_pairs = [(i, int(permuted_indices[i])) for i in range(n_colors) if i != permuted_indices[i]]

    else:
        # Level 1 or 2: Predefined swap pairs
        swap_pairs = config['swap_pairs']
        label2hue_permuted = config['label2hue']

        print(f"\nSwap pairs: {swap_pairs}")

        # Swap selected runs
        for color_a, color_b in swap_pairs:
            runs_display = [idx+1 for idx in permute_run_indices]
            print(f"\n  Swapping color_{color_a+1} ↔ color_{color_b+1} in runs {runs_display}:")
            print(f"    Runs {runs_display}: color_{color_a+1} gets color_{color_b+1}'s beta")
            print(f"    Runs {runs_display}: color_{color_b+1} gets color_{color_a+1}'s beta")

            # Swap for selected runs
            temp = amplitudes_permuted[permute_run_indices, color_a, :].copy()
            amplitudes_permuted[permute_run_indices, color_a, :] = amplitudes_z[permute_run_indices, color_b, :]
            amplitudes_permuted[permute_run_indices, color_b, :] = temp

    # Save permuted amplitudes
    np.save(output_path / "amplitudes_z.npy", amplitudes_permuted)
    print(f"\n✓ Saved: {output_path / 'amplitudes_z.npy'}")

    # Save label2hue mapping (for reconstruction)
    with open(output_path / "label2hue_permuted.json", 'w') as f:
        json.dump(label2hue_permuted, f, indent=2)
    print(f"✓ Saved: {output_path / 'label2hue_permuted.json'}")

    # Save metadata
    metadata = {
        'scenario': scenario,
        'description': description,
        'level': level,
        'swap_pairs': swap_pairs,
        'swap_runs': [4, 5, 6],  # 1-indexed
        'original_runs': [1, 2, 3],  # 1-indexed
        'input_dir': str(input_path),
        'n_runs': n_runs,
        'n_colors': n_colors,
        'n_voxels': n_voxels,
    }

    # Add random seed for Level 3
    if 'random_seed' in config:
        metadata['random_seed'] = config['random_seed']

    with open(output_path / "permutation_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Saved: {output_path / 'permutation_metadata.json'}")

    # Copy other necessary files
    for filename in ['amplitudes_raw.npy', 'voxel_snr.npy', 'hrf_rmse.npy',
                     'roi_hrf.npy', 'selected_voxel_indices.npy']:
        src = input_path / filename
        if src.exists():
            shutil.copy(src, output_path / filename)
            print(f"✓ Copied: {filename}")

    print(f"\n{'='*60}")
    print(f"Permutation Complete!")
    print(f"Output: {output_path}")
    print(f"{'='*60}\n")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description='Create permuted amplitudes for red-green label permutation analysis'
    )

    parser.add_argument('--subject', type=str, required=True,
                        help='Subject ID (01, 02, ..., 10)')
    parser.add_argument('--roi', type=str, required=True,
                        help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--timestamp', type=str, required=True,
                        help='Baseline timestamp (e.g., baseline81_deob)')
    parser.add_argument('--scenario', type=str, default='red_green_primary',
                        choices=list(PERMUTATION_SCENARIOS.keys()),
                        help='Permutation scenario')
    parser.add_argument('--dataset', type=str, default='deoblique_v2',
                        help='Dataset name')
    parser.add_argument('--config', type=str, default=None,
                        help='Config directory name (auto-detected if not provided)')

    # Randomized run selection (NEW 2025-12-15)
    parser.add_argument('--randomize_runs', action='store_true',
                        help='Randomize which runs to permute (default: False, uses runs 4-6)')
    parser.add_argument('--n_permute_runs', type=int, default=3,
                        help='Number of runs to permute when randomize_runs=True (default: 3)')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for run selection (default: hash(subject+roi+scenario))')

    args = parser.parse_args()

    # Construct paths
    if args.config is None:
        # Auto-detect config directory
        base_dir = Path(f'derivatives/BH2009_{args.dataset}/{args.timestamp}')
        # Find directory matching pattern
        pattern = f"*_sub-{args.subject}_{args.roi}_*"
        matching_dirs = list(base_dir.glob(pattern))

        if len(matching_dirs) == 0:
            raise FileNotFoundError(f"No config directory found matching: {base_dir / pattern}")
        elif len(matching_dirs) > 1:
            print(f"Warning: Multiple directories found. Using first one:")
            for d in matching_dirs:
                print(f"  - {d}")

        config_dir = matching_dirs[0].name
    else:
        config_dir = args.config

    input_dir = Path(f'derivatives/BH2009_{args.dataset}/{args.timestamp}/{config_dir}')
    output_dir = Path(f'derivatives/BH2009_{args.dataset}/{args.timestamp}_permuted_{args.scenario}/{config_dir}')

    # Create permuted amplitudes
    create_permuted_amplitudes(
        input_dir=input_dir,
        output_dir=output_dir,
        scenario=args.scenario,
        randomize_runs=args.randomize_runs,
        n_permute_runs=args.n_permute_runs,
        seed=args.seed
    )

    print(f"\nNext step:")
    print(f"  Run feature selection with permuted labels:")
    print(f"  python feature_selection_anova.py \\")
    print(f"    --subject {args.subject} \\")
    print(f"    --roi {args.roi} \\")
    print(f"    --timestamp {args.timestamp}_permuted_{args.scenario} \\")
    print(f"    --dataset {args.dataset}")


if __name__ == '__main__':
    main()
