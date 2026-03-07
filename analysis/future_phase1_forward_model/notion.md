# Future Phase 2: 연속 색조 보간 모델 (Continuous Hue Interpolation)
> 6-channel encoding으로 360° 색 공간의 임의 색조에 대한 뇌 반응 예측

## 상태
- 📋 **Planned** — Future Phase 1 완료 후 시작

## 목표
- **Stimulus hue (0-360°) → Brain voxel responses** 매핑 학습
- 8개 이산 자극 (45° 간격)으로부터 360° 연속 공간으로 보간
- 6개 half-wave rectified basis channel 사용 (Brouwer & Heeger, 2009)

## 성공 기준

| 수준 | 지표 | 목표 |
|------|------|------|
| ✅ Required | Reconstruction error (LOCO CV) | < 60° (chance 90°, baseline 32°) |
| ⭐ Excellent | Reconstruction error | < 45° |
| Indirect | RDM smoothness | 색조 간 점진적 변화 |
| Indirect | Inter-encoder consistency | HC 피험자 간 인코더 일관성 |

## 방법

**Channel Response Function**: 6개 half-wave rectified Gaussian basis channel
```
C(θ) = max(0, exp(-(θ - θ_center)² / 2σ²))
```

**인코더 학습** (Phase 1 HC common space에서):
- `Y_predicted = C(θ) @ W_enc`
- **LOCO validation**: 7색 학습 → 1색 예측 (보간 품질 평가)

> 💡 **Phase 3 의존성**: Filter optimization은 8개 이산 색상이 아닌 **임의 display 색상**에 대한 반응 예측 필요 → 이 인코더가 필수

---

## 완료 후 조치
- 디렉토리명 변경: `future_phase2_forward_model` → `phase2_forward_model`

## 다음 단계
→ **Future Phase 3**: CVD Filter Optimization via 360° search

### 🔽 작업 위치 및 관련 문서
- 작업 공간: `prediction_model_workspace/`
- 상세 계획: `prediction_model_workspace/docs/PHASE2_PREDICTION_MODEL.md`
- TODO: `prediction_model_workspace/MASTER_PLAN.md` Phase 2 section

### 🔽 TODO: 문헌 조사
- SOTA fMRI prediction model 조사 (2023-2026)
- 탐색 범주: Linear encoders, Neural networks, Generative models, Hybrid approaches
- 평가 기준: Sample efficiency, 해석 가능성, 계산 비용, 유사 fMRI 과제 성공 사례
