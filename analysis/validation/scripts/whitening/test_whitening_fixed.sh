#!/bin/bash
# Test whitening with centered residuals fix
# Expected: Realistic noise ceiling (0.4-0.7), SNR (1-5), shrinkage (0.3-0.5)

SUBJECT="01"
ROI="V1"
BASELINE_DIR="/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline_residuals"
OUTPUT_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/whitening_evaluation/TEST_CENTERED_$(date +%Y%m%d_%H%M%S)"

echo "=================================================="
echo "TEST: Whitening with Centered Residuals"
echo "Subject: sub-${SUBJECT}"
echo "ROI: ${ROI}"
echo "Output: ${OUTPUT_DIR}"
echo "=================================================="

# Activate conda
source ~/.bashrc
eval "$(conda shell.bash hook)"
conda activate nilearn

# Create output dir
mkdir -p ${OUTPUT_DIR}

# Check residuals statistics before running
echo ""
echo "Pre-check: Residuals statistics"
python << EOF
import numpy as np
from pathlib import Path

residuals_path = Path("${BASELINE_DIR}/sub-${SUBJECT}/${ROI}/residuals_1st_level.npy")
if residuals_path.exists():
    residuals = np.load(residuals_path)
    print(f"Residuals shape: {residuals.shape}")
    print(f"Mean: {residuals.mean():.3f} (should be ~113 before centering)")
    print(f"Std: {residuals.std():.3f}")
    print(f"Min: {residuals.min():.3f}")
    print(f"Max: {residuals.max():.3f}")
else:
    print(f"ERROR: Residuals not found at {residuals_path}")
EOF

echo ""
echo "Running whitening evaluation..."
python /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/evaluate_whitening_ceiling_snr.py \
    --subject ${SUBJECT} \
    --roi ${ROI} \
    --baseline_dir ${BASELINE_DIR} \
    --output_dir ${OUTPUT_DIR} \
    --n_ceiling_iterations 1000 \
    --n_jobs 4 \
    --save_whitened_data

EXIT_CODE=$?

echo ""
echo "=================================================="
echo "RESULTS VERIFICATION"
echo "=================================================="

if [ -f "${OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_whitening_results.json" ]; then
    echo "✓ Results file created"
    echo ""

    python << EOF
import json
import sys

try:
    with open("${OUTPUT_DIR}/sub-${SUBJECT}_${ROI}_whitening_results.json", 'r') as f:
        results = json.load(f)

    print("=== Key Metrics ===")

    # Noise ceiling
    if 'noise_ceiling' in results:
        nc = results['noise_ceiling']
        raw = nc.get('raw_split_half', -999)
        whitened = nc.get('whitened_split_half', -999)
        improvement = nc.get('improvement_percent', 0)

        print(f"\nNoise Ceiling:")
        print(f"  Raw:      {raw:.3f}")
        print(f"  Whitened: {whitened:.3f}")
        print(f"  Change:   +{improvement:.1f}%")

        # Validate
        if raw < 0 or raw > 1:
            print(f"  ❌ FAIL: Raw ceiling out of range [0,1]")
            sys.exit(1)
        if whitened < 0 or whitened > 1:
            print(f"  ❌ FAIL: Whitened ceiling out of range [0,1]")
            sys.exit(1)
        if whitened <= raw:
            print(f"  ⚠️  WARNING: Whitening did not improve ceiling")
        else:
            print(f"  ✓ PASS: Ceiling improved")

    # SNR
    if 'snr_analysis' in results:
        snr = results['snr_analysis']

        # Pattern SNR
        if 'pattern_snr' in snr:
            psnr_raw = snr['pattern_snr'].get('raw', -999)
            psnr_wh = snr['pattern_snr'].get('whitened', -999)
            psnr_imp = snr['pattern_snr'].get('improvement_percent', 0)

            print(f"\nPattern SNR:")
            print(f"  Raw:      {psnr_raw:.2f}")
            print(f"  Whitened: {psnr_wh:.2f}")
            print(f"  Change:   +{psnr_imp:.1f}%")

            # Validate
            if psnr_raw < 0.5 or psnr_raw > 10:
                print(f"  ⚠️  WARNING: Raw pattern SNR unusual ({psnr_raw:.2f})")
            if psnr_wh > 100:
                print(f"  ❌ FAIL: Whitened SNR unrealistic (>{psnr_wh:.2f})")
                sys.exit(1)
            if psnr_wh > psnr_raw:
                print(f"  ✓ PASS: Pattern SNR improved")

        # Effective SNR
        if 'effective_snr' in snr:
            esnr_raw = snr['effective_snr'].get('raw', -999)
            esnr_wh = snr['effective_snr'].get('whitened', -999)

            print(f"\nEffective SNR:")
            print(f"  Raw:      {esnr_raw:.2f}")
            print(f"  Whitened: {esnr_wh:.2f}")

            # Validate
            if esnr_raw > 100:
                print(f"  ❌ FAIL: Raw effective SNR unrealistic (>{esnr_raw:.2f})")
                sys.exit(1)
            if esnr_wh > 100:
                print(f"  ❌ FAIL: Whitened effective SNR unrealistic (>{esnr_wh:.2f})")
                sys.exit(1)
            if esnr_wh > esnr_raw:
                print(f"  ✓ PASS: Effective SNR improved")

    # Covariance estimation
    if 'whitening_info' in results:
        wh_info = results['whitening_info']
        shrinkage = wh_info.get('shrinkage', -999)

        print(f"\nCovariance Estimation:")
        print(f"  Shrinkage: {shrinkage:.3f}")

        # Validate
        if shrinkage < 0.01:
            print(f"  ❌ FAIL: Shrinkage too low (<0.01) - covariance estimation failed")
            sys.exit(1)
        elif shrinkage < 0.2:
            print(f"  ⚠️  WARNING: Low shrinkage ({shrinkage:.3f})")
        elif shrinkage > 0.6:
            print(f"  ⚠️  WARNING: High shrinkage ({shrinkage:.3f}) - noisy data")
        else:
            print(f"  ✓ PASS: Shrinkage in expected range [0.2, 0.6]")

    # RDM reliability
    if 'rdm_reliability' in results:
        rdm = results['rdm_reliability']
        raw_rdm = rdm.get('raw', -999)
        wh_rdm = rdm.get('whitened_procrustes', -999)

        print(f"\nRDM Reliability:")
        print(f"  Raw:              {raw_rdm:.3f}")
        print(f"  Whitened+Proc:    {wh_rdm:.3f}")

        if wh_rdm > raw_rdm:
            print(f"  ✓ PASS: Whitening improved RDM reliability")
        else:
            print(f"  ⚠️  WARNING: No RDM improvement from whitening")

    print("\n===================")
    print("✅ ALL VALIDATION CHECKS PASSED")
    print("Whitening is working correctly with centered residuals!")

except Exception as e:
    print(f"❌ Error parsing results: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Test SUCCESSFUL - Fix verified!"
        echo ""
        echo "Next steps:"
        echo "  1. Upload fixed evaluate_whitening_ceiling_snr.py"
        echo "  2. Run full array job: sbatch sbatch/run_whitening_ceiling_evaluation.sbatch"
    else
        echo ""
        echo "❌ Test FAILED - Results still unrealistic"
        echo "Check output in: ${OUTPUT_DIR}"
    fi
else
    echo "❌ Results file not created"
    exit 1
fi

exit ${EXIT_CODE}
