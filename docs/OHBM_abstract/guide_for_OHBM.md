# Guide for OHBM

Additional analysis to be done before December 15th of system time. 
궁극적 질문:  색약인들의 색지각은 구분이 잘 안 된다. 다만 본 분석에서 뇌표상도 구분이 잘 안 될까? Primary visual cortex(V1~V4)에서는 잘 되는 게 아닐까? 이는 지금까지의 분석 결과를 기반으로 함. 
이를 위한 검증이 아래임. 

1. FIGURE 색 레이블 실험대로 수정하기
- colorBlind_test.py와 circular figure 간의 제시하는 색이 다름
- 현재 피규어의 색 레이블이 너무 파스텔톤임. python 파일의 화면에서의 색처럼 vivid해야 함

**실험 자극 색상 (스크린샷 기준):**
- color_1 (0°): 붉은색 (빨강) - Screenshot 11.20.48 PM
- color_2 (45°): 주황색 - Screenshot 11.20.54 PM
- color_3 (90°): 황갈색 - Screenshot 11.21.00 PM
- color_4 (135°): 녹색 - Screenshot 11.21.07 PM
- color_5 (180°): 청록색 - Screenshot 11.21.14 PM
- color_6 (225°): 파란색 - Screenshot 11.21.20 PM
- color_7 (270°): 진한 파랑 - Screenshot 11.21.26 PM
- color_8 (315°): 보라/분홍 - Screenshot 11.21.30 PM

**해결 방법:** 스크린샷에서 직접 RGB 추출하여 사용 (Lab 공식 변환 대신)

2. Model performance baseline 파악을 위한 추가 실험
- 배경: 
우리가 하고 싶은 주장: 적녹색약인들의 brain representation이 차이가 나더라!
—> 예상 가능한 비판: 그거 그냥 beta-map fitting 하고, ANOVA 기반 가장 중요한 친구들 select 해서 모델 만들어서 그런 것 아니야? 즉, 데이터인 참가자의 색 반응이 유의미한 게 아니라 모델 구조 때문에 reconstruction 정확도가 높은 거 아니야? 
—> 비판에 대한 대응: 그게 아닌 것을 확인하려고 추가실험을 해봤어. 만약 적록 색약자가 적색과 녹색을 정말 구분을 못한다면, 이 둘의 레이블을 뒤바꿔도 결과가 동일하게 나오겠지?

If 적-녹이 완전 equivalent 하다 —> true label을 그대로 쓰나, random으로 섞으나, 둘을 1:1 완전 뒤바꾸나, 모두 동일한 결과가 나와야 할 것.

- 방법: 
따라서, 유의미한 equivalent feature 를 가정한 분석. color 1과 color 2로 구성된 red 쌍, color 4와 5로 구성된 green 쌍에 대해서 permutation 등 라벨 혼동을 주었을 때 reconstruction 성능 확인

- 진행 방향: 
가능하다면, fMRIprep을 다시 하지 않고, 현재 전처리된 데이터로 진행하였으면 함. 
가장 확실한 방법은 ezbids 생성 전 events.tsv의 trial_type (color) 바꾸기

3. 2의 연장선상에서 novel color로 해서 선형 파괴?
Novel color reconstruction은 색 간 선형 관계를 가정하기에, 단순히 color 2, color 4 간의 정답 레이블을 바꾸는 것만으로도 성능에 영향을 줄 수 있음. 
따라서 novel color reconstruction 시행 및 결과 분석 후, 정답 레이블 바꾸어서 시행 및 결과 분석, 이후 비교 

4. Group level model
—> unseen HC —> performance score들 —> t-test —> HC쪽이 통계적으로 유의하게 CVD보다 더 좋은 예측 성능을 보인다.
—> unseen CVD —> performance score들
—> CVD와 HC의 색지각 뇌표상이 다르다.

Group level map을 뽑아서 - CVD 개인에게 적용해서 - CVD에게 안 나오게 하는 방법이 있지 않을까
개인차 때문에 그룹 레벨 모델이 어렵다면 - 통계적으로 비교해서 - unseen healthy 퍼포와 unseen cvd 퍼포 간 유의미한 차이를 보일 수 있지 않을까