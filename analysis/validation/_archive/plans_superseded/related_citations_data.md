제공된 문헌들을 바탕으로 요청하신 5가지 핵심 주제를 정리해 드립니다.

### 1. RSA의 실패 가능성 (Low RDM Correlation의 해석)
낮은 RDM 상관관계가 반드시 해당 뇌 영역에 표상 정보(signal)가 부재함을 의미하는 것은 아닙니다. 문헌들은 이를 데이터의 품질 한계나 가정의 위반으로 해석할 수 있음을 시사합니다.

*   **노이즈에 의한 상한선 (Noise Ceiling):** 데이터 자체에 측정 노이즈가 많다면, 아무리 완벽한 모델이라도 뇌 데이터와의 상관관계(RDM correlation)가 낮게 나올 수밖에 없습니다. 따라서 RDM 상관관계가 낮더라도 그것이 **노이즈 천장(noise ceiling)**에 도달했다면, 신호가 없는 것이 아니라 현재 데이터 수준에서 설명 가능한 최대치를 달성한 것으로 해석해야 합니다.
*   **측정 및 샘플링의 한계:** 개별 뉴런의 활동이 복셀 단위로 평균화(averaging)되는 과정이나, 복셀 간의 공간적 불일치 등은 실제 존재하는 미세한 패턴 정보를 왜곡하거나 약화시켜 RSA의 감도를 떨어뜨릴 수 있습니다.

### 2. RDM 계산 시 Procrustes 등 Alignment의 필요성
해부학적 정렬만으로는 개인 간의 미세한 기능적 차이를 극복하기 어려우며, 이를 해결하기 위해 기능적 정렬(Functional Alignment)이 필수적입니다.

*   **해부학적 정렬의 한계:** 뇌의 거시적인 해부학적 구조를 맞추더라도, 미세한 기능적 지형(fine-scale topography)은 개인마다 고유하고 불규칙(idiosyncratic)합니다. 따라서 해부학적 정렬만으로는 공통된 정보 패턴을 포착하는 데 실패할 수 있습니다.
*   **Vector Geometry의 보존 및 회복:** Hyperalignment(주로 Procrustes 방식)는 고차원 공간에서 각 피험자의 반응 패턴 벡터들 간의 기하학적 관계(vector geometry)를 보존하면서 회전(rotation)을 통해 공통 공간으로 정렬합니다. 연구 결과, Hyperalignment를 적용했을 때 해부학적 정렬 대비 피험자 간 상관관계(ISC)와 정보의 신뢰도(reliability)가 유의미하게 향상되었으며, 이는 정렬이 잘못된 매칭에 의해 가려졌던 실제 신호를 회복(recover)시킴을 의미합니다.

### 3. Noise Ceiling의 의의와 계산 방법
**Nili et al. (2014)**은 모델 성능 평가의 절대적인 기준점으로 노이즈 천장(Noise Ceiling)을 제시합니다.

*   **의의:** 관측된 RDM 상관관계 값이 절대적으로 낮더라도(예: 0.1), 노이즈 천장이 그만큼 낮다면 해당 모델은 데이터를 훌륭하게 설명하고 있는 것입니다. 반대로 천장이 1보다 현저히 낮다면, 실험 데이터의 노이즈가 심하거나 데이터 양이 부족하여 실험의 민감도가 떨어짐을 시사합니다.
*   **계산 방법:** 실제 모델(True Model)의 성능 범위를 추정하기 위해 상한과 하한을 계산합니다.
    *   **상한 (Upper Bound):** 각 피험자의 RDM과 전체 그룹 평균 RDM 간의 상관관계를 계산하여 평균 냅니다. 이는 실제 모델 성능을 과대평가(overfitting)하는 경향이 있습니다.
    *   **하한 (Lower Bound):** 'Leave-one-subject-out' 방식을 사용하여, 한 피험자의 RDM과 나머지 피험자들의 평균 RDM 간의 상관관계를 계산합니다. 이는 실제 모델 성능을 과소평가(underestimation)하는 경향이 있어 보수적인 기준이 됩니다.

### 4. Procrustes와 SRM (Shared Response Model) 비교
두 방법 모두 다피험자 데이터를 공통 공간으로 정렬하지만, 수학적 접근과 차원 축소 여부에서 차이가 있습니다.

*   **Procrustes (Hyperalignment):** 주로 결정론적(deterministic) 방법으로, 피험자의 데이터 차원(복셀 수)을 유지하면서($k=v$) 벡터 기하학을 보존하는 '회전' 행렬을 찾습니다.
*   **SRM:** 확률적 생성 모델(probabilistic generative model)로, 데이터를 공유된 반응(Shared response)과 개별 노이즈로 분해합니다. 핵심 차이점은 **차원 축소**입니다. SRM은 복셀 수보다 적은 수의 특징($k < v$)을 추출하여 노이즈를 제거(denoising)하는 효과가 있으며, 종종 Procrustes보다 높은 디코딩 성능을 보입니다. 이는 SRM이 개인 고유의 기하학적 형태를 일부 왜곡하더라도 공유된 정보를 더 효과적으로 필터링하기 때문입니다.

#### SRM의 기하학적 구조 보존에 대한 수학적 증명 (Mathematical Detail)

제공된 문헌, 특히 **Chen et al. (2015)**의 원저 논문과 **Haxby et al. (2020)**의 리뷰를 바탕으로 SRM(Shared Response Model)이 어떻게 기하학적 구조(geometry)를 보존하는지 수학적으로 설명해 드립니다.

SRM이 기하학적 구조를 보존한다는 것은, **공유된 저차원 공간($S$)에서의 벡터 간 거리(또는 관계)가 개별 피험자의 고차원 복셀 공간($X_i$)으로 투영될 때 그대로 유지됨(Isometry)**을 의미합니다. 이를 수학적으로 증명하는 핵심은 SRM이 제약 조건으로 두는 **$W_i$의 직교성(Orthonormality)**에 있습니다.

##### 1. SRM의 수학적 정의 (Mathematical Definition)

**Chen et al. (2015)**에 따르면, SRM은 피험자 $i$의 fMRI 데이터 $X_i$ (복셀 수 $v \times$ 시간 $d$)를 다음과 같이 모델링합니다:

$$ X_i = W_i S + E_i $$

여기서:
*   $S \in \mathbb{R}^{k \times d}$: 모든 피험자가 공유하는 반응(shared response) 또는 잠재 특징(latent features). ($k$: 특징의 수, $d$: 시간)
*   $W_i \in \mathbb{R}^{v \times k}$: 공유 공간 $S$를 피험자 $i$의 복셀 공간으로 매핑하는 개별 기저(subject-specific basis).
*   $E_i$: 개별 노이즈.

SRM의 핵심 제약 조건은 개별 기저 $W_i$가 **직교(orthonormal) 행렬**이어야 한다는 것입니다:

$$ W_i^T W_i = I_k $$
($I_k$는 $k \times k$ 단위 행렬)

##### 2. 기하학적 구조 보존의 수학적 증명 (Proof of Geometry Preservation)

기하학적 구조가 보존된다는 것은 공유 공간($S$) 상의 두 시점(또는 자극) $t_1$과 $t_2$ 사이의 유클리드 거리가, 피험자의 복셀 공간($X_i$)으로 변환된 후에도 동일하게 유지됨을 의미합니다.

공유 공간의 두 벡터를 $s_1, s_2$라고 하고, 이를 피험자 공간으로 투영한 벡터를 $x_1, x_2$ (노이즈 $E_i$ 제외한 설명되는 부분)라고 할 때:
$$ x_1 = W_i s_1, \quad x_2 = W_i s_2 $$

두 벡터 사이의 거리의 제곱(Squared Euclidean Distance)을 계산하면 다음과 같습니다:

$$
\begin{aligned}
\| x_1 - x_2 \|^2 &= \| W_i s_1 - W_i s_2 \|^2 \\
&= \| W_i (s_1 - s_2) \|^2 \\
&= (s_1 - s_2)^T W_i^T W_i (s_1 - s_2)
\end{aligned}
$$

여기서 SRM의 제약 조건인 $W_i^T W_i = I_k$를 대입하면:

$$
\begin{aligned}
&= (s_1 - s_2)^T I_k (s_1 - s_2) \\
&= (s_1 - s_2)^T (s_1 - s_2) \\
&= \| s_1 - s_2 \|^2
\end{aligned}
$$

**결론:**
$$ \| x_1 - x_2 \| = \| s_1 - s_2 \| $$

즉, **개별 기저 $W_i$를 통한 변환은 등거리를 유지하는 변환(Isometric embedding)**입니다. 따라서 공유 공간 $S$에서 형성된 자극 간의 기하학적 관계(representational geometry)는 왜곡 없이 개별 피험자의 뇌 공간으로 매핑됩니다. 이것이 SRM이 기하학적 구조를 보존한다고 말하는 수학적 근거입니다.

##### 3. 확률적 모델 관점에서의 보존 (Probabilistic Perspective)

**Chen et al. (2015)**은 이를 확률적 생성 모델(Probabilistic Generative Model)로 확장하여 설명합니다.

$$ x_{it} \sim N(W_i s_t + \mu_i, \rho_i^2 I) $$

*   여기서 $s_t$는 시간 $t$에서의 공유된 반응 벡터입니다.
*   SRM은 관측된 데이터 $X_i$에서 노이즈($E_i$)를 제거하고, 모든 피험자에게서 공통적으로 나타나는 "진정한" 기하학적 구조인 $S$를 찾아내는 과정입니다.
*   **Haxby et al. (2020)**은 이 과정이 정보의 내용(content)인 벡터 기하학(vector geometry)을 보존하면서, 이를 담고 있는 개별적인 신경 반응 프로파일(tuning profiles)을 재혼합(remixing)하는 과정이라고 설명합니다.

##### 4. Procrustes와의 차이점 (Dimensionality Reduction)

수학적으로 Procrustes(Hyperalignment)와 SRM 모두 직교 변환($R^T R = I$ 또는 $W^T W = I$)을 사용하므로 기하학적 구조를 보존합니다. 하지만 차이점은 **차원($k$)**에 있습니다.

*   **Procrustes:** $k = v$ (복셀 수와 동일). 전체 공간을 회전(rotation)만 시킴.
*   **SRM:** $k < v$ (복셀 수보다 작음). 저차원 공유 공간으로의 투영을 통해 노이즈를 제거(denoising)하고 주성분을 추출함.

**Chen et al. (2015)**의 실험 결과(Fig 1)에 따르면, SRM은 $k$를 줄임으로써 데이터에 내재된 본질적인 기하학적 구조를 더 잘 포착하고, 테스트 데이터에 대한 일반화 성능(accuracy)을 높입니다. 이는 단순히 거리를 보존하는 것을 넘어, 노이즈를 걸러내어 **"신뢰할 수 있는 기하학적 구조"**를 보존함을 의미합니다.

### 5. 신뢰도 저하에 따른 Diedrichsen et al. (2016)의 대처 방법
**Diedrichsen et al. (2016)**은 RDM의 신뢰도가 낮거나 편향(bias)이 발생하는 문제를 해결하기 위해 통계적으로 엄밀한 거리 측정법을 제안합니다.

*   **교차 검증된 마할라노비스 거리 (Cross-validated Mahalanobis distance / LDC):** 노이즈는 거리 추정치를 양의 방향으로 편향(positive bias)시킵니다. 이를 해결하기 위해 데이터를 독립적인 파티션(예: run)으로 나누어 교차 곱(cross-product)을 통해 거리를 계산함으로써, 기대값이 0이 되는 비편향 추정치(unbiased estimate)를 얻습니다.
*   **다변량 노이즈 정규화 (Multivariate Noise Normalization):** 복셀 간의 노이즈가 공간적으로 상관관계(spatial correlation)를 갖는다는 점을 고려하여, 공분산 행렬($\Sigma$)을 추정해 데이터를 '백색화(pre-whitening)'합니다. 이때 샘플 수가 부족하여 공분산 행렬을 정확히 구하기 어려운 문제를 해결하기 위해 **축소 추정량(shrinkage estimator)**을 사용하여 정규화(regularization)합니다.
