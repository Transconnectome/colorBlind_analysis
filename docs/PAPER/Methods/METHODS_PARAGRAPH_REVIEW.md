# methods_v2.tex — 문단별 검토 (roast)

> **작업 방식**: 첫 문단부터 순서대로 `수정안 제안 → 확인·피드백 → 개선 → 수락 후 적용`.
> 해결된 문단은 이 파일에서 **삭제**한다. 이 파일에 남아 있는 항목 = 미해결.
>
> **적용 기준** (이 세션에서 합의된 것)
> - 두괄식: Results식 BLUF가 아니라 **정의·결정을 먼저, 근거를 나중에**. 배경·목적절로 시작하는 것 자체는 장르 표준이므로 허용. 문제는 **문단의 결정이 끝에 묻히는 경우**.
> - 부정 표현: 문헌 관행상 정상인 부정형은 유지. 평가적·자기폄하 표현만 교체.
> - 문장 길이 35단어 이하 지향, 콜론·세미콜론·삽입구 최소화.
> - 용어 스킴: 범주=`color classification`(측정)/`decodable`(피험자 측), 연속=`hue interpolation`, 전역기하=`Procrustes disparity`, 국소기하=`per-pair RDM difference (ΔRDM)`, 행동=`hue discrimination`(JND 전용).
> - 미국식 철자. (본문 tex 완료)
>
> **범례**: 🔴 수정 필요 · 🟡 사실 확인 필요(코드·데이터 대조) · ⛔ 저장소 밖 자산이라 여기서 해결 불가
>
> 줄번호는 편집에 따라 밀린다. 각 항목의 인용문으로 찾을 것.

---

## 우선 처리 대상 (문단 순서와 무관하게 무거운 것)

| # | 위치 | 내용 |
|---|---|---|
| ~~A~~ | ~~P37 Grid search~~ | ✅ **해결 (2026-08-05).** 실제 격자 = `two_comp.py:47-48` `BS_GRID=arange(0,50,2)`(26) × `BC_GRID=arange(-50,50,2)`(51) = **1,326셀**. β_s 하한 0이 격자에 구현되어 있어 제약과 모순 없음. R+C `rc_1dof.py:26` g∈[0,3] step 0.05 (61점). 본문 반영 완료 |
| **C-1** | P10 전처리 | 🔴 **분석 데이터에 HMC·STC·SDC 미적용.** `run_full_dataset_C010.py:29` → `fmriprep_out_method3_header_mi` = `run_method3_header_mi_all_subjects.sbatch`가 **원본 BIDS BOLD**를 applywarp로 MNI에 얹은 출력. 별도로 **진짜 fMRIPrep 산출물이 존재**(`data/sub-01/func/*desc-hmc_xfm.txt` 실측 per-volume ITK affine, `*_desc-preproc_bold.json` → `SliceTimingCorrected: true`, `figures/*fieldmap.svg`). 즉 두 전처리가 병존하고 논문 결과는 후자를 쓰지 않음. **결정: Candidate A (method3 + HMC) 재산출.** 사전 확정 문서 `analysis/phase0_preprocessing/HMC_REANALYSIS_PRESPEC.md`. 스크립트 업로드·preflight 완료(exp1 240/240, exp2 64/64). 본문 S17 문장은 재산출 결과로 교체 예정 |
| ~~C-2~~ | ~~Supp S1~~ | ✅ **해결.** MCFLIRT 실측 FD(0.32±0.04 mm, FD>0.5 mm 16.2%) 수록 + 정렬본 미사용 명시. `power2012` bib 추가 |
| ~~D~~ | ~~P11 ROI~~ | ✅ **해결.** C010은 voxel selection 미적용. `No further functional voxel selection was applied.` 추가 완료 |
| ~~E~~ | ~~P03 Participants~~ | ✅ **해결.** sub-10 = 군 입대로 2차 세션 불참 → 중도탈락. 문안: "three did not complete the first scanning session, and a fourth completed it but became unavailable for the filter-evaluation session". CVD 연령 24/25 반영 |
| ~~F~~ | ~~P17/P18~~ | ✅ **해결 (2026-08-05).** 차원 표기는 정확했음(`W (K,V)`, `channel_resp = W @ X.T`). 실제 오류는 "and inverted it" — 의사역행렬은 **C에** 적용되고 W는 역행렬을 취하지 않음. 디코딩이 360-way라는 사실과 exact accuracy의 45° 반올림 규칙 추가. `nearest-neighbor matching` 2곳 → `correlation readout` |
| ~~G~~ | ~~P22~~ | ✅ **해결.** MW는 귀무 결과(p=0.668)이므로 검정 유지, 비독립성 공개 문장 추가 + 40단어 문장 분해 |

---

## P02 — Figure 1 캡션

- ⛔ 그림 이미지 안의 Panel C 헤더가 **"Modelling & Filter"** (영국식). 래스터이고 저장소에 생성 스크립트 없음 → 외부 원본 수정 후 재출력 필요. tex 캡션 쪽은 이미 `Modeling`으로 수정됨
- 🔴 `rapid serial visual presentation (RSVP)`를 캡션에서 확장하고 P05에서 **또 확장**. 캡션은 순서대로 읽히지 않으므로 정의 위치로 부적절 — 본문 P05를 정의 위치로 삼고 캡션은 약어만 사용
- 🔴 캡션이 SRM·RDM을 본문 정의보다 먼저 사용 (SRM은 여기가 최초 등장, 확장은 P15)
- CVD 표본수가 캡션에 없음 (`HC: n = 7`만 표기)

---

## P03 — Participants

- 세미콜론 2개. 마지막 문장 `…modified $t$-test; no population-level inference is made.` → 두 문장 분리 가능
- `were classified as` — **유지 결정됨** (2026-08-05)

---

## P05 — RSVP 과제 문단

- 🔴 48단어 문장: `Because the schedule was optimized for detection power rather than for equal counts, trials were not balanced across colors within a run: …` — 콜론 1개 포함. 부정형 자체는 문헌 관행상 유지 가능하나 길이는 분해 필요
- 🔴 43단어 문장: `The same optimized schedule was used for every participant, so … ; single-trial amplitudes were subsequently averaged …` — 세미콜론으로 두 독립절 연결
- 🔴 `two consecutive 'K's` — LaTeX 직선 따옴표. `` `K's `` 로 고쳐야 좌우 따옴표가 맞음
- `comprised`가 두 문장에서 반복 (`Each run comprised 72 events` / `Each session comprised six runs`)

---

## P08 — 8AFC

- 🔴 `It was compared to the Ishihara screening outcome post-hoc.` — "compared"의 조작적 정의가 없음. 통계도 지표도 제시되지 않음. 무엇을 어떻게 비교했는지 한 절 필요

---

## P09 — MRI 획득

- slice gap, multiband/SMS factor, 위상 부호화 방향 미기재

---

## P10 — 전처리

- 🔴 **C-1 참조.** 움직임 보정·slice-timing·왜곡 보정 미적용 사실과 그 QC 수치 미기재. MCFLIRT FD는 산출 완료 (`results/motion_qc_summary.json`: 분석 9명 mean FD 0.318±0.044 mm, HC 0.313 / CVD 0.338, FD>0.5 mm 16.2%)
- 🔴 **평활화(smoothing) 여부 미기재.** MVPA 논문은 "spatial smoothing was not applied" 를 명시하는 것이 관행 (Kuriki, Shim 등 선행 논문 모두 명시)

---

## P11 — ROI 정의

- 🔴 46단어 문장에 세미콜론 4개 (voxel count 나열). 표로 빼거나 문장 분리

---

## P12 — 반응 추정 (two-stage GLM)

- FIR 8-TR 기저에서 추출한 ROI 수준 HRF를 전 복셀에 공통 적용하는 근거 미기재 (추정기 `ridge`→`OLS` 정정 및 미분·drift 회귀자 명시는 완료)

---

## P15 — SRM 학습

- 🔴 41단어 문장, 세미콜론 3개 + 콜론 1개 (k값 나열)
- `to avoid circular inference` — 유지 가능. 대안: `so that CVD comparisons remain out-of-sample`

---

## P17 / P18 — 디코딩·인코딩

- 🔴 P18 `Regularization is warranted because … would otherwise overfit $W$ and degrade prediction` — 정당화 프레이밍. → `Ridge regularization stabilizes $W$ under eight stimuli and correlated channels, improving held-out prediction`
- `imposes no spatial structure on the voxels` — **유지** (smooth Tikhonov 기각 이력과의 구분에 필요)

---

## P20 — 두 디코딩 스킴 도입

- 🔴 `measured as color classification` / `measured as hue interpolation` — 표상을 과제 이름"으로" 측정한다는 표현. → `quantified by color-classification accuracy` / `by hue-interpolation accuracy`
- `the continuous representation`이 생략적 (무엇의 연속 표상인지)

---

## P21 — LORO

- 🔴 `Primary classification performance was the 8-class exact accuracy` — 계사 불일치(performance ≠ accuracy). → `was quantified as`
- 🔴 **같은 지표에 이름 4종**: `8-class exact accuracy`(여기) / `eight-way accuracy`(Results, S16) / `categorization accuracy`(supplementary_content) / `LORO classification accuracy`. 하나로 통일

---

## P24 — Adjacent accuracy

- 🔴 54단어 문장. 괄호 안에 세미콜론 2개와 등식 3개가 중첩: `(range 0--1; chance … = 3/8 = 0.375; exact-accuracy chance = 1/8 = 0.125)`

---

## P25 — Vulnerability profile

- 🔴 `For group-level model fit, we report Spearman ρ…` — CVD가 2명인데 "group-level"이 무엇을 가리키는지 불명
- `(one-tailed, uncorrected)` 8회 검정 — 공개되어 있으므로 유지, 다만 Results와 보정 정책 일치 확인

---

## P27 — Procrustes disparity

- 🔴 **문단의 결정이 마지막 문장에 있음.** "all-HC가 primary, 대칭 LOSO는 sensitivity"를 첫 두 문장 안으로 올려야 함. 현재는 6번째 문장에 가서야 추정치가 둘이라는 사실이 드러남
- 🔴 **7 fold 평균이라는 사실이 본문에 없음.** CVD 값은 7개 LOO 기준에 대한 평균인데 서술되지 않음
- 마지막 문장 세미콜론 1개

---

## P30 — Figure 5 캡션

- ⛔ 그림 이미지 안에 영국식 철자 3개: `personalised`, `Behavioural`, `parameterised`. 생성 스크립트(`Figures/scripts/phase2/generate_fig5_pipeline.py`)는 현재 미사용 → 이미지 자산 자체를 교체해야 함
- 🔴 47단어, 콜론 1개 + 세미콜론 1개
- `only the LOCO loss couples to the forward encoder` — `only` 유지(정밀 한정)

---

## P31 — Candidate Model 1 (R+C)

- 🔴 **문단의 핵심 사양이 마지막 문장에 평가형으로 있음.** "자유 파라미터 1개, 왜곡이 단일 축에 갇힘"이 독자가 먼저 알아야 할 정보
- 🔴 `R+C can only displace colors along this single direction and cannot account for distortions in other color directions` — 경쟁 모델에 대한 평가. Methods에서는 범위 진술로: `R+C therefore spans a one-dimensional family of hue displacements, all lying along the confusion axis.`
- 🔴 61단어 문장(첫 문장군), 49단어 문장(`The gain g parameterizes cortical compensation: … ; … ; …`) — 콜론 1 + 세미콜론 2로 3분기
- `confusion axis` 정의가 문단 끝에서 두 번째에 있으나, 용어 최초 등장은 Fig 5 캡션 → 정의를 최초 사용 지점으로

---

## P32 — Candidate Model 2 (2-comp)

- 🔴 `a weak directional prior that fixes only the sign, not the magnitude, of the S-cone-axis term` — 자기폄하 + 3중 한정. → `β_s ≥ 0 fixes the sign of the S-cone term and leaves its magnitude free.`
- 🔴 **`\citeNP{emery2021}` 렌더링 오류.** 문장 끝 괄호 없는 인용이라 "…confusion loci Emery et al. 2021."로 출력됨 → `\cite`
- 🟡 Methods가 Results를 전방 참조 (`\S\ref{sec:results:loco}`, `\S\ref{sec:results:geometry}`). 대상 저널 스타일 확인
- 54단어 문장, 세미콜론 2개

---

## P35 — L_RDM

- 🔴 **정의가 두 번째 문장에 있음.** 손실함수 문단은 첫 문장이 정의여야 하고, 세 손실 문단(L_γ·L_RDM·L_LOCO)이 서로 다른 형태로 시작해 병렬이 깨져 있음
- 🔴 **논리 겹침**: "a simulated difference is obtained by applying δθ … **and comparing it to** the observed ΔRDM" — 비교는 산출 절차가 아니라 손실 그 자체
- **제안**: `L_RDM is the cosine dissimilarity between the observed and simulated ΔRDM, taken over the 28 upper-triangle elements. The simulated difference follows from applying the candidate δθ to the HC mean RDM.`

---

## P36 — L_LOCO

- 🔴 **문단 제목과 본문이 다른 구성개념**: 제목 `hV4 LOCO voxel-prediction` vs 본문 `hue interpolation`. → `hV4 interpolation-profile loss`
- 🔴 `records where each CVD participant's hue interpolation breaks down` — 비격식. → `records per-hue interpolation accuracy`
- 🔴 정의 선행 필요 (P35와 동일 템플릿)

---

## P39 — Gate 1

- 🔴 `Only loss atoms where … were admitted. Admission required …; atoms failing this gate were excluded from combination.` — 한 문단에 3중 부정. → `Loss atoms qualified when the CVD loss exceeded the HC LOO distribution in the predicted direction (signed Cohen's d ≥ +0.5). The remainder were withheld from combination.`

---

## P41 — Gate 3

- 🔴 **`the modal 45° bin`이 미정의.** 45° 빈이 무엇인지 앞에서 도입된 적 없음
- 🔴 매우 긴 단일 문단(7문장). 주 기준/부 기준/보조 지표를 구분하는 구조가 산문에 묻힘
- `The HC false-positive rate was not itself used as a selection criterion` — **유지 필수** (프로젝트 정책: specificity는 descriptive-only)

---

## P42 — Identifiability and recovery

- 🔴 **(1)~(4)를 `itemize`로 분리 권고.** 현재 한 문단에 콜론 6개, 최장 58단어 항목
- `(excluded from the test pool, as it returns no p-value)` — 유지

---

## P44 — Pre-image 계산

- 🔴 **허용오차 서술이 두 값을 뭉갬.** 현재 "numerical inversion of the forward map (Brent's-method root-finding) **to a convergence tolerance of $< 0.001°$**". 코드상 brentq의 `xtol`은 **1e-9**이고, `1e-3°`는 해를 순전파에 되먹여 검증하는 **수용 기준**(`max residual > 1e-3` 이면 reject). 서로 다른 두 값이 한 구절에 합쳐져 있음
- **제안**: `Pre-images were computed by Brent's-method root-finding on the forward map. Every solution reproduced its target hue to within $0.001°$.`
- 참고: bracketing 실패 시 720점 격자로 부호 변화 구간을 찾아 재호출하는 폴백이 있음. Methods에 넣을 필요는 없음

## P46 — 2차 세션 지표

- 🔴 `On the second-session data we recomputed, **within each condition**, the primary …` — 주어–동사 사이 삽입구. → `Within each condition we recomputed …`
- 🔴 `Because it indexes the encoding fit rather than the validated decoding readout, it is reported as corroboration only.` — 이유절 선행 + `only`. 지표의 **지위**가 먼저 와야 함. → `A secondary encoding index, the forward-tuning correlation, is reported as corroborating evidence. It is the Spearman ρ … and it indexes the encoding fit rather than the validated decoding readout.`
- 🟡 `encoding index`라 부르면서 정의는 `per-hue **decoded** hue` 기반. 둘 중 하나가 부정확할 수 있으므로 산출 코드와 대조 필요

---

## P48 — Reproducibility

- 코드 저장소 URL은 있으나 **버전/커밋 또는 DOI 미기재**. 재현성 섹션의 관행상 태그나 Zenodo DOI 권장

---

## 이상 없음으로 판단한 문단

P04(자극 정의) · P06(행동 과제 도입) · P14(SRM 정의·수식) · P16(전향 인코딩 모델 정의) · P19(Fig 2 캡션, 표기 문제 제외) · P23(LOCO 절차) · P26(기하 절 도입) · P28(ΔRDM) · P29(후보 모델 도입) · P33(역산 도입) · P34(L_γ) · P38(선택 절차 도입) · P40(Gate 2) · P43(필터 pre-image 정의) · P45(필터 평가 도입) · P47(효과크기·행동 비교)

---

## 이미 해결되어 목록에서 제외한 것

용어 스킴 적용(축 1·3·5), 미국식 철자(본문 tex), `discrimination` 예약, LOO/LOSO 약어 충돌, `read-out`→`readout`, `deviation`→`difference`, disparity 기술 오류(축 4), Results 제목 `decodable` 통일, `Ishihara classifications`→`screening outcome`, **P01 개요 문단(4곳)**, **역산 방식 `analytically`→`numerically`(P01 + Fig 5 캡션)**, **격자 사양(A)**, **디코딩 표기·360-way·exact 반올림(F)**, **MW 비독립 공개(G)**, **voxel selection 무적용 명시(D)**, **런당 볼륨 수**, **CVD 연령·sub-10 제외 사유(E)**, **GLM 추정기 OLS 정정(P12)**, **JND 계단법 전 사양(P07)**, **움직임 QC 수치 + 미적용 단계(C-1/C-2)**.
