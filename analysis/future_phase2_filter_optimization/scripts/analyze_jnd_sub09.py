"""Aggregate JND across HC pool and compare CVD (sub-08, sub-09) per pair."""
import pandas as pd
import numpy as np

DATA_DIR = "data/behavior"
HC_SUBJS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
CVD_SUBJS = ['sub-08', 'sub-09']

PAIRS = ['red-orange', 'orange-yellow', 'yellow-green', 'green-blue',
         'blue-purple', 'yellow-purple', 'cyan-magenta', 'red-cyan']


def load_jnd(subj):
    """Return dict pair -> mean of sc0 + sc1."""
    df = pd.read_csv(f"{DATA_DIR}/{subj}_jnd_ses1_no_filter_summary.csv")
    out = {}
    for p in PAIRS:
        sub = df[df['pair_name'] == p]
        if len(sub) == 0:
            out[p] = np.nan
        else:
            out[p] = sub['jnd_mean'].mean()  # avg of sc0, sc1
    return out


def main():
    # Load all
    data = {s: load_jnd(s) for s in HC_SUBJS + CVD_SUBJS}

    # HC pool stats per pair
    print("=" * 110)
    print(f"{'Pair':<18}" + "".join(f"{s:>9}" for s in HC_SUBJS) +
          f"{'HC_mean':>10}{'HC_SD':>9}" + f"{'sub-08':>10}{'sub-09':>10}")
    print("=" * 110)
    hc_means_per_pair = {}
    hc_sds_per_pair = {}
    for p in PAIRS:
        hc_vals = [data[s][p] for s in HC_SUBJS]
        hc_mean = np.nanmean(hc_vals)
        hc_sd = np.nanstd(hc_vals, ddof=1)
        hc_means_per_pair[p] = hc_mean
        hc_sds_per_pair[p] = hc_sd
        sub08 = data['sub-08'][p]
        sub09 = data['sub-09'][p]
        row = f"{p:<18}" + "".join(
            f"{data[s][p]:>9.3f}" if not np.isnan(data[s][p]) else f"{'NA':>9}"
            for s in HC_SUBJS
        ) + f"{hc_mean:>10.3f}{hc_sd:>9.3f}{sub08:>10.3f}{sub09:>10.3f}"
        print(row)
    print("=" * 110)

    # CVD vs HC summary — z-score and ratio
    print(f"\n{'Pair':<18}{'sub-08 z':>10}{'sub-08/HC':>12}{'sub-08 dir':>14}"
          f"{'sub-09 z':>10}{'sub-09/HC':>12}{'sub-09 dir':>14}")
    print("=" * 92)
    for p in PAIRS:
        hcm = hc_means_per_pair[p]
        hcs = hc_sds_per_pair[p]
        s08 = data['sub-08'][p]
        s09 = data['sub-09'][p]
        z08 = (s08 - hcm) / hcs if hcs > 0 else np.nan
        z09 = (s09 - hcm) / hcs if hcs > 0 else np.nan
        r08 = s08 / hcm
        r09 = s09 / hcm

        def label_dir(r):
            if r > 1.5:
                return "HYPO (worse)"
            elif r < 0.7:
                return "HYPER (better)"
            else:
                return "≈HC"
        d08 = label_dir(r08)
        d09 = label_dir(r09)
        print(f"{p:<18}{z08:>10.2f}{r08:>12.2f}{d08:>14}{z09:>10.2f}{r09:>12.2f}{d09:>14}")
    print("=" * 92)

    # Summary statistics
    print(f"\n--- Summary ---")
    s08_hypo_n = sum(1 for p in PAIRS if data['sub-08'][p] / hc_means_per_pair[p] > 1.5)
    s08_hyper_n = sum(1 for p in PAIRS if data['sub-08'][p] / hc_means_per_pair[p] < 0.7)
    s09_hypo_n = sum(1 for p in PAIRS if data['sub-09'][p] / hc_means_per_pair[p] > 1.5)
    s09_hyper_n = sum(1 for p in PAIRS if data['sub-09'][p] / hc_means_per_pair[p] < 0.7)
    print(f"sub-08 (deutan): HYPO pairs (worse than HC) = {s08_hypo_n}/8, HYPER pairs (better) = {s08_hyper_n}/8")
    print(f"sub-09 (protan): HYPO pairs (worse than HC) = {s09_hypo_n}/8, HYPER pairs (better) = {s09_hyper_n}/8")

    # Overall JND average
    s08_overall = np.mean([data['sub-08'][p] for p in PAIRS])
    s09_overall = np.mean([data['sub-09'][p] for p in PAIRS])
    hc_overall = np.mean([hc_means_per_pair[p] for p in PAIRS])
    hc_sd_overall = np.std([np.mean([data[s][p] for s in HC_SUBJS]) for p in PAIRS], ddof=1)
    print(f"\nOverall mean JND (across 8 pairs):")
    print(f"  HC mean = {hc_overall:.3f}")
    print(f"  sub-08 = {s08_overall:.3f}")
    print(f"  sub-09 = {s09_overall:.3f}")

    # Z-scored CVD overall vs HC distribution of overall means
    hc_overall_per_subj = [np.mean([data[s][p] for p in PAIRS]) for s in HC_SUBJS]
    hc_mean_of_means = np.mean(hc_overall_per_subj)
    hc_sd_of_means = np.std(hc_overall_per_subj, ddof=1)
    z08_overall = (s08_overall - hc_mean_of_means) / hc_sd_of_means
    z09_overall = (s09_overall - hc_mean_of_means) / hc_sd_of_means
    print(f"\nHC pool overall JND per subject: {[f'{v:.3f}' for v in hc_overall_per_subj]}")
    print(f"HC mean of subject-means = {hc_mean_of_means:.3f} ± {hc_sd_of_means:.3f}")
    print(f"sub-08 overall z = {z08_overall:+.2f}")
    print(f"sub-09 overall z = {z09_overall:+.2f}")


if __name__ == "__main__":
    main()
