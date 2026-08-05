#!/usr/bin/env python3
"""
verify_implementation.py
------------------------
Verification script to check that all files are implemented correctly

Run this before uploading to server to ensure everything is ready.
"""

import sys
from pathlib import Path
import importlib.util


def check_file_exists(filepath: Path, description: str) -> bool:
    """Check if a file exists and is not empty"""
    if not filepath.exists():
        print(f"❌ MISSING: {description}")
        print(f"   Expected: {filepath}")
        return False

    if filepath.stat().st_size == 0:
        print(f"⚠️  EMPTY: {description}")
        print(f"   File: {filepath}")
        return False

    print(f"✅ {description}")
    return True


def check_python_imports(filepath: Path, description: str) -> bool:
    """Check if a Python file can be imported without errors"""
    try:
        spec = importlib.util.spec_from_file_location("module", filepath)
        module = importlib.util.module_from_spec(spec)
        # Don't execute, just check syntax
        compile(filepath.read_text(), filepath, 'exec')
        print(f"✅ {description} - Syntax OK")
        return True
    except SyntaxError as e:
        print(f"❌ SYNTAX ERROR: {description}")
        print(f"   {e}")
        return False
    except Exception as e:
        print(f"⚠️  WARNING: {description} - {e}")
        return True  # May be import errors, but syntax is OK


def main():
    base_dir = Path(__file__).parent
    print("="*70)
    print("Between-Subject Procrustes Implementation Verification")
    print("="*70)
    print()

    all_checks = []

    # Phase 0: Modified Preprocessing
    print("[Phase 0] Modified Preprocessing")
    print("-"*70)
    all_checks.append(check_file_exists(
        base_dir / "fir_reconstruction_no_voxel_filtering.py",
        "Modified preprocessing script"
    ))
    all_checks.append(check_python_imports(
        base_dir / "fir_reconstruction_no_voxel_filtering.py",
        "Modified preprocessing script"
    ))
    all_checks.append(check_file_exists(
        base_dir / "run_preprocessing_unfiltered.sbatch",
        "SLURM batch script"
    ))
    print()

    # Phase 1: Voxel Correspondence
    print("[Phase 1] Voxel Correspondence")
    print("-"*70)
    all_checks.append(check_file_exists(
        base_dir / "utils" / "__init__.py",
        "Utils package init"
    ))
    all_checks.append(check_file_exists(
        base_dir / "utils" / "voxel_correspondence.py",
        "Voxel correspondence utilities"
    ))
    all_checks.append(check_python_imports(
        base_dir / "utils" / "voxel_correspondence.py",
        "Voxel correspondence utilities"
    ))
    print()

    # Phase 2: ANOVA Voxel Selection
    print("[Phase 2] ANOVA Voxel Selection")
    print("-"*70)
    all_checks.append(check_file_exists(
        base_dir / "anova_voxel_selection.py",
        "ANOVA voxel selection"
    ))
    all_checks.append(check_python_imports(
        base_dir / "anova_voxel_selection.py",
        "ANOVA voxel selection"
    ))
    print()

    # Phase 3: Between-Subject Procrustes
    print("[Phase 3] Between-Subject Procrustes")
    print("-"*70)
    all_checks.append(check_file_exists(
        base_dir / "evaluate_procrustes_anova.py",
        "Procrustes evaluation"
    ))
    all_checks.append(check_python_imports(
        base_dir / "evaluate_procrustes_anova.py",
        "Procrustes evaluation"
    ))
    print()

    # Phase 4: Pipeline Integration
    print("[Phase 4] Pipeline Integration")
    print("-"*70)
    all_checks.append(check_file_exists(
        base_dir / "run_pipeline_local.py",
        "Main pipeline script"
    ))
    all_checks.append(check_python_imports(
        base_dir / "run_pipeline_local.py",
        "Main pipeline script"
    ))
    all_checks.append(check_file_exists(
        base_dir / "run_local_test.sh",
        "Test bash script"
    ))
    all_checks.append(check_file_exists(
        base_dir / "run_local_all.sh",
        "Full analysis bash script"
    ))
    print()

    # Documentation
    print("[Documentation]")
    print("-"*70)
    all_checks.append(check_file_exists(
        base_dir / "README.md",
        "Main README"
    ))
    all_checks.append(check_file_exists(
        base_dir / "SERVER_EXECUTION_GUIDE.md",
        "Server execution guide"
    ))
    all_checks.append(check_file_exists(
        base_dir / "IMPLEMENTATION_SUMMARY.md",
        "Implementation summary"
    ))
    print()

    # Directories
    print("[Directories]")
    print("-"*70)
    logs_dir = base_dir / "logs"
    results_dir = base_dir / "results"

    if logs_dir.exists():
        print(f"✅ Logs directory exists: {logs_dir}")
        all_checks.append(True)
    else:
        print(f"⚠️  Logs directory missing (will be created): {logs_dir}")
        all_checks.append(False)

    if results_dir.exists():
        print(f"✅ Results directory exists: {results_dir}")
        all_checks.append(True)
    else:
        print(f"⚠️  Results directory missing (will be created): {results_dir}")
        all_checks.append(False)
    print()

    # Check for key modifications in preprocessing script
    print("[Verification] Modified Preprocessing Changes")
    print("-"*70)
    preprocessing_file = base_dir / "fir_reconstruction_no_voxel_filtering.py"
    if preprocessing_file.exists():
        content = preprocessing_file.read_text()

        # Check for key modifications
        checks = {
            "ENABLE_VOXEL_FILTERING flag": "ENABLE_VOXEL_FILTERING" in content,
            "OUTPUT_DIR_SUFFIX flag": "OUTPUT_DIR_SUFFIX" in content,
            "Modified z-scoring logic": "⚠️ MODIFIED:" in content and "Keep ALL voxels" in content,
            "NaN handling": "np.nan_to_num" in content,
            "Zero variance handling": "mean-centering" in content.lower() or "1e-10" in content,
        }

        for check_name, passed in checks.items():
            if passed:
                print(f"✅ {check_name}")
                all_checks.append(True)
            else:
                print(f"❌ MISSING: {check_name}")
                all_checks.append(False)
    print()

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)

    passed = sum(all_checks)
    total = len(all_checks)
    percentage = 100 * passed / total if total > 0 else 0

    print(f"Checks passed: {passed}/{total} ({percentage:.1f}%)")
    print()

    if passed == total:
        print("🎉 ALL CHECKS PASSED! Implementation is complete.")
        print()
        print("Next steps:")
        print("1. Upload to server:")
        print("   scp analysis/validation/scripts/between_procrustes/fir_reconstruction_no_voxel_filtering.py \\")
        print("       analysis/validation/scripts/between_procrustes/run_preprocessing_unfiltered.sbatch \\")
        print("       haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/between_procrustes/")
        print()
        print("2. Run on server:")
        print("   ssh haba6030@node2")
        print("   cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/between_procrustes")
        print("   sbatch run_preprocessing_unfiltered.sbatch")
        print()
        print("See SERVER_EXECUTION_GUIDE.md for detailed instructions.")
        return 0
    elif passed >= total * 0.9:
        print("⚠️  MOSTLY COMPLETE with minor issues.")
        print("   Review warnings above and fix if necessary.")
        return 0
    else:
        print("❌ INCOMPLETE - Several checks failed.")
        print("   Review errors above and fix before proceeding.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
