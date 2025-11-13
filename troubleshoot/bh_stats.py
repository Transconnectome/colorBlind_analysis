"""
Statistical analysis tools for the ColorBlind pipeline.
"""

import numpy as np
from scipy import stats
import pandas as pd
import matplotlib.pyplot as plt

def run_permutation_test(roi_data, n_permutations=1000, save_dir=None):
    """
    Run permutation tests to assess significance of color decoding.
    
    Args:
        roi_data: Dictionary of ROI responses {roi_name: response_matrix}
        n_permutations: Number of permutations for the test
        save_dir: Directory to save results
        
    Returns:
        Dictionary of p-values per ROI
    """
    p_values = {}
    null_distributions = {}
    
    n_runs = 6
    n_colors = 8
    
    for roi, responses in roi_data.items():
        print(f"\nTesting {roi}...")
        true_accuracies = []
        null_accuracies = []
        
        # Get true accuracy
        for test_run in range(n_runs):
            test_idx = slice(test_run * n_colors, (test_run + 1) * n_colors)
            test_data = responses[:, test_idx]
            train_data = np.delete(responses, test_idx, axis=1)
            
            W = np.linalg.pinv(train_data.T @ train_data) @ train_data.T
            predictions = np.argmax(W @ test_data, axis=0)
            true_labels = np.arange(n_colors)
            
            accuracy = np.mean(predictions == true_labels)
            true_accuracies.append(accuracy)
        
        true_mean = np.mean(true_accuracies)
        
        # Generate null distribution
        for _ in range(n_permutations):
            perm_accuracies = []
            for test_run in range(n_runs):
                test_idx = slice(test_run * n_colors, (test_run + 1) * n_colors)
                test_data = responses[:, test_idx]
                train_data = np.delete(responses, test_idx, axis=1)
                
                # Permute labels
                perm_labels = np.random.permutation(n_colors)
                
                W = np.linalg.pinv(train_data.T @ train_data) @ train_data.T
                predictions = np.argmax(W @ test_data, axis=0)
                
                accuracy = np.mean(predictions == perm_labels)
                perm_accuracies.append(accuracy)
            
            null_accuracies.append(np.mean(perm_accuracies))
        
        # Calculate p-value
        p_value = np.mean(np.array(null_accuracies) >= true_mean)
        p_values[roi] = p_value
        null_distributions[roi] = null_accuracies
        
        print(f"True accuracy: {true_mean:.3f}")
        print(f"p-value: {p_value:.3e}")
        
        if save_dir:
            # Plot null distribution
            plt.figure(figsize=(8, 6))
            plt.hist(null_accuracies, bins=50, color='C0', alpha=0.8)
            plt.axvline(true_mean, color='r', linestyle='--', 
                       label=f'True accuracy: {true_mean:.3f}')
            # chance level is an x-axis value (accuracy), draw vertical line
            plt.axvline(1/8, color='g', linestyle=':', 
                       label='Chance level (1/8)')
            plt.title(f'{roi} Null Distribution')
            plt.xlabel('Classification Accuracy')
            plt.ylabel('Count')
            plt.legend()
            plt.savefig(f"{save_dir}/{roi}_null_dist.png")
            plt.close()
    
    return p_values, null_distributions

def analyze_color_selectivity(roi_data, save_dir=None):
    """
    Analyze color selectivity patterns in each ROI.
    
    Args:
        roi_data: Dictionary of ROI responses {roi_name: response_matrix}
        save_dir: Directory to save results
    """
    selectivity_metrics = {}
    
    for roi, responses in roi_data.items():
        print(f"\nAnalyzing {roi}...")
        
        # 1. Calculate mean response per color
        mean_responses = responses.mean(axis=1)  # (n_colors,)
        
        # 2. Calculate selectivity index (max - min) / (max + min)
        selectivity_idx = ((mean_responses.max() - mean_responses.min()) / 
                          (mean_responses.max() + mean_responses.min()))
        
        # 3. Calculate tuning width (std of responses)
        tuning_width = mean_responses.std()
        
        # 4. Calculate response reliability (correlation between runs)
        n_runs = 6
        n_colors = 8
        reliability = []
        for i in range(n_runs):
            for j in range(i+1, n_runs):
                run1 = responses[:, i*n_colors:(i+1)*n_colors]
                run2 = responses[:, j*n_colors:(j+1)*n_colors]
                r = np.corrcoef(run1.ravel(), run2.ravel())[0,1]
                reliability.append(r)
        
        metrics = {
            'selectivity_index': selectivity_idx,
            'tuning_width': tuning_width,
            'reliability': np.mean(reliability)
        }
        selectivity_metrics[roi] = metrics
        
        print(f"Selectivity index: {selectivity_idx:.3f}")
        print(f"Tuning width: {tuning_width:.3f}")
        print(f"Response reliability: {np.mean(reliability):.3f}")
        
        if save_dir:
            # Plot tuning curves
            plt.figure(figsize=(8, 6))
            colors = plt.cm.hsv(np.linspace(0, 1, n_colors))
            
            for run in range(n_runs):
                run_data = responses[:, run*n_colors:(run+1)*n_colors]
                plt.plot(range(n_colors), run_data, 
                        alpha=0.3, color='gray', linewidth=1)
            
            plt.plot(range(n_colors), mean_responses, 
                    'k-', linewidth=2, label='Mean')
            
            plt.title(f'{roi} Color Tuning')
            plt.xlabel('Color')
            plt.ylabel('Response (β)')
            plt.legend()
            plt.savefig(f"{save_dir}/{roi}_tuning.png")
            plt.close()
    
    return selectivity_metrics

if __name__ == '__main__':
    from bh_anal import BHAnalysisPipeline
    
    # Example usage
    pipeline = BHAnalysisPipeline()
    roi_data = pipeline.run_extract_roi()
    
    output_dir = os.path.join(pipeline.config.analysis_dir, 'stats')
    os.makedirs(output_dir, exist_ok=True)
    
    # Run analyses
    p_values, null_dists = run_permutation_test(roi_data, save_dir=output_dir)
    selectivity = analyze_color_selectivity(roi_data, save_dir=output_dir)