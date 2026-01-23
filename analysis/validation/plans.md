This is to verify data and model structure in the analysis. 

## Data Verification
- [ ]  Preprocessing results: Metrics & Visualization
	•	tSNR: ROI별 tSNR 분포(중앙값/사분위)
	•	Mask 안정성: ROI voxel count(run별), overlap(Dice) between runs
        •	(필수) ROI overlay QC (run별 reference 위에 mask)
- [ ]  HRF Estimation: Correlation between runs
- [ ]  Procrustes: RDM between color sets, Inter Subject Similarity in procrustes or SRM
    - [ ]  Baseline Threshold: how much similarity is needed?? How much RDM??
    : TODO: search for relevant research and gather standards
    - [ ]  Visualization: RDM matrix, color distance visualization for each run + overlap, procrustes visualization

## Decoding Model

- [ ]  여러 모델 비교 (SVM, Ridge, MLP - non-linearlity) + 현재 모델 보완
- How: Apply non-linearlity in phase1's decoder instead of current linear matrix W
- Why: Assuming linearlity in brain's channel - voxel mapping is highly vulnerable
    - [ ]  Metrics:
        1. Mean, SD of each model
        2. Test-retest reliability (How can I extract distribution?)
        3. Confidence test with intervals (how?)
        4. uncertainty quantification (what is this)
    - [ ]  Visualizations:
        1. Bar Graphs with above metrics