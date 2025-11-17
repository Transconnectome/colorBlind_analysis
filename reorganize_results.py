"""
Reorganize analysis results from subject-based to method-ROI-based structure

OLD STRUCTURE:
logs/TIMESTAMP/sub-01/fir_reconstruction_uni_hrf/METHOD/ROI_universal_hrf/

NEW STRUCTURE:
logs/TIMESTAMP_reorganized/METHOD_ROI/sub-01_*

Date: 2025-11-17
"""

import shutil
from pathlib import Path
import re

def reorganize_results(source_dir, target_dir=None):
    """
    Reorganize results from subject-based to method-ROI-based structure

    Parameters:
    -----------
    source_dir : str or Path
        Source directory (e.g., 'logs/20251117_021334')
    target_dir : str or Path, optional
        Target directory. If None, creates 'source_dir_reorganized'
    """
    source_dir = Path(source_dir)

    if target_dir is None:
        target_dir = Path(str(source_dir) + "_reorganized")
    else:
        target_dir = Path(target_dir)

    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nReorganizing: {source_dir}")
    print(f"Target:       {target_dir}")
    print("="*80)

    subjects = ["sub-01", "sub-02", "sub-03", "sub-04"]
    rois = ["V1", "V2", "V3", "hV4"]

    # Track statistics
    files_copied = 0
    folders_created = set()

    # Iterate through all possible combinations
    for subject in subjects:
        subject_path = source_dir / subject / "fir_reconstruction_uni_hrf"

        if not subject_path.exists():
            print(f"⚠️  Skipping {subject}: path does not exist")
            continue

        # Find all method directories (zScore, voxelSelect, etc.)
        for method_dir in subject_path.iterdir():
            if not method_dir.is_dir():
                continue

            method_name = method_dir.name  # e.g., 'zScore', 'voxelSelect'

            # Find all ROI directories
            for roi in rois:
                roi_dir = method_dir / f"{roi}_universal_hrf"

                if not roi_dir.exists():
                    continue

                # Create method-ROI folder
                method_roi_folder = target_dir / f"{method_name}_{roi}"
                method_roi_folder.mkdir(parents=True, exist_ok=True)
                folders_created.add(str(method_roi_folder))

                # Copy files with subject prefix
                # 1. Copy log.txt
                if (roi_dir / "log.txt").exists():
                    shutil.copy2(
                        roi_dir / "log.txt",
                        method_roi_folder / f"{subject}_log.txt"
                    )
                    files_copied += 1

                # 2. Copy results.pkl
                if (roi_dir / "results.pkl").exists():
                    shutil.copy2(
                        roi_dir / "results.pkl",
                        method_roi_folder / f"{subject}_results.pkl"
                    )
                    files_copied += 1

                # 3. Copy summary.csv
                if (roi_dir / "summary.csv").exists():
                    shutil.copy2(
                        roi_dir / "summary.csv",
                        method_roi_folder / f"{subject}_summary.csv"
                    )
                    files_copied += 1

                # 4. Copy mask file
                mask_file = roi_dir / f"{roi}_functional_selection_mask.nii.gz"
                if mask_file.exists():
                    shutil.copy2(
                        mask_file,
                        method_roi_folder / f"{subject}_{roi}_mask.nii.gz"
                    )
                    files_copied += 1

                # 5. Copy all figures
                figures_dir = roi_dir / "figures"
                if figures_dir.exists():
                    for fig_file in figures_dir.iterdir():
                        if fig_file.is_file():
                            # Extract figure type from filename
                            # e.g., "V1_confusion_matrix.png" -> "confusion_matrix"
                            fig_name = fig_file.name
                            fig_name = re.sub(f"^{roi}_", "", fig_name)  # Remove ROI prefix

                            new_name = f"{subject}_{fig_name}"
                            shutil.copy2(
                                fig_file,
                                method_roi_folder / new_name
                            )
                            files_copied += 1

                print(f"✓ Copied {subject} → {method_name}_{roi}")

    print("\n" + "="*80)
    print(f"REORGANIZATION COMPLETE")
    print(f"  Folders created: {len(folders_created)}")
    print(f"  Files copied:    {files_copied}")
    print(f"  Target:          {target_dir}")
    print("="*80)

    # List all created folders
    print("\nCreated folders:")
    for folder in sorted(folders_created):
        folder_path = Path(folder)
        n_files = len(list(folder_path.iterdir()))
        print(f"  {folder_path.name:25s} ({n_files} files)")

    return target_dir

def create_summary_readme(target_dir):
    """Create a README in the reorganized directory explaining the structure"""

    target_dir = Path(target_dir)
    readme_path = target_dir / "README.md"

    content = """# Reorganized Analysis Results

## Directory Structure

This directory contains analysis results organized by **method-ROI pairs**.

### Folder Naming Convention
```
{METHOD}_{ROI}/
```

Where:
- **METHOD**: Analysis method (e.g., `zScore`, `voxelSelect`)
- **ROI**: Brain region (e.g., `V1`, `V2`, `V3`, `hV4`)

### File Naming Convention

Within each folder, files are prefixed by subject ID:
```
{SUBJECT}_{filetype}
```

Examples:
- `sub-01_log.txt` - Analysis log for subject 01
- `sub-01_results.pkl` - Pickle file with results
- `sub-01_summary.csv` - Summary statistics
- `sub-01_V1_mask.nii.gz` - ROI mask
- `sub-01_confusion_matrix.png` - Confusion matrix figure
- `sub-01_circular_color_space.png` - Circular color space figure
- `sub-01_reconstruction_per_run.png` - Per-run reconstruction
- `sub-01_universal_hrf.png` - HRF figure

### Available Comparisons

This structure makes it easy to:
1. **Compare methods** for a specific ROI (compare `zScore_V1/` vs `voxelSelect_V1/`)
2. **Compare subjects** within a method-ROI (all files in `zScore_V1/`)
3. **Compare ROIs** for a specific method (compare `zScore_V1/` vs `zScore_V2/`)

### Example Usage

To compare all subjects' performance in V1 using zscore:
```bash
ls zScore_V1/sub-*_summary.csv
```

To view all figures for sub-01 across all methods and ROIs:
```bash
find . -name "sub-01_*.png"
```

### Subject Groups
- **Non-CVD**: sub-01, sub-02
- **CVD**: sub-03, sub-04

---
Generated: 2025-11-17
"""

    with open(readme_path, 'w') as f:
        f.write(content)

    print(f"\n✓ Created README: {readme_path}")

def main():
    """Main reorganization function for both log directories"""

    print("\n" + "="*80)
    print("REORGANIZING ANALYSIS RESULTS")
    print("="*80)

    # Reorganize both directories
    dirs_to_reorganize = [
        "logs/20251117_021334",  # zscore
        "logs/20251117_021329",  # voxelSelect
    ]

    reorganized_dirs = []

    for dir_path in dirs_to_reorganize:
        if Path(dir_path).exists():
            target = reorganize_results(dir_path)
            create_summary_readme(target)
            reorganized_dirs.append(target)
        else:
            print(f"\n⚠️  Directory not found: {dir_path}")

    # Create combined reorganized directory
    if len(reorganized_dirs) > 0:
        print("\n" + "="*80)
        print("CREATING COMBINED REORGANIZED DIRECTORY")
        print("="*80)

        combined_dir = Path("logs/20251117_combined_reorganized")
        combined_dir.mkdir(parents=True, exist_ok=True)

        # Copy all files from both reorganized directories
        for src_dir in reorganized_dirs:
            for method_roi_folder in Path(src_dir).iterdir():
                if method_roi_folder.is_dir() and not method_roi_folder.name.startswith('.'):
                    target_folder = combined_dir / method_roi_folder.name

                    # Copy or merge
                    if not target_folder.exists():
                        shutil.copytree(method_roi_folder, target_folder)
                        print(f"✓ Created {target_folder.name}")
                    else:
                        # Merge files
                        for file in method_roi_folder.iterdir():
                            if file.is_file():
                                shutil.copy2(file, target_folder / file.name)
                        print(f"✓ Merged into {target_folder.name}")

        create_summary_readme(combined_dir)

        print(f"\n✓ Combined directory created: {combined_dir}")
        print(f"  Total folders: {len(list(combined_dir.glob('*_*/')))} method-ROI pairs")

    print("\n" + "="*80)
    print("ALL REORGANIZATION COMPLETE!")
    print("="*80)

if __name__ == "__main__":
    main()
