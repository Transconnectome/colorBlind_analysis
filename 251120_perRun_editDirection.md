현재 Per-run 코드와 참조 논문(B&H, 2009)는 아래와 같은 차이점을 지니고 있습니다. 이는 분석 결과에 큰 영향을 미칠 수 있으므로, 논문 과정에 부합하도록 수정을 요청합니다. 

1. 10 delay가 아닌 8 delay 사용
	•	논문: 12 s, 8 time points → TR 기준으로 8개의 FIR 샘플.
	•	현재 코드: FIR_DELAYS가 10개(예: 0~9 TR)라면, 창 길이/해상도가 논문과 다름.

Pseudocode:
# --- Step 1: Set FIR delays exactly as in B&H (8 delays) ---
FIR_DELAYS = np.arange(8)  # 0,1,2,3,4,5,6,7

2. optimal delay 계산이 아닌, 각 voxel 별 pseudo-inverse를 통한 HRF 계산
•	논문:
	•	1단계: 각 voxel에 대해 FIR design(8 delay)을 만들고
        → X⁺ * y_voxel로 voxel-wise HIRF 전체(time course) 추정.
	•	ROI 안에서 r² 높은 voxel만 골라 voxel HIRF들을 평균 → ROI 평균 HIRF.
	•	어떤 ‘optimal delay 하나’를 고르지 않고, 이 ROI HIRF 전체 모양을 그대로 basis function으로 사용.

•	현재 코드:
	•	FIR GLM으로 delay별 beta를 뽑은 뒤
	•	색/voxel을 평균해서 나온 universal_hrf에서 peak delay 한 칸만 선택해서,
	•	그 delay에서의 beta 하나만 “amplitude”로 사용.

따라서 논문과 깉이 각 voxel별 pseudo-inverse로 HRF 전체를 얻고, R^2을 기준으로 SNR이 높은 voxel만을 추출한 후, 그걸 ROI 평균 HRF로 써서 2단계 GLM을 진행하자. 
현재 코드는 FIR에서 얻은 HRF로부터 ‘단일 optimal delay’를 뽑아 그 시점의 beta만 amplitude로 쓴다.

Pseudo-code: 1단계(FIR deconvolution)를 별도로 구현해서 voxel-wise HIRF를 직접 추정해야 함.
# --- Step 1: voxel-wise FIR to estimate HRF h_v(t) ---  
for voxel v in ROI_voxels:
    y = fmri_timeseries[:, v]           # (T,)
    X_fir = build_FIR_design(onsets, FIR_DELAYS)  # (T, 8)
    h_v = pinv(X_fir) @ y               # (8,)
    HRF_voxel[v] = h_v

3. r^2 기준 상위 50프로 복셀만 이용
•	논문: r²(모델 적합도) 기준으로 ROI 내 voxel 상위 50%만 사용해서 ROI HIRF를 평균.
•	현재 코드: r² thresholding 없이, mask_img=roi_path로 정의된 voxel들을 전부 사용 (r² 기반 voxel selection 없음).

따라서 universal_hrf 계산 전에 voxel별 r² 계산 → 상위 50%만 골라서 평균하도록 확장해야 한다. 

Pseudo-code: universal HRF 계산 전에 voxel-wise r² 계산 → 상위 50%만 사용
# --- Step 2: Compute r² per voxel ---
for v in ROI_voxels:
    y = fmri_timeseries[:, v]
    y_pred = X_fir @ HRF_voxel[v]
    r2[v] = compute_r2(y, y_pred)

selected_voxels = voxels_with_r2_above_median(r2)

ROI_HRF = mean(HRF_voxel[v] for v in selected_voxels)
ROI_HRF_deriv = numerical_derivative(ROI_HRF)

4. amplitude 계산을 위한 2nd level GLM 진행: 각 run, color, voxel에 대해 HIRF와 onset을 convolve 하여 regression matrix 계산 후, fmri response에 대해 pseudoinverse 진행하여 amplitude beta 계산. 
즉, run, color, voxel 별 amplitude가 나타나야 함. 

•	논문의 2단계:
	1.	ROI 평균 HIRF h(t)와 그 derivative h'(t)를 사용.
	2.	8개의 색에 대해:
    	•	color_i_stick ⊗ h(t)  → 8개 컬럼
        •	color_i_stick ⊗ h'(t) → 8개 컬럼
            → 총 16개 컬럼짜리 design matrix X (T × 16).
	3.	voxel × run마다:
	    •	β = X⁺ y_voxel
	    •	앞 8개(=h 쪽)가 color별 amplitude, 뒤 8개(=h’ 쪽)는 latency/shape 오차 흡수용. derivative 계수는 최종 decoding에서는 버림.
	4.	voxel × run별로 color 8개 amplitude를 z-score.

•	현재 코드:
	•	비슷한 구조로 “각 run, 각 color, 각 voxel에 대해 amplitude 추정 + z-score”를 하고 있지만,
	•	2단계 GLM을 “HRF 전체 + derivative”로 다시 짜는 게 아니라, FIR GLM에서 이미 얻은 delay별 beta 중 하나(PEAK_DELAY)만 amplitude로 쓰는 방식입니다.
	•	그리고 derivative regressor를 두지 않는다는 점도 차이.

Pseudo code 각 run에 대해 X(16 columns)를 직접 생성, voxel별로 pinv(X) @ y 수행해 color-amplitude를 얻는 절차를 구현해야 한다.:
# --- Step 3: 2nd-level GLM for amplitude estimation (per run & voxel) ---
for run in runs:
    y_run = fmri_run[run]  # (T, n_voxels)

    # Build design matrix X (T, 16)
    X = []
    for color in 1..8:
        stick = stick_function(color_onsets[color])
        X.append(convolve(stick, ROI_HRF))
    for color in 1..8:
        X.append(convolve(stick, ROI_HRF_deriv))
    X = np.column_stack(X)

    # Amplitude estimation
    for v in selected_voxels:
        y = y_run[:, v]
        beta = pinv(X) @ y        # (16,)
        amp[v, run, :] = beta[:8] # 8 color amplitudes only

# z-score per voxel per run
amp_z = zscore(amp, axis=2)

5. ROI의 voxel들에 대한 공통 HRF 계산은 현재 코드에서도 모든 voxel에 대한 mean으로 color response 구현으로 나타나있기는 함, 단 HRF를 평균낸 것은 아니기에 필요시 수정 필요

•	현재 코드에서의 universal_hrf는
	•	“각 delay에서, 각 color의 contrast map → ROI voxel 평균 → 그걸 color들에 대해 평균”이므로
	•	결과적으로 delay별 평균 response curve라서, 사실상 “ROI 공통 HRF”와 비슷한 개념이긴 합니다.

•	다만 논문처럼
	•	(1) voxel-wise FIR HIRF → (2) r² 상위 voxel만 골라 평균하는 절차를 거친 건 아니고,
	•	color별 FIR beta를 먼저 추정한 뒤, 나중에 color와 voxel을 평균하는 방식이라 수학적으로 완전히 동일하진 않습니다.

그래서
	•	color 무시한 단일 FIR,
	•	voxel-wise HIRF,
	•	r² 기반 voxel selection,
	•	그 후 ROI 평균 HIRF”
를 추가로 구현해야 한다

pseudocode: color를 무시한 FIR → voxel-wise HRF → r² 기반 voxel selection → 평균 이 순서를 명확히 구현해야 함.

# unified summary
HRF_voxel[v] = pinv(X_fir_color_ignored) @ y_voxel
r2[v] = compute_r2(...)
selected_voxels = top50(r2)
ROI_HRF = average(HRF_voxel[selected_voxels])
ROI_HRF_deriv = gradient(ROI_HRF)