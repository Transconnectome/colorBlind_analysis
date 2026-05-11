## Data collection

**Participants**   
Twelve volunteers were recruited under Institutional Review Board approval (\#2510/002-023), providing written informed consent prior to participation. Participants reported no history of neurological disorders. Color vision was assessed using the 14-plate Ishihara test (Ishihara, 1917). Participants accurately identifying more than 12 plates were classified as Healthy Controls (HC; n=7, 3 females, age 22.7±2.5 years), while those scoring below this threshold were classified as having Color Vision Deficiency (CVD; n=2, including one participant with deuteranomaly and one with protanomaly, both male). Three participants were excluded for failing to complete the experiment. Given the small CVD sample, all CVD results are interpreted as individual case demonstrations using Crawford & Howell (1998) single-case statistics, not as population-level effects.

**fMRI experiment**  
We conducted an fMRI experiment to collect participants’ voxel responses while perceiving colors. Stimuli consisted of eight colors equally spaced from 0**°** to 315° in Commission Internationale de L’Eclairage (CIE) L\*a\*b\* space (Commission Internationale de L’Eclairage, 1986). A gray filler was additionally included as a nonchromatic condition. Their lightness was fixed to L\* \= 75 with an identical distance of 40 chroma from the gray point with a\* \= 0, and b \* \= 0 **(Fig 1A)**.   
To maintain participants’ attention and fixation, we conducted a modified ‘Rapid Serial Visual Presentation’(RSVP) detection task(Brouwer & Heeger, 2009\) throughout each run. During the experiment, a circular patch was presented for 1.5 s. The patch contained one of the color stimuli or a gray point in a randomized order. The order of colors was optimized using the Neurodesign package(Durnez et al., 2018\) to maximize design efficiency. 0.35s after stimulus onset, a set of alternating alphabets was presented for 0.4s each above the stimulus. Participants were instructed to press a button when an alphabet 'K' appeared consecutively. Such a target set emerged with a random probability of 0.33. Interstimulus intervals (ISIs) were randomly selected among 3s, 4.5s, and 6s. Each run included eight repetitions of the eight colors and a gray point. Each run lasted approximately 7min and each session consisted of six runs. The experiment was designed with the Psychopy 2022.2.5 package (Peirce et al., 2019).  
To evaluate color display filter conditions, CVD participants underwent two sessions.While the first session utilized original stimuli in all runs, the second session consisted of two runs for each of three conditions: colors modified by the Windows filter, by the optimized filter and original stimuli. We compared neural responses of CVD participants under two filter conditions with the responses of HC participants to the original stimuli.  
We acquired the MRI data focusing on the occipital lobe with a Siemens 3T MAGNETOM Cima.X Scanner with BioMatrix 3T coils. To constrain FOV to posterior occipital lobe, we set twenty-four oblique slices perpendicular to calcarine sulcus(Ryu & Lee, 2024). The scanner was set as 1.5s TR, 30ms TE, 75° FA, 2 × 2 × 2 mm voxel size, and 96 × 80 matrix size. 

## Preprocessing and response estimation

**Spatial Normalization and registration**  
We converted the acquired data into BIDS format, and removed facial features using ezBIDS(Levitas et al., 2024). Functional images were then registered to the T1w image. Coregistration was performed by optimizing a Mutual Information based (MI) cost function (Maes et al., 1997; Wells et al., 1996\) via FreeSurfer’s mri\_coreg. This method is well suited to images with limited field-of-view (FOV) and obliquity because it does not require complete anatomical boundaries outside the acquired image.  
Image orientation was first initialized according to the scanner-defined obliquity information in the NIfTI header. The mutual-information cost function was then optimized to maximize the statistical dependence between T1w and BOLD intensity distribution within the overlapping region. T1w-to-MNI normalization was then performed using a 12-degrees-of-freedom affine transformation (FSL FLIRT; Jenkinson et al., 2002), followed by nonlinear warping (FNIRT; Andersson et al., 2007), yielding final BOLD data in MNI space at 2 mm isotropic resolution.

- **Supple: Confound regression and temporal filtering**

Within-run head motion was estimated via rigid-body realignment. No temporal filtering or confound regression was applied; slow drift was modeled via linear per-run regressors in the general linear model.

**ROI definition**

Bilateral regions of interest (V1, V2, V3, and hV4; Fig. 1b) were defined in MNI space at 2 mm resolution using the Wang probabilistic atlas (Wang et al., 2015). Bilateral ROIs were thresholded at 50% atlas probability (following Wang et al., 2015\) and intersected with each individual’s BOLD brain mask. Voxel counts varied across ROIs (V1: 655 \+/- 214; V2: 451 \+/- 145; V3: 103 \+/- 29; hV4: 63 \+/- 22; all mean \+/- SD across subjects).

**Supplementary \- quality control**  
Registration quality was evaluated by computing the intersection between the Wang Atlas ROIs (V1, V2, V3, hV4) and the BOLD brain mask in MNI space. Across 10 subjects, mean ROI coverage was 84.3% (SD \= 21.7%), and GLM valid ratio (percentage of ROI voxels with reliable stimulus-evoked responses) was 99.6%. We evaluated all subjects’ data suitable for downstream analysis, though sub-07 showed reduced coverage (30.8%) due to individual anatomical variability.

- Supplementary \- Voxel counts range

Saved in markdown..  
 

**FIR-based response estimation**  
Neural response amplitudes were estimated using a two-stage procedure: first extracting a hemodynamic response function (HRF) for each ROI via a finite impulse response (FIR) model, followed by a general linear model (GLM; Dale, 1999; Brouwer & Heeger, 2009, 2013). This data-driven approach recovers a more accurate HRF than canonical models because the FIR model makes no assumption about HRF shape. In the first stage, we estimated the HRF of each ROI using an FIR model. Design matrices for each run were constructed with all stimulus onsets regardless of color identity. The FIR basis set spanned 8 TRs (12 s). The FIR beta weights were estimated by fitting the model to the preprocessed voxel time courses using linear regression. A mean ROI-level HRF was then obtained by averaging the FIR beta weights across voxels within each ROI. Voxels in the top 50% of variance explained by this mean ROI-level HRF were retained, balancing signal quality with sample size (mean retained: V1 328±107, V2 226±73, V3 52±15, hV4 32±11 voxels).  
In the second stage, a design matrix was constructed by convolving binary time courses for each color condition with the estimated ROI-specific HRF and its temporal derivative. The temporal derivative was included to capture voxel-to-voxel variability in HRF timing. This design matrix was then fitted to the preprocessed MNI-space voxel time courses using linear regression to estimate response amplitudes. Beta weights for the derivative regressors were discarded, and the remaining coefficients provided a single response amplitude estimate for each voxel, color, and run.

**Within-subject Procrustes alignment**  
To improve cross-run consistency in voxel response patterns within each participant, voxel response amplitudes were aligned across runs using Procrustes alignment (Gower, 1975). To preserve structural representations, voxel response amplitude matrices (across all colors) from runs 2–6 were aligned to run 1, selected as reference to maintain temporal ordering consistency, by estimating an orthogonal transformation that minimized the residual error (Equation 1). To preserve voxel response amplitude magnitudes, scaling was prohibited. To evaluate whether alignment improved cross-run consistency while preserving stimulus-related structure, we computed the mean pairwise Pearson correlation of voxel response amplitude patterns across all run pairs (15 comparisons). Average correlation improved from r \= 0.54 (SD \= 0.12) before alignment to r \= 0.71 (SD \= 0.09) after alignment, indicating improved cross-run consistency.

  Equation 1:X\_{aligned} \= XQ: where X \\in \\mathbb{R}^{n\_{voxels} \\times n\_{colors}}  
is the amplitude matrix for a given run, 

X\_{ref} \\in \\mathbb{R}^{n\_{voxels} \\times n\_{colors}} is the reference matrix, and Q \\in \\mathbb{R}^{n\_{voxels} \\times n\_{voxels}} is the orthogonal matrix minimizing ||X\_{ref} \- XQ||\_F 

## Functional Alignment and shared representational space

**Construction of HC-derived common space with Shared Response Model**   
After within-subject Procrustes alignment, cross-subject alignment was performed using shared response modeling (SRM; Chen et al., 2015), a dimension-reduction technique related to hyperalignment (Haxby et al., 2011; Guntupalli et al., 2016). This enabled comparison of color representations in a common space across participants with different numbers of voxels. SRM learns a low-dimensional common space S where between-subject variability is minimized. We utilized the Brain Imaging Analysis Kit package (BrainIAK) for SRM implementation.   
SRM estimates linear mappings between each participant’s original voxel space and the common space. For participant i, let X\_i \\in R^{v \* c} denote the matrix of fMRI response amplitudes, where v is the number of voxels in the ROI and c \= 8 colors. SRM estimates a common space \\(S \\in \\mathbb{R}^{k \\times c}\\) and participant-specific mappings relating each \\(X\_i\\) to that space, where \\(k\\) is the reduced dimension.

  Equation 2: X\_i \= W\_iS \+ E\_i  
  Equation 3: $\\min\_{W\_i, S} \\sum\_{i=1}^N \\|X\_i \- W\_iS\\|\_F^2 \\quad \\text{s.t.} \\quad W\_i^T W\_i \= I\_k$

In equation 3, $W\_i \\in \\mathbb{R}^{v \\times k}$ is the orthogonal mapping matrix mapping participant i’s voxel space to the common space, and E\_i is the residual error. The matrix W\_i  is optimized to minimize the sum of Frobenius norm of residuals across all participants. The orthogonal constraint (W\_i^T W\_i \= I\_k) helps preserve geometric relationships between colors-distances and angles-in the common space. So, each participant’s residuals reflect the extent to which their data are not captured by the common structure, including inherent geometric differences.  
To establish an HC-derived reference common space, we fitted SRM using voxel response data from the seven HC participants only. CVD participants were subsequently projected into this fixed space by computing W\_CVD \= U V^T, where U Σ V^T \= SVD(X\_CVD · S^†), yielding an orthonormal mapping that best aligned CVD data to the HC-derived space without re-estimating S. To quantify HC-CVD disparity with unbiased references, we used a leave-one-out (LOO) consistent procedure: for each fold i (leaving out HC participant i), a reference pattern R\_{-i} was computed as the mean of the remaining six HC participants' aligned data. Both the held-out HC\_i and both CVD participants were compared against this same reference R\_{-i}, yielding disparity scores d(HC\_i, R\_{-i}) and d(CVD\_j, R\_{-i}). This ensures HC and CVD disparities are measured against identical references within each fold. Individual CVD disparity significance was assessed via Crawford & Howell (1998) modified t-tests comparing each CVD participant's mean disparity (averaged across 7 folds) to the HC  distribution (n=7, df=6).  
To identify which color pairs showed geometric deviations in CVD, we computed the representational dissimilarity matrix (RDM) for each of all 28 color pairs in the common space using correlation distance. To identify pairs exhibiting significant deviation, we computed element-wise differences between each CVD participant’s RDM and the mean HC RDM, evaluating significance via 95% bootstrap confidence intervals (1,000 iterations, resampling HC participants with replacement). Additionally, global between-subject RDM similarity was quantified using Spearman correlation.

The reduced dimension k was determined via LOSO cross-validation based on within-subject RDM reliability (Cunningham & Yu, 2014). For each candidate k and fold, reliability was quantified as the Spearman correlation between RDMs computed from even runs (2,4,6) versus odd runs (1,3,5) of the held-out participant in SRM space. We selected k maximizing mean reliability across seven folds. The selected values were: V1 k \= 4 (cross-subject RDM correlation \= 0.60); V2 k \= 4 (0.57); V3 k \= 3 (0.55); hV4 k \= 3 (0.32).

- Supple: Consistency test \- PCA, norm procrustes (TBA)

- **Supple: Mean activation analysis**

We conducted mean voxel response amplitudes analysis to identify whether SRM-based differences rely on the activation. We checked mean amplitudes across all colors and for each color. 

## Color decoding and voxel response prediction model

**Forward Encoding Model**  
We modeled hue-selective neural populations using half-wave rectified and squared sinusoidal basis functions following Brouwer and Heeger (2009, 2013; **Fig 2a**). Each of six hypothetical channels was tuned to a preferred hue θ\_k evenly spaced around the hue circle, with response profile r\_k(θ) \= max(0, cos(θ \- θ\_k))^2. The squaring operation sharpens the tuning profiles and introduces higher-order harmonic components, requiring multiple phase-shifted channels to fully span the circular hue space. Six channels provide a complete basis set, allowing any hue-selective tuning curve to be expressed as a weighted sum of the basis functions (Freeman & Adelson, 1992).

This forward model formalizes how hypothetical color channels map to observed voxel responses: each voxel's response B is modeled as a weighted sum of six channel outputs C, where the weight matrix W represents the brain's mapping from hue-selective population activity to measured BOLD signals (Equation 4).

  Equation 4: B \= W C

Training and evaluation were conducted using cross-validations. Preprocessed response data, represented either in voxel space or in the SRM-derived shared-space, were partitioned into training (B₁, C₁) and test sets (B₂, C₂). During training, the weight matrix W was estimated via ridge regression (Equation 5), where the regularization parameter α was selected via generalized cross-validation (GCV; Golub et al., 1979). GCV provides a computationally efficient approximation to leave-one-out cross-validation for selecting α. The optimal α minimizes the GCV score (Equation 6), where \\(X\\) denotes the design matrix, y is the observed response vector, ŷ is the ridge-predicted response, H \= X(XᵀX \+ αI)⁻¹Xᵀ is the hat matrix, and n is the number of training samples. Once W was estimated, channel outputs were decoded from test voxel responses (Equation 7a), or voxel responses were predicted from channel outputs (Equation 7b). Decoded channel outputs Ĉ were converted to hue angle estimates by finding the angle θ that minimized ||Ĉ \- C(θ)||₂.

  Equation 5: Ŵ \= B₁ C₁ᵀ (C₁ C₁ᵀ \+ αI)⁻¹  
  Equation 6: GCV(α) \= (1/n) ||y \- ŷ||²₂ / (1 \- tr(H)/n)²  
  Equation 7a (color decoding): Ĉ \= (Ŵᵀ Ŵ)⁻¹ Ŵᵀ B₂  
  Equation 7b (voxel prediction): B̂ \= Ŵ C₂

**Cross-Validation and Evaluation**  
The voxel response prediction and color decoding models were evaluated using three cross-validation tasks: leave-one-run-out  (LORO), leave-one-color-out (LOCO), and leave-one-subject-out (LOSO). LORO evaluated whether individual colors could be distinguished from voxel response amplitudes, testing the consistency of neural color encoding across runs. For each of six runs, the corresponding response matrices (B, C) were held out as the test set, W was trained on the remaining five runs. Both color decoding (Equation 7a) and voxel response prediction (Equation 7b) were evaluated on the held-out run.

LOCO tested whether geometric relationships of circular hue space were preserved in neural representation by evaluating interpolation to held-out colors. For each color, all six run response matrices of the target color were held out. W was trained on the remaining seven colors, and the model predicted either the held-out color from voxel responses (Equation 7a) or voxel responses from the held-out color's channel outputs (Equation 7b).

LOSO evaluated zero-shot generalization to held-out participants. As LOSO requires  cross-subject prediction, SRM-transformed data were used to align voxel spaces across participants. For each HC participant, W was trained on the remaining HC participants' shared-space data and tested on the held-out participant. This assessed whether the HC group-derived common space supported generalization to novel individuals.

**Evaluation metrics:** Color decoding was evaluated using (1) mean absolute error (MAE) between predicted and true hue angles (chance \= 90°, expected from a uniform random predictor on a circle), and (2) categorization accuracy with ±22.5° bins around each of the eight colors (chance \= 12.5% \= 1/8). Voxel response prediction was evaluated using Pearson correlation between predicted and observed response vectors, computed across all voxels and colors in the test set. Statistical significance of group comparisons (HC vs CVD) and individual CVD analyses was assessed using nonparametric permutation tests (10,000 iterations; Nichols & Holmes, 2002).

## Behavioral-neural concordance

**Behavioral tasks**  
To examine the relationship between geometrical deviations in neural representations and perceptual color discrimination, participants completed two subsequent behavioral tasks under display settings matching the fMRI environment.  
First, participants performed a same-different color discrimination task to estimate their Just Noticeable Difference (JND) thresholds.On each trial, participants saw a pair of colors and reported whether they were identical or different. Stimuli were transformed from CIEL\*a\*b\* space into polar coordinates to allow continuous interpolation along the hue angle. Thresholds were estimated using two interleaved 1-up/1-down adaptive staircases per color pair, terminating after eight reversals (Levitt, 1971). The task included eight color pairs selected based on RDM deviation analysis results: (1) three pairs showing significant difference in both deuteranopes and protanomalous compared to HC participants (Yellow-purple, Blue-purple, red-orange), (2) two pairs that significantly differed only in deuteranopes (Orange-yellow, Yellow-green), (3) two pairs that significantly differed only in protanomalous (Cyan-magenta, Green-blue), and (4) a control pair that did not differ significantly across any group(Red-cyan).   
Second, participants performed an 8-alternative forced-choice (8-AFC) color identification task. On each trial, a circular color patch was presented, and participants selected the matching hue from eight options identical to the fMRI stimulus set. 

- **Behavioral-neural concordance (TBA)**

Behavioral-neural concordance between RDM deviations and JND thresholds will be reported following completion of data collection.

## Filter design (TBA)

- Cone-gain model (Fig 2b.)  
- Fitting Criteria  
  - Loss function & Validation  
- Evaluation  
  - Permutation test

**Filter design**  
We modeled CVD color distortion as a cone-specific spectral shift (Δλ in nm) applied to the stimulus hue angles (Brettel et al., 1997). 

## Reproducibility

All analyses were conducted in Python 3.10 with numpy 1.24.3, scipy 1.11.3, scikit-learn 1.3.0, and BrainIAK 0.11. Random seeds were fixed (seed=42) for permutation tests and bootstrap resampling. Analysis code and preprocessing scripts are available at https://github.com/haba6030/colorBlind\_analysis. Anonymized preprocessed data are available upon reasonable request to the corresponding author.

## 

## Supplementary: Statistical Analysis

All tests used a significance threshold of α \= 0.05 with False Discovery Rate correction (Benjamini & Hochberg, 1995; q \= 0.05) applied to RDM color-pair comparisons (28 pairs per participant). Individual CVD participants were compared to the HC distribution using Crawford & Howell (1998) modified t-tests:

    t\* \= (x\_CVD − x̄\_HC) / (SD\_HC × √((n+1)/n)),  df \= n−1 \= 6

with one-tailed p-values testing the directional hypothesis that CVD disparity exceeds HC. Effect sizes were quantified via Hedges' g. Group-level permutation tests (10,000 iterations) were used for HC-CVD comparisons by permuting subject labels; color-level permutation tests (1,000 iterations) were used for LOCO/LORO validation by permuting color labels within subjects.

## References

Levitas, D., Hayashi, S., Vinci-Booher, S., Heinsfeld, A., Bhatia, D., Lee, N., Galassi, A., Niso, G., & Pestilli, F. (2024). ezBIDS: Guided standardization of neuroimaging data interoperable with major data archives and platforms. *Scientific Data*, 11, 179\. https://doi.org/10.1038/s41597-024-02959-0   
Greve, D. N., & Fischl, B. (2009). Accurate and robust brain image alignment using boundary-based registration. *NeuroImage*, *48*(1), 63–72. [https://doi.org/10.1016/j.neuroimage.2009.06.060](https://doi.org/10.1016/j.neuroimage.2009.06.060)  
Gower, J. C. (1975). Generalized procrustes analysis. Psychometrika, 40(1), 33–51.  
https://doi.org/10.1007/BF02291478  
Wang, L., Mruczek, R. E., Arcaro, M. J., & Kastner, S. (2015). Probabilistic maps  
of visual topography in human cortex. Cerebral Cortex, 25(10), 3911–3931.  
https://doi.org/10.1093/cercor/bhu277  
Haxby JV, Guntupalli JS, Connolly AC, Halchenko YO, Conroy BR, Gobbini  
MI, Hanke M, Ramadge PJ (2011) A common, high-dimensional model  
of the representational space in human ventral temporal cortex. Neuron  
72:404–416  
Guntupalli JS, Hanke M, Halchenko YO, Connolly AC, Ramadge PJ, Haxby  
JV (2016) A model of representational spaces in human cortex. Cereb  
Cortex 26:2919–2934.  
Freeman, W. T., & Adelson, E. H. (1991). The design and use of steerable filters. IEEE Transactions on Pattern analysis and machine intelligence, 13(9), 891-906.  
Jenkinson, M., Bannister, P., Brady, M., & Smith, S. (2002). Improved optimization for the robust and accurate linear registration and motion correction of brain images. *NeuroImage*, *17*(2), 825–841. https://doi.org/10.1016/s1053-8119(02)91132-8

Wang, L., Mruczek, R. E., Arcaro, M. J., & Kastner, S. (2015). Probabilistic Maps of Visual Topography in Human Cortex. *Cerebral cortex (New York, N.Y. : 1991\)*, *25*(10), 3911–3931. [https://doi.org/10.1093/cercor/bhu277](https://doi.org/10.1093/cercor/bhu277)

Wells, W.M., Viola, P.A., Atsumi, H., Nakajima, S., & Kikinis, R. (1996). Multi-modal volume registration by maximization of mutual information. *Medical image analysis, 1 1*, 35-51 .  
Golub, G. H., Heath, M., & Wahba, G. (1979). Generalized Cross-Validation as a Method for Choosing a Good Ridge Parameter. *Technometrics*, *21*(2), 215–223. [https://doi.org/10.1080/00401706.1979.10489751](https://doi.org/10.1080/00401706.1979.10489751)  
Nichols, T. E., & Holmes, A. P. (2002). Nonparametric permutation tests for functional neuroimaging: a primer with examples. *Human brain mapping*, *15*(1), 1–25. [https://doi.org/10.1002/hbm.1058](https://doi.org/10.1002/hbm.1058)  
Levitt, H. (1971). Transformed up-down methods in psychoacoustics. *Journal of the Acoustical Society of America, 49*(2, Pt. 2), 467–477. [https://doi.org/10.1121/1.1912375](https://psycnet.apa.org/doi/10.1121/1.1912375)