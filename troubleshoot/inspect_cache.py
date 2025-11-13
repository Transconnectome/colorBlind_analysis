#!/usr/bin/env python
"""
Simple script to inspect the structure of cached reconstruction results
"""

import os
import joblib
import pandas as pd
import numpy as np

OUTDIR = './hrf_test_outputs'

print("=" * 80)
print("CACHE INSPECTION TOOL")
print("=" * 80)
print()

# Check brain cache
brain_cache = os.path.join(OUTDIR, 'cache_brain', 'reconstruction_results.joblib')

if os.path.exists(brain_cache):
    print(f"Found: {brain_cache}")
    print("-" * 80)

    data = joblib.load(brain_cache)

    print(f"Type: {type(data)}")
    print()

    if isinstance(data, dict):
        print("Keys in file:")
        for key in data.keys():
            val = data[key]
            if isinstance(val, (list, tuple)):
                print(f"  {key}: {type(val).__name__} with {len(val)} items")
                if len(val) > 0:
                    print(f"    First item type: {type(val[0])}")
                    if isinstance(val[0], dict):
                        print(f"    First item keys: {list(val[0].keys())}")
            elif isinstance(val, dict):
                print(f"  {key}: dict with keys {list(val.keys())}")
            else:
                print(f"  {key}: {type(val).__name__} = {val}")
        print()

        # Try to extract hit rates
        print("Attempting to extract hit rates and p-values:")
        print()

        if 'all_hits' in data and 'all_ps' in data:
            print("✅ Found 'all_hits' and 'all_ps' keys (standard structure)")
            all_hits = data['all_hits']
            all_ps = data['all_ps']
            all_thrs = data.get('all_thrs', [])

            print(f"   Number of runs: {len(all_hits)}")
            print()
            print("   Per-run details:")
            for i, (hit, p) in enumerate(zip(all_hits, all_ps), 1):
                thr = all_thrs[i-1] if i-1 < len(all_thrs) else 'N/A'
                print(f"     Run {i}: hit_rate={hit:.3f}, p_value={p:.3f}, threshold={thr}")
            print()

            # Compute mean
            print(f"   Mean hit rate: {np.mean(all_hits):.3f}")
            print(f"   Mean p-value:  {np.mean(all_ps):.3f}")
        elif 'per_run_results' in data:
            print("✅ Found 'per_run_results' key")
            per_run = data['per_run_results']
            print(f"   Number of runs: {len(per_run)}")
            print()
            print("   Per-run details:")
            for i, run_result in enumerate(per_run, 1):
                if isinstance(run_result, dict):
                    hit = run_result.get('hit_rate', 'N/A')
                    p = run_result.get('p_value', 'N/A')
                    print(f"     Run {i}: hit_rate={hit}, p_value={p}")
            print()

            # Compute mean
            hits = [r['hit_rate'] for r in per_run if 'hit_rate' in r]
            ps = [r['p_value'] for r in per_run if 'p_value' in r]
            if hits and ps:
                print(f"   Mean hit rate: {np.mean(hits):.3f}")
                print(f"   Mean p-value:  {np.mean(ps):.3f}")
        else:
            print("❌ No 'per_run_results' key found")
            print("   Looking for alternative structure...")

            # Look for run_X keys
            run_keys = [k for k in data.keys() if k.startswith('run_')]
            if run_keys:
                print(f"   Found {len(run_keys)} run_X keys: {run_keys}")
                for key in run_keys:
                    print(f"   {key}: {data[key]}")
    else:
        print("Data is not a dictionary!")
        print(f"Value: {data}")

    print()
else:
    print(f"❌ Cache file not found: {brain_cache}")
    print()
    print("Run naive_analysis.py first to generate reconstruction results.")

print()
print("=" * 80)

# Also check for CSV file
csv_file = os.path.join(OUTDIR, 'cache_brain', 'reconstruction_results.csv')
if os.path.exists(csv_file):
    print(f"Found CSV file: {csv_file}")
    print("-" * 80)
    df = pd.read_csv(csv_file)
    print(df.to_string(index=False))
    print()
else:
    print(f"No CSV file found: {csv_file}")
    print()
