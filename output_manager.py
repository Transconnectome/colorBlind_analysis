"""
output_manager.py
-----------------
Unified output manager for reorganized directory structure

NEW STRUCTURE:
logs/{TIMESTAMP}/{METHOD}_{ROI}/
    sub-01_log.txt
    sub-01_results.pkl
    sub-01_summary.csv
    sub-01_confusion_matrix.png
    sub-01_V1_mask.nii.gz  # ROI-specific files keep ROI in name
    ...

Date: 2025-11-17
"""

import os
import sys
from pathlib import Path
from datetime import datetime


class OutputManager:
    """
    Manages output paths for reorganized method-ROI structure

    Usage:
    ------
    >>> om = OutputManager(
    ...     subject_id='01',
    ...     roi_name='V1',
    ...     method_name='zScore',
    ...     timestamp='20251117_1234'
    ... )
    >>> om.get_log_path()
    'logs/20251117_1234/zScore_V1/sub-01_log.txt'
    >>> om.get_figure_path('confusion_matrix.png')
    'logs/20251117_1234/zScore_V1/sub-01_confusion_matrix.png'
    """

    def __init__(self, subject_id, roi_name, method_name,
                 base_dir='logs', timestamp=None, create_dirs=True):
        """
        Parameters:
        -----------
        subject_id : str
            Subject ID (e.g., '01', '02', 'P01')
        roi_name : str
            ROI name (e.g., 'V1', 'V2', 'hV4')
        method_name : str
            Analysis method (e.g., 'zScore', 'voxelSelect', 'rawBeta')
        base_dir : str
            Base directory for logs (default: 'logs')
        timestamp : str, optional
            Timestamp string (default: current datetime)
        create_dirs : bool
            Whether to create directories (default: True)
        """
        self.subject_id = subject_id
        self.roi_name = roi_name
        self.method_name = method_name
        self.base_dir = Path(base_dir)

        # Generate timestamp if not provided
        if timestamp is None:
            self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        else:
            self.timestamp = timestamp

        # Create method-ROI directory
        self.method_roi_dir = self.base_dir / self.timestamp / f"{method_name}_{roi_name}"

        if create_dirs:
            self.method_roi_dir.mkdir(parents=True, exist_ok=True)

        self.subject_prefix = f"sub-{subject_id}"

    def get_path(self, filename, add_prefix=True):
        """
        Get full path for a file

        Parameters:
        -----------
        filename : str
            Base filename (e.g., 'log.txt', 'confusion_matrix.png')
        add_prefix : bool
            Whether to add subject prefix (default: True)

        Returns:
        --------
        Path object
        """
        if add_prefix:
            final_name = f"{self.subject_prefix}_{filename}"
        else:
            final_name = filename

        return self.method_roi_dir / final_name

    def get_log_path(self):
        """Get log file path"""
        return self.get_path('log.txt')

    def get_results_path(self):
        """Get results pickle path"""
        return self.get_path('results.pkl')

    def get_summary_path(self):
        """Get summary CSV path"""
        return self.get_path('summary.csv')

    def get_mask_path(self):
        """Get ROI mask path (includes ROI name)"""
        return self.get_path(f"{self.roi_name}_mask.nii.gz")

    def get_figure_path(self, figure_type):
        """
        Get figure path

        Parameters:
        -----------
        figure_type : str
            Figure type (e.g., 'confusion_matrix', 'circular_color_space')
            Can include .png extension or not

        Returns:
        --------
        Path object
        """
        # Remove ROI prefix if present (for backward compatibility)
        figure_type = figure_type.replace(f"{self.roi_name}_", "")

        # Ensure .png extension
        if not figure_type.endswith('.png'):
            figure_type += '.png'

        return self.get_path(figure_type)

    def get_zmap_path(self, color_idx):
        """Get z-map path for a specific color"""
        return self.get_path(f"color_{color_idx}_zmap.nii.gz")

    def create_dual_logger(self):
        """
        Create a dual logger that writes to both stdout and log file

        Returns:
        --------
        DualLogger object
        """
        return DualLogger(self.get_log_path())

    def __repr__(self):
        return (f"OutputManager(subject={self.subject_prefix}, "
                f"roi={self.roi_name}, method={self.method_name}, "
                f"dir={self.method_roi_dir})")


class DualLogger:
    """
    Logger that writes to both terminal and file

    Usage:
    ------
    >>> sys.stdout = DualLogger('log.txt')
    >>> print("This goes to both terminal and file")
    """

    def __init__(self, filename):
        """
        Parameters:
        -----------
        filename : str or Path
            Log file path
        """
        self.terminal = sys.stdout
        self.log = open(filename, 'w', buffering=1)

    def write(self, message):
        self.terminal.write(message)
        self.terminal.flush()
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

    def close(self):
        self.log.close()
        sys.stdout = self.terminal  # Restore original stdout

    def __del__(self):
        try:
            self.close()
        except:
            pass


def create_readme(method_roi_dir):
    """
    Create README in method-ROI directory explaining file structure

    Parameters:
    -----------
    method_roi_dir : str or Path
        Method-ROI directory path
    """
    method_roi_dir = Path(method_roi_dir)
    readme_path = method_roi_dir / "README.md"

    # Extract method and ROI from directory name
    dir_name = method_roi_dir.name
    parts = dir_name.split('_')
    roi = parts[-1]
    method = '_'.join(parts[:-1])

    content = f"""# {dir_name}

## Directory Information
- **Method:** {method}
- **ROI:** {roi}
- **Structure:** Reorganized method-ROI format

## File Naming Convention

All files are prefixed with subject ID: `sub-{{ID}}_{{filename}}`

### Standard Files
- `sub-{{ID}}_log.txt` - Analysis log
- `sub-{{ID}}_results.pkl` - Serialized results
- `sub-{{ID}}_summary.csv` - Summary statistics

### Mask Files
- `sub-{{ID}}_{roi}_mask.nii.gz` - ROI mask (if using voxel selection)

### Figure Files
- `sub-{{ID}}_confusion_matrix.png` - Classification confusion matrix
- `sub-{{ID}}_circular_color_space.png` - Circular color space visualization
- `sub-{{ID}}_reconstruction_per_run.png` - Per-run reconstruction
- `sub-{{ID}}_universal_hrf.png` - HRF response curve
- `sub-{{ID}}_polar_reconstruction.png` - Polar plot of reconstruction
- `sub-{{ID}}_error_distribution.png` - Error distribution histogram

### Optional Files
- `sub-{{ID}}_color_{{N}}_zmap.nii.gz` - Z-map for color N (if saved)

## Subject Groups
- **Non-CVD:** sub-01, sub-02
- **CVD:** sub-03, sub-04

---
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    with open(readme_path, 'w') as f:
        f.write(content)


# Example usage and tests
if __name__ == "__main__":
    print("OutputManager Test")
    print("="*70)

    # Create test manager
    om = OutputManager(
        subject_id='01',
        roi_name='V1',
        method_name='zScore',
        timestamp='TEST',
        create_dirs=False
    )

    print(f"\nManager: {om}\n")

    # Test path generation
    print("Path Examples:")
    print(f"  Log:        {om.get_log_path()}")
    print(f"  Results:    {om.get_results_path()}")
    print(f"  Summary:    {om.get_summary_path()}")
    print(f"  Mask:       {om.get_mask_path()}")
    print(f"  Figure:     {om.get_figure_path('confusion_matrix')}")
    print(f"  Figure:     {om.get_figure_path('V1_confusion_matrix.png')}")  # Backward compat
    print(f"  Z-map:      {om.get_zmap_path(1)}")

    print("\n" + "="*70)
    print("Usage Example:")
    print("""
    # In your analysis script:
    from output_manager import OutputManager

    # Create manager
    om = OutputManager(
        subject_id=args.subject,
        roi_name=args.roi,
        method_name='zScore',  # or 'voxelSelect', etc.
        timestamp='20251117_1234'  # or None for auto
    )

    # Setup logging
    sys.stdout = om.create_dual_logger()

    # Save files
    df.to_csv(om.get_summary_path(), index=False)
    plt.savefig(om.get_figure_path('confusion_matrix.png'))
    pickle.dump(results, open(om.get_results_path(), 'wb'))
    """)
