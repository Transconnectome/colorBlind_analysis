# Methods Section v1.2 (2026-04-06)

**Version**: Streamlined (filter-focused, main-only)  
**Word count**: 2,003 words (text) + 57 headers  
**Supplementary**: Moved to supplementary.tex  
**Changes from v1.1**: Removed supplementary sections to main text; cleaner structure

---

## Data collection

### Participants

Twelve volunteers were recruited under Institutional Review Board approval (\#2510/002-023), providing written informed consent prior to participation. Participants reported no history of neurological disorders. Color vision was assessed using the 14-plate Ishihara test [@ishihara1917]. Participants accurately identifying more than 12 plates were classified as Healthy Controls (HC; $n=7$, 3 females, age $22.7 \pm 2.5$ years), while those scoring below this threshold were classified as having Color Vision Deficiency (CVD; $n=2$, including one participant with deuteranomaly and one with protanomaly, both male). Three participants were excluded for failing to complete the experiment. Given the small CVD sample, all CVD results are interpreted as individual case demonstrations using @crawford1998 single-case statistics, not as population-level effects.

### fMRI experiment

We conducted an fMRI experiment to collect participants' voxel responses while perceiving colors. Stimuli consisted of eight colors equally spaced from 0° to 315° in Commission Internationale de L'Eclairage (CIE) $L^*a^*b^*$ space [@cie1986]. A gray filler was additionally included as a nonchromatic condition. Their lightness was fixed to $L^* = 75$ with an identical distance of 40 chroma from the gray point with $a^* = 0$, and $b^* = 0$ **(Fig 1A)**.

To maintain participants' attention and fixation, we conducted a modified 'Rapid Serial Visual Presentation' (RSVP) detection task [@brouwer2009] throughout each run. During the experiment, a circular patch was presented for 1.5 s. The patch contained one of the color stimuli or a gray point in a randomized order. The order of colors was optimized using the Neurodesign package [@durnez2018] to maximize design efficiency. 0.35s after stimulus onset, a set of alternating alphabets was presented for 0.4s each above the stimulus. Participants were instructed to press a button when an alphabet 'K' appeared consecutively. Such a target set emerged with a random probability of 0.33. Interstimulus intervals (ISIs) were randomly selected among 3s, 4.5s, and 6s. Each run included eight repetitions of the eight colors and a gray point. Each run lasted approximately 7min and each session consisted of six runs. The experiment was designed with the Psychopy 2022.2.5 package [@peirce2019].

To evaluate color display filter conditions, CVD participants underwent two sessions. While the first session utilized original stimuli in all runs, the second session consisted of two runs for each of three conditions: colors modified by the Windows filter, by the optimized filter and original stimuli. We compared neural responses of CVD participants under two filter conditions with the responses of HC participants to the original stimuli.

We acquired the MRI data focusing on the occipital lobe with a Siemens 3T MAGNETOM Cima.X Scanner with BioMatrix 3T coils. To constrain FOV to posterior occipital lobe, we set twenty-four oblique slices perpendicular to calcarine sulcus [@ryu2024]. The scanner was set as 1.5s TR, 30ms TE, 75° FA, $2 \times 2 \times 2$ mm voxel size, and $96 \times 80$ matrix size.

## Preprocessing and response estimation

### Spatial Normalization and registration

We converted the acquired data into BIDS format, and removed facial features using ezBIDS [@levitas2024]. Functional images were then registered to the T1w image. Coregistration was performed by optimizing a Mutual Information based (MI) cost function [@maes1997, wells1996] via FreeSurfer's mri\_coreg. This method is well suited to images with limited field-of-view (FOV) and obliquity because it does not require complete anatomical boundaries outside the acquired image. Image orientation was first initialized according to the scanner-defined obliquity information in the NIfTI header. The mutual-information cost function was then optimized to maximize the statistical dependence between T1w and BOLD intensity distribution within the overlapping region. T1w-to-MNI normalization was then performed using a 12-degrees-of-freedom affine transformation (FSL FLIRT; @jenkinson2002), followed by nonlinear warping (FNIRT; @andersson2007), yielding final BOLD data in MNI space at 2 mm isotropic resolution.

### ROI definition

Bilateral regions of interest (V1, V2, V3, and hV4; Fig. 1b) were defined in MNI space at 2 mm resolution using the Wang probabilistic atlas [@wang2015]. Bilateral ROIs were thresholded at 50\% atlas probability (following @wang2015) and intersected with each individual's BOLD brain mask. Voxel counts varied across ROIs (V1: $655 \pm 214$; V2: $451 \pm 145$; V3: $103 \pm 29$; hV4: $63 \pm 22$; all mean $\pm$ SD across subjects).

### FIR-based response estimation

Neural response amplitudes were estimated using a two-stage procedure: first extracting a hemodynamic response function (HRF) for each ROI via a finite impulse response (FIR) model, followed by a general linear model (GLM; @dale1999, brouwer2009, brouwer2013). This data-driven approach recovers a more accurate HRF than canonical models because the FIR model makes no assumption about HRF shape. In the first stage, we estimated the HRF of each ROI using an FIR model. Design matrices for each run were constructed with all stimulus onsets regardless of color identity. The FIR basis set spanned 8 TRs (12 s). The FIR beta weights were estimated by fitting the model to the preprocessed voxel time courses using linear regression. A mean ROI-level HRF was then obtained by averaging the FIR beta weights across voxels within each ROI. Voxels in the top 50\% of variance explained by this mean ROI-level HRF were retained, balancing signal quality with sample size (mean retained: V1 $328 \pm 107$, V2 $226 \pm 73$, V3 $52 \pm 15$, hV4 $32 \pm 11$ voxels).

In the second stage, a design matrix was constructed by convolving binary time courses for each color condition with the estimated ROI-specific HRF and its temporal derivative. The temporal derivative was included to capture voxel-to-voxel variability in HRF timing. This design matrix was then fitted to the preprocessed MNI-space voxel time courses using linear regression to estimate response amplitudes. Beta weights for the derivative regressors were discarded, and the remaining coefficients provided a single response amplitude estimate for each voxel, color, and run.

### Within-subject Procrustes alignment

To improve cross-run consistency in voxel response patterns within each participant, voxel response amplitudes were aligned across runs using Procrustes alignment [@gower1975]. This preprocessing reduces measurement noise across runs while preserving color representational geometry, thereby improving the quality of subsequent SRM fitting. To preserve structural representations, voxel response amplitude matrices (across all colors) from runs 2--6 were aligned to run 1, selected as reference to maintain temporal ordering consistency, by estimating an orthogonal transformation that minimized the residual error (Equation 1). To preserve voxel response amplitude magnitudes, scaling was prohibited. To evaluate whether alignment improved cross-run consistency while preserving stimulus-related structure, we computed the mean pairwise Pearson correlation of voxel response amplitude patterns across all run pairs (15 comparisons). Average correlation improved from $r = 0.54$ (SD = 0.12) before alignment to $r = 0.71$ (SD = 0.09) after alignment, indicating improved cross-run consistency.

$$
X_{aligned} = XQ
$$

where $X \in \mathbb{R}^{n_{voxels} \times n_{colors}}$ is the amplitude matrix for a given run, $X_{ref} \in \mathbb{R}^{n_{voxels} \times n_{colors}}$ is the reference matrix, and $Q \in \mathbb{R}^{n_{voxels} \times n_{voxels}}$ is the orthogonal matrix minimizing $\|X_{ref} - XQ\|_F$.

## Functional Alignment and shared representational space

### Construction of HC-derived common space with Shared Response Model

After within-subject Procrustes alignment, cross-subject alignment was performed using shared response modeling (SRM; @chen2015), a dimension-reduction technique related to hyperalignment [@haxby2011, guntupalli2016]. This enabled comparison of color representations in a common space across participants with different numbers of voxels. SRM learns a low-dimensional common space $S$ where between-subject variability is minimized. We utilized the Brain Imaging Analysis Kit package (BrainIAK) for SRM implementation.

SRM estimates linear mappings between each participant's original voxel space and the common space. For participant $i$, let $X_i \in \mathbb{R}^{v \times c}$ denote the matrix of fMRI response amplitudes, where $v$ is the number of voxels in the ROI and $c = 8$ colors. SRM estimates a common space $S \in \mathbb{R}^{k \times c}$ and participant-specific mappings relating each $X_i$ to that space, where $k$ is the reduced dimension.

$$
X_i = W_i S + E_i
$$

$$
\min_{W_i, S} \sum_{i=1}^N \|X_i - W_i S\|_F^2 \quad s.t. \quad W_i^T W_i = I_k
$$

In equation 3, $W_i \in \mathbb{R}^{v \times k}$ is the orthogonal mapping matrix mapping participant $i$'s voxel space to the common space, and $E_i$ is the residual error. The matrix $W_i$ is optimized to minimize the sum of Frobenius norm of residuals across all participants. The orthogonal constraint ($W_i^T W_i = I_k$) helps preserve geometric relationships between colors---distances and angles---in the common space. To establish an HC-derived reference common space, we fitted SRM using voxel response data from the seven HC participants only. CVD participants were subsequently projected into this fixed space by computing $W_{CVD} = U V^T$, where $U \Sigma V^T = SVD(X_{CVD} \cdot S^\dagger)$, yielding an orthonormal mapping that best aligned CVD data to the HC-derived space without re-estimating $S$.

To identify which color pairs showed geometric deviations in CVD, we computed the representational dissimilarity matrix (RDM) for each of all 28 color pairs in the common space using correlation distance (1 - Pearson r), which captures pattern similarity while being robust to amplitude scaling and additive offsets. To identify pairs exhibiting significant deviation, we computed element-wise differences between each CVD participant's RDM and the mean HC RDM, evaluating significance via 95\% bootstrap confidence intervals (1,000 iterations, resampling HC participants with replacement). The reduced dimension $k$ was set to: V1 $k = 4$; V2 $k = 4$; V3 $k = 3$; hV4 $k = 3$.

## Color decoding and voxel response prediction model

### Forward Encoding Model

We modeled hue-selective neural populations using half-wave rectified and squared sinusoidal basis functions following @brouwer2009 and @brouwer2013 (**Fig 2a**). Each of six hypothetical channels was tuned to a preferred hue $\theta_k$ evenly spaced around the hue circle, with response profile $r_k(\theta) = \max(0, \cos(\theta - \theta_k))^2$. The squaring operation sharpens the tuning profiles and introduces higher-order harmonic components, requiring multiple phase-shifted channels to fully span the circular hue space. Six channels provide a complete basis set, allowing any hue-selective tuning curve to be expressed as a weighted sum of the basis functions [@freeman1991].

This forward model formalizes how hypothetical color channels map to observed voxel responses: each voxel's response $B$ is modeled as a weighted sum of six channel outputs $C$, where the weight matrix $W$ represents the brain's mapping from hue-selective population activity to measured BOLD signals (Equation 4).

$$
B = W C
$$

Training and evaluation were conducted using cross-validations. Preprocessed response data, represented either in voxel space or in the SRM-derived shared-space, were partitioned into training ($B_1$, $C_1$) and test sets ($B_2$, $C_2$). During training, the weight matrix $W$ was estimated via ridge regression (Equation 5), where the regularization parameter $\alpha$ was selected via generalized cross-validation (GCV; @golub1979). Once $W$ was estimated, channel outputs were decoded from test voxel responses (Equation 6a), or voxel responses were predicted from channel outputs (Equation 6b). Decoded channel outputs $\hat{C}$ were converted to hue angle estimates by finding the angle $\theta$ that minimized $\|\hat{C} - C(\theta)\|_2$.

$$
\hat{W} = B_1 C_1^T (C_1 C_1^T + \alpha I)^{-1}
$$

$$
(color decoding) \quad \hat{C} &= (\hat{W}^T \hat{W})^{-1} \hat{W}^T B_2 \\
(voxel prediction) \quad \hat{B} &= \hat{W} C_2
$$

### Cross-validation: discrimination vs interpolation

To dissociate color discrimination from continuous hue-space interpolation, we evaluated the forward model using two complementary cross-validation schemes.

**Leave-one-run-out (LORO)** tested whether individual colors could be reliably distinguished from voxel responses, assessing discrimination consistency across stimulus repetitions. For each of six runs, the corresponding response matrices ($B$, $C$) were held out as the test set, $W$ was trained on the remaining five runs, and voxel responses were predicted (Equation 6b).

**Leave-one-color-out (LOCO)** tested whether the model could interpolate to novel hues not seen during training, assessing the preservation of continuous color-space geometry. For each color, all six run response matrices of the target color were held out. $W$ was trained on the remaining seven colors, and voxel responses to the held-out color were predicted (Equation 6b).

Both were evaluated using Pearson correlation between predicted and observed response vectors, computed across all voxels and test samples. LORO performance indicates color discriminability, while LOCO performance reflects the intactness of continuous hue-space geometry.

## Behavioral-neural concordance

### Behavioral tasks

To examine the relationship between geometrical deviations in neural representations and perceptual color discrimination, participants completed two subsequent behavioral tasks under display settings matching the fMRI environment.

First, participants performed a same-different color discrimination task to estimate their Just Noticeable Difference (JND) thresholds. On each trial, participants saw a pair of colors and reported whether they were identical or different. Stimuli were transformed from CIE$L^*a^*b^*$ space into polar coordinates to allow continuous interpolation along the hue angle. Thresholds were estimated using two interleaved 1-up/1-down adaptive staircases per color pair, terminating after eight reversals [@levitt1971]. The task included eight color pairs selected based on RDM deviation analysis results: (1) three pairs showing significant difference in both deuteranopes and protanomalous compared to HC participants (Yellow-purple, Blue-purple, red-orange), (2) two pairs that significantly differed only in deuteranopes (Orange-yellow, Yellow-green), (3) two pairs that significantly differed only in protanomalous (Cyan-magenta, Green-blue), and (4) a control pair that did not differ significantly across any group (Red-cyan).

Second, participants performed an 8-alternative forced-choice (8-AFC) color identification task. On each trial, a circular color patch was presented, and participants selected the matching hue from eight options identical to the fMRI stimulus set.

## Filter design

We modeled CVD color distortion as a cone-specific spectral shift ($\Delta\lambda$ in nm) applied to the stimulus hue angles [@brettel1997]. The filter parameters were optimized to minimize the discrepancy between CVD neural responses to filtered stimuli and HC responses to original stimuli. Validation was performed using both RDM convergence and V4 LOCO performance as dual criteria.

## Reproducibility

All analyses were conducted in Python 3.10 with numpy 1.24.3, scipy 1.11.3, scikit-learn 1.3.0, and BrainIAK 0.11. Random seeds were fixed (seed=42) for permutation tests and bootstrap resampling. Analysis code and preprocessing scripts are available at [https://github.com/haba6030/colorBlind_analysis](https://github.com/haba6030/colorBlind_analysis). Anonymized preprocessed data are available upon reasonable request to the corresponding author.
