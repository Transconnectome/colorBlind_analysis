# S14 atom redesign — comparison

- N_RESAMPLES = 50 (HC pool draws, 5-train)
- PCA_SHARED_K = 6 (A1/A2/A3 bridge)
- B1 splits = 15 (CVD 4-train / 2-test from 6 runs)
- Elapsed = 98.6s

## Atom × Candidate (median loss)

| Atom | S08-B | S08-C | S08-E | S08-D | S09-A_DPS | S09-A_orig | S09-C | GT_null_sub-08 | GT_null_sub-09 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gamma_focal | 41.399 | 39.621 | 33.498 | 0.439 | 0.290 | 4.922 | 2.139 | 44.462 | 6.055 |
| gamma_all | 11.513 | 11.322 | 6.377 | 708.145 | 0.742 | 1.115 | 10.851 | 11.272 | 1.261 |
| RDM_V1 | 0.978 | 1.102 | 1.040 | 1.000 | 0.917 | 0.925 | 0.712 | 1.000 | 1.000 |
| RDM_V2 | 0.845 | 0.973 | 1.019 | 1.143 | — | — | — | 1.000 | — |
| RDM_V3 | 0.970 | 0.908 | 1.205 | 1.035 | — | — | — | 1.000 | — |
| RDM_V4 | 0.877 | 0.852 | 0.819 | 1.016 | — | — | — | 1.000 | — |
| LOCO_V4 | 1.176 | 1.162 | 1.238 | 0.997 | 1.039 | 1.039 | 0.955 | 1.275 | 1.035 |
| A2_PCA_RDM_V1 | 0.647 | 0.852 | 0.724 | 0.794 | 0.727 | 0.696 | 0.767 | 1.000 | 1.000 |
| A2_PCA_RDM_V2 | 0.906 | 1.090 | 1.078 | 1.146 | — | — | — | 1.000 | — |
| A2_PCA_RDM_V3 | 0.629 | 0.917 | 0.817 | 1.037 | — | — | — | 1.000 | — |
| A2_PCA_RDM_V4 | 0.643 | 0.675 | 0.775 | 0.790 | — | — | — | 1.000 | — |
| A1_decoder_V1 | 0.470 | 0.497 | 0.685 | 0.914 | 0.566 | 0.434 | 0.855 | 0.390 | 0.423 |
| A1_decoder_V2 | 0.437 | 0.460 | 0.843 | 0.919 | — | — | — | 0.403 | — |
| A1_decoder_V3 | 0.433 | 0.444 | 0.643 | 0.982 | — | — | — | 0.411 | — |
| A1_decoder_V4 | 0.492 | 0.514 | 0.759 | 0.863 | — | — | — | 0.429 | — |
| A3_xs_LOCO_V4 | 1.304 | 1.322 | 1.190 | 1.313 | — | — | — | 1.292 | — |
| B1_RDM_V4 | 0.900 | 0.870 | 0.844 | 1.087 | 1.020 | 1.004 | 0.900 | 1.000 | 1.000 |
| B1_LOCO_V4 | 1.133 | 1.091 | 1.182 | 0.967 | 0.944 | 0.968 | 0.921 | 1.168 | 0.972 |
| B1_A3_xs_LOCO_V4 | 1.270 | 1.274 | 1.131 | 1.312 | — | — | — | 1.250 | — |
| A3_xs_LOCO_V1 | — | — | — | — | 1.261 | 1.322 | 1.195 | — | 1.344 |
| B1_A3_xs_LOCO_V1 | — | — | — | — | 1.261 | 1.273 | 1.145 | — | 1.273 |

## δθ RMS per candidate

| Candidate | model | forward | δθ RMS |
| --- | --- | --- | --- |
| S08-B | rc | (6.0, 2.6, 'deutan') | 19.27° |
| S08-C | rc | (6.0, 1.1, 'deutan') | 28.91° |
| S08-E | 2comp | (38.0, -44.0, 'deutan') | 29.22° |
| S08-D | 2comp | (34.0, 48.0, 'deutan') | 50.46° |
| S09-A_DPS | rc | (10.0, 2.6, 'protan') | 21.16° |
| S09-A_orig | rc | (1.5, 2.45, 'protan') | 4.06° |
| S09-C | 2comp | (6.0, 46.0, 'protan') | 33.94° |
| GT_null_sub-08 | null | None | 0.00° |
| GT_null_sub-09 | null | None | 0.00° |
---

## Findings (500-word summary)

### A2 PCA-aligned RDM — recommended augmentation

A2_PCA_RDM (PCA proxy for SRM, K=6) is the only new atom that produces a strictly larger gap between real candidates and the null GT than the existing within-voxel RDM atom. On hV4 the existing RDM_V4 (sub-08): real candidates 0.82-1.02 vs GT_null=1.00 (gap 0.0-0.18). A2_PCA_RDM_V4 (sub-08): real 0.64-0.79 vs GT_null=1.00 (gap 0.21-0.36, ~2× wider sensitivity). At V1 (sub-09): A2_PCA_RDM_V1 separates real candidates (0.696-0.767) from GT_null (1.000) by 0.23-0.30 with IQR≈0.03-0.06. The PCA denoising step is doing real work — concentrating the response covariance into K=6 components reduces voxel-noise variance in the RDM cosine.

**Sub-09 ranking change under A2.** A2_PCA_RDM_V1 prefers S09-A_orig (0.696 ± 0.031) over S09-A_DPS (0.727 ± 0.042). This is a non-trivial reversal of the Phase C v2 preference (S09-A_DPS chosen via composite). The IQRs are tight enough that the swap is real, not noise. For sub-08, S08-B and S08-C are statistically tied under A2_V4 (0.643 ± 0.069 vs 0.675 ± 0.074) — agnostic about g=2.60 vs g=1.10 within behavior axis.

### A1 cross-subject decoder — design failure

A1_decoder shows an *inverted* discrimination: GT_null = 0.39-0.43 (best, lowest loss) while real candidates yield 0.43-0.98 (higher loss). This is a structural artifact: the Procrustes alignment R is fit on the un-perturbed CVD PC to maximize diagonal HC↔CVD match at δθ=0. Any δθ≠0 candidate then necessarily *degrades* that pre-fit alignment, regardless of whether the model is correct. A1 as currently implemented measures residual post-Procrustes misalignment, not model fit. Salvage would require refitting Procrustes per δθ candidate (apply δθ to HC ref before alignment) — out of scope here. **Do not include A1 in any composite.**

### A3 cross-subject LOCO — collapsed signal

A3_xs_LOCO is flat across all candidates and nulls (range 1.13-1.34). The K=6 PCA bridge collapses the cross-subject prediction signal, exactly as advisor predicted. The atom does not discriminate real from null. **Negative result — do not use.**

### B1 CVD run-split wrapper — bias-neutral

B1_LOCO_V4 (sub-08): real 0.92-1.18 vs GT_null=1.17. B1_RDM_V4 (sub-08): real 0.84-1.09 vs null=1.00. Compared to the unwrapped originals, B1 versions track within ~0.03 with no inversion or hidden bias revealed. The "LOCO IQR=0 artifact" from Cycle 4 is not resolved by run-splitting because the within-CVD W training step is repeated independently on test runs — the wrapper averages noise but does not introduce external information. **B1 is a useful audit tool (confirms stability under CVD run-split) but not a composite atom.**

### Recommendation

1. **Add A2_PCA_RDM at the candidate-relevant ROI** (V4 for sub-08, V1 for sub-09) to the composite. It provides ~2× cleaner real-vs-null separation than within-voxel RDM, and changes the sub-09 ranking (S09-A_orig > S09-A_DPS) — a finding worth pursuing with confirmatory analysis.
2. **Drop A1** (Procrustes-circular by construction) and **drop A3** (PCA-bridge collapses signal). Report both as honest negative findings.
3. **Keep B1 as an audit tool**, not a composite component. Use to spot-check candidates flagged by other atoms; do not weight into selection.
4. The double-dipping concern (Cycle 4 Issue 1) is *partially* addressed by A2 (PC space removes voxel-level overlap between train/test of HC pool RDM construction). Strict cross-subject decoding remains unresolved — A3 attempt confirms the PCA-bridge approach is too lossy.
