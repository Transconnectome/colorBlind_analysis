"""
Quality control visualization tools for the ColorBlind analysis pipeline.
"""

import os
import numpy as np
import matplotlib.pyplot as plt

try:
    from config import cfg  # when running scripts from repository root
except ImportError:  # pragma: no cover - fallback for package-style imports
    from .config import cfg  # type: ignore


def _normalize_roi_array(data):
    """Return ROI responses as a 2D array (samples x voxels)."""
    arr = np.asarray(data)
    if arr.ndim == 1:
        arr = arr[:, np.newaxis]
    return arr


def plot_roi_responses(roi_data, save_dir=None):
    """Plot the average beta response per stimulus condition for each ROI."""
    if not roi_data:
        print("[WARN] No ROI data available for plotting responses.")
        return

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.ravel()
    for ax in axes:
        ax.set_visible(False)

    n_colors = getattr(cfg, "N_COLORS", None)

    for ax, (roi, data) in zip(axes, roi_data.items()):
        arr = _normalize_roi_array(data)
        if arr.size == 0:
            continue

        n_samples = arr.shape[0]
        use_colors = n_colors and n_samples % n_colors == 0 and n_colors > 0

        if use_colors:
            n_runs = n_samples // n_colors
            reshaped = arr.reshape(n_runs, n_colors, -1)
            mean_response = reshaped.mean(axis=(0, 2))
            x = np.arange(n_colors)
            xticklabels = [f'Color {i + 1}' for i in x]
        else:
            mean_response = arr.mean(axis=1)
            x = np.arange(mean_response.size)
            xticklabels = [f'Sample {i + 1}' for i in x]

        ax.set_visible(True)
        ax.bar(x, mean_response)
        ax.set_title(f'{roi} Mean Response')
        ax.set_xlabel('Condition')
        ax.set_ylabel('Beta')
        ax.set_xticks(x)
        if len(xticklabels) <= 12:
            ax.set_xticklabels(xticklabels, rotation=45, ha='right')
        else:
            ax.set_xticklabels([])

    plt.tight_layout()
    if save_dir:
        plt.savefig(os.path.join(save_dir, 'roi_responses.png'))
    plt.show()

def _extract_classification_entry(entry):
    """Safely retrieve the classification results dictionary for an ROI."""
    if not isinstance(entry, dict):
        return None
    if 'classification' in entry:
        return entry['classification']
    return entry if 'confusion' in entry or 'run_accuracy' in entry else None


def plot_confusion_matrices(results, save_dir=None):
    """Plot confusion matrices for each ROI."""
    if not results:
        print("[WARN] No results available for confusion-matrix plotting.")
        return

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.ravel()
    for ax in axes:
        ax.set_visible(False)

    populated = False
    for ax, (roi, entry) in zip(axes, results.items()):
        class_data = _extract_classification_entry(entry)
        if not class_data:
            continue

        confusion = class_data.get('confusion') or class_data.get('confusion_matrix')
        if confusion is None:
            continue

        cm = np.asarray(confusion)
        if cm.ndim != 2:
            continue

        populated = True
        ax.set_visible(True)
        im = ax.imshow(cm, interpolation='nearest', cmap='viridis')
        n_rows, n_cols = cm.shape
        for i in range(n_rows):
            for j in range(n_cols):
                val = cm[i, j]
                color = 'w' if val < (cm.max() / 2.0) else 'black'
                ax.text(j, i, f"{val:.2f}", ha='center', va='center', color=color)
        ax.set_title(f'{roi} Confusion Matrix')
        ax.set_xlabel('Predicted')
        ax.set_ylabel('True')
        plt.colorbar(im, ax=ax)

    if not populated:
        plt.close(fig)
        print("[WARN] No confusion matrices available to plot.")
        return

    plt.tight_layout()
    if save_dir:
        plt.savefig(os.path.join(save_dir, 'confusion_matrices.png'))
    plt.show()


def plot_accuracy_comparison(results, save_dir=None):
    """Plot accuracy comparison across ROIs."""
    if not results:
        print("[WARN] No results available for accuracy comparison.")
        return

    rois = []
    accuracies = []
    for roi, entry in results.items():
        class_data = _extract_classification_entry(entry)
        if not class_data:
            continue

        run_acc = class_data.get('run_accuracy') or class_data.get('train_accuracy')
        if run_acc is None:
            continue

        rois.append(roi)
        accuracies.append(float(np.nanmean(run_acc)))

    if not rois:
        print("[WARN] No classification accuracy data to plot.")
        return

    plt.figure(figsize=(8, 6))
    plt.bar(rois, accuracies)
    chance = 1.0 / getattr(cfg, "N_COLORS", len(accuracies) or 1)
    plt.axhline(chance, color='r', linestyle='--', label=f'Chance ({chance:.2f})')
    plt.ylabel('Classification Accuracy')
    plt.title('Decoding Performance by ROI')
    plt.legend()

    if save_dir:
        plt.savefig(os.path.join(save_dir, 'accuracy_comparison.png'))
    plt.show()

def make_qc_report(roi_data, model_results, output_dir):
    """Generate comprehensive QC report"""
    os.makedirs(output_dir, exist_ok=True)
    
    plot_roi_responses(roi_data, output_dir)
    plot_confusion_matrices(model_results, output_dir)
    plot_accuracy_comparison(model_results, output_dir)
    
    print(f"[OK] QC plots saved to {output_dir}")

if __name__ == '__main__':
    from bh_anal import BHAnalysisPipeline
    
    # Example usage
    pipeline = BHAnalysisPipeline()
    roi_data = pipeline.run_extract_roi()
    results = pipeline.run_forward_model(roi_data)
    
    output_dir = os.path.join(pipeline.config.analysis_dir, 'qc_plots')
    make_qc_report(roi_data, results, output_dir)
