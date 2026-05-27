"""Fit response noise σ from HC 8AFC confusion matrices.

P(j|i; sigma, delta_theta) ∝ exp(−d_mod(theta_i + delta_theta_i, theta_j)² / sigma²)

For HC, assume delta_theta = 0 (no perceptual rotation).
For CVD (sub-08, sub-09), also fit but reporting separately.
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar

HUES_DEG = np.arange(0, 360, 45)
HC_SUBJS = ['sub-01', 'sub-03', 'sub-06', 'sub-07']
CVD_SUBJS = ['sub-08', 'sub-09']
DATA_DIR = "data/behavior"


def hue_dist_modular(theta_i, theta_j):
    d = np.abs(theta_i - theta_j)
    return np.minimum(d, 360 - d)


def softmax_pred_8afc(sigma, delta_theta=None):
    if delta_theta is None:
        delta_theta = np.zeros(8)
    P = np.zeros((8, 8))
    for i in range(8):
        theta_perceived = (HUES_DEG[i] + delta_theta[i]) % 360
        for j in range(8):
            d = hue_dist_modular(theta_perceived, HUES_DEG[j])
            P[i, j] = np.exp(-(d ** 2) / (sigma ** 2))
        P[i] /= P[i].sum()
    return P


def neg_log_lik(sigma, conf, delta_theta=None):
    if sigma <= 0.5 or sigma > 200:
        return 1e10
    P = softmax_pred_8afc(sigma, delta_theta)
    P = np.clip(P, 1e-12, 1.0)
    return -np.sum(conf * np.log(P))


def build_confusion(df):
    counts = np.zeros((8, 8))
    for _, row in df.iterrows():
        try:
            i = int(row['stimulus_label'].split('_')[1]) - 1
            j = int(row['response_label'].split('_')[1]) - 1
            counts[i, j] += 1
        except Exception:
            continue
    return counts


def load_subj(subj):
    csv = f"{DATA_DIR}/{subj}_rsvp_8afc_ses1_run1.csv"
    df = pd.read_csv(csv)
    df = df[df['rt'] > 0]
    return df, build_confusion(df)


def main():
    results = {}
    for subj in HC_SUBJS + CVD_SUBJS:
        df, conf = load_subj(subj)
        acc = df['correct'].mean()
        res = minimize_scalar(lambda s: neg_log_lik(s, conf),
                              bounds=(1.0, 100.0), method='bounded',
                              options={'xatol': 0.1})
        sigma_fit = res.x
        P = softmax_pred_8afc(sigma_fit)
        pc_pred = np.mean([P[i, i] for i in range(8)])
        results[subj] = {
            'n': len(df), 'acc': acc, 'errors': int(conf.sum() - np.trace(conf)),
            'sigma': sigma_fit, 'pc_pred': pc_pred,
        }

    print("=" * 82)
    print(f"{'Subject':<14} {'N':>5} {'Accuracy':>10} {'Errors':>8} {'σ_fit (deg)':>13} {'P_correct@σ':>14}")
    print("=" * 82)
    for s, r in results.items():
        label = "HC" if s in HC_SUBJS else "CVD"
        print(f"{s} ({label})    {r['n']:>5}  {r['acc']*100:>8.2f}%  {r['errors']:>5}  "
              f"{r['sigma']:>10.2f}  {r['pc_pred']*100:>11.2f}%")
    print("=" * 82)

    hc_sigmas = [results[s]['sigma'] for s in HC_SUBJS]
    print(f"\nHC pool σ_HC stats (N=4):")
    print(f"  mean = {np.mean(hc_sigmas):.2f}°")
    print(f"  SD   = {np.std(hc_sigmas, ddof=1):.2f}°")
    print(f"  range = [{min(hc_sigmas):.2f}, {max(hc_sigmas):.2f}]°")

    # Pooled HC fit (combine all 4 HC confusions → more stable, treats all as exchangeable)
    pooled_hc_conf = np.zeros((8, 8))
    for s in HC_SUBJS:
        _, c = load_subj(s)
        pooled_hc_conf += c
    res_pool = minimize_scalar(lambda s: neg_log_lik(s, pooled_hc_conf),
                                bounds=(1.0, 100.0), method='bounded',
                                options={'xatol': 0.1})
    print(f"\nPooled HC σ (single fit on combined N=4 confusion):")
    print(f"  σ_pooled = {res_pool.x:.2f}°")
    print(f"  Pooled trials: {int(pooled_hc_conf.sum())}, correct: {int(np.trace(pooled_hc_conf))}, "
          f"acc: {np.trace(pooled_hc_conf)/pooled_hc_conf.sum()*100:.2f}%")

    # Sensitivity sweep — what σ predicts what accuracy?
    print(f"\nσ sensitivity (predicted overall accuracy at δθ=0):")
    for sigma in [5, 10, 15, 20, 22, 24, 26, 30, 40, 50]:
        P = softmax_pred_8afc(sigma)
        pc = np.mean([P[i, i] for i in range(8)])
        print(f"  σ={sigma:>3}°: P(correct) = {pc*100:.2f}%")

    # Error structure: which adjacent-color confusions dominate?
    print(f"\n--- Per-HC error structure (stim → response, count) ---")
    for s in HC_SUBJS:
        _, conf = load_subj(s)
        err_pairs = [(i + 1, j + 1, int(conf[i, j])) for i in range(8) for j in range(8)
                     if i != j and conf[i, j] > 0]
        if err_pairs:
            # Distance of each error
            ann = [(i, j, c, int(hue_dist_modular(HUES_DEG[i-1], HUES_DEG[j-1]))) for i, j, c in err_pairs]
            print(f"  {s}: {ann}  [last col = hue dist in deg]")
        else:
            print(f"  {s}: 0 errors (degenerate σ fit)")


if __name__ == "__main__":
    main()
