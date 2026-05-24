# S8 Selection Report — Model-Loss Pair LOO+Train-Test

**Sprint date**: 2026-05-23. Phase 2 model-loss selection RE-OPENED.
**Design**: 4 losses × 2 models × 4 ROIs × 2 CVD × 7 LOO HC folds.
**Losses**: L_γ (JND), L_α (8AFC), L_LOCO (within-W voxel), L_RDM (HC-pool ΔRDM cos)

## Metrics
- (a) `cvd_param_sd`: parameter SD across 7 LOO folds (stability)
- (b) `separation_rate`: fraction of folds CVD > 95th %ile of held-out HC
- (e) `train_test_mse`: variance of held-out HC parameter across folds (generalization)
- (d) inter-loss Pearson r: convergence between loss vectors over 7 folds

## sub-08 (deutan)

### V1

#### R+C 1-DOF (Δλ = DPS_lit)
| Loss | mean g | SD (a) | sep rate (b) | HC mean | train-test MSE (e) |
|---|---|---|---|---|---|
| L_gamma | 1.61 | 1.10 | 0.43 | 1.64 | 0.633 |
| L_alpha | 2.00 | 0.00 | 0.00 | 2.00 | 0.000 |
| L_LOCO | 0.00 | 0.00 | 0.00 | 1.18 | 1.101 |
| L_RDM | 2.15 | 0.00 | 0.14 | 1.59 | 0.641 |

#### 2-Component (β_s, β_c)
| Loss | mean norm | norm SD (a) | β_s SD | β_c SD | sep rate (b) | HC mean | train-test MSE (e) |
|---|---|---|---|---|---|---|---|
| L_gamma | 59.7 | 2.9 | 5.0 | 2.7 | 1.00 | 18.2 | 231.40 |
| L_alpha | 17.9 | 0.0 | 0.0 | 0.0 | 1.00 | 6.7 | 16.69 |
| L_LOCO | 57.3 | 0.0 | 0.0 | 0.0 | 0.00 | 46.3 | 330.39 |
| L_RDM | 2.0 | 0.0 | 0.0 | 0.0 | 0.00 | 17.2 | 407.34 |

#### Inter-loss Pearson r (R+C g, Δλ=DPS_lit)
| Pair | r |
|---|---|
| L_gamma ↔ L_alpha | nan |
| L_gamma ↔ L_LOCO | nan |
| L_gamma ↔ L_RDM | nan |
| L_alpha ↔ L_LOCO | nan |
| L_alpha ↔ L_RDM | nan |
| L_LOCO ↔ L_RDM | nan |

#### Inter-loss Pearson r (2-comp norm)
| Pair | r |
|---|---|
| L_gamma ↔ L_alpha | nan |
| L_gamma ↔ L_LOCO | nan |
| L_gamma ↔ L_RDM | nan |
| L_alpha ↔ L_LOCO | nan |
| L_alpha ↔ L_RDM | nan |
| L_LOCO ↔ L_RDM | nan |

### V2

#### R+C 1-DOF (Δλ = DPS_lit)
| Loss | mean g | SD (a) | sep rate (b) | HC mean | train-test MSE (e) |
|---|---|---|---|---|---|
| L_gamma | 1.61 | 1.10 | 0.43 | 1.64 | 0.633 |
| L_alpha | 2.00 | 0.00 | 0.00 | 2.00 | 0.000 |
| L_LOCO | 0.00 | 0.00 | 0.00 | 1.03 | 0.696 |
| L_RDM | 3.00 | 0.00 | 1.00 | 1.52 | 0.595 |

#### 2-Component (β_s, β_c)
| Loss | mean norm | norm SD (a) | β_s SD | β_c SD | sep rate (b) | HC mean | train-test MSE (e) |
|---|---|---|---|---|---|---|---|
| L_gamma | 59.7 | 2.9 | 5.0 | 2.7 | 1.00 | 18.2 | 231.40 |
| L_alpha | 17.9 | 0.0 | 0.0 | 0.0 | 1.00 | 6.7 | 16.69 |
| L_LOCO | 70.7 | 0.0 | 0.0 | 0.0 | 0.29 | 37.2 | 865.76 |
| L_RDM | 22.4 | 15.6 | 1.0 | 15.6 | 0.00 | 29.5 | 438.53 |

#### Inter-loss Pearson r (R+C g, Δλ=DPS_lit)
| Pair | r |
|---|---|
| L_gamma ↔ L_alpha | nan |
| L_gamma ↔ L_LOCO | nan |
| L_gamma ↔ L_RDM | nan |
| L_alpha ↔ L_LOCO | nan |
| L_alpha ↔ L_RDM | nan |
| L_LOCO ↔ L_RDM | nan |

#### Inter-loss Pearson r (2-comp norm)
| Pair | r |
|---|---|
| L_gamma ↔ L_alpha | nan |
| L_gamma ↔ L_LOCO | nan |
| L_gamma ↔ L_RDM | -0.79 |
| L_alpha ↔ L_LOCO | nan |
| L_alpha ↔ L_RDM | nan |
| L_LOCO ↔ L_RDM | nan |

### V3

#### R+C 1-DOF (Δλ = DPS_lit)
| Loss | mean g | SD (a) | sep rate (b) | HC mean | train-test MSE (e) |
|---|---|---|---|---|---|
| L_gamma | 1.61 | 1.10 | 0.43 | 1.64 | 0.633 |
| L_alpha | 2.00 | 0.00 | 0.00 | 2.00 | 0.000 |
| L_LOCO | 0.00 | 0.00 | 0.00 | 1.01 | 0.970 |
| L_RDM | 0.41 | 0.08 | 0.00 | 1.88 | 0.910 |

#### 2-Component (β_s, β_c)
| Loss | mean norm | norm SD (a) | β_s SD | β_c SD | sep rate (b) | HC mean | train-test MSE (e) |
|---|---|---|---|---|---|---|---|
| L_gamma | 59.7 | 2.9 | 5.0 | 2.7 | 1.00 | 18.2 | 231.40 |
| L_alpha | 17.9 | 0.0 | 0.0 | 0.0 | 1.00 | 6.7 | 16.69 |
| L_LOCO | 61.6 | 0.0 | 0.0 | 0.0 | 0.00 | 57.5 | 374.13 |
| L_RDM | 8.9 | 11.7 | 0.0 | 11.7 | 0.00 | 30.2 | 389.71 |

#### Inter-loss Pearson r (R+C g, Δλ=DPS_lit)
| Pair | r |
|---|---|
| L_gamma ↔ L_alpha | nan |
| L_gamma ↔ L_LOCO | nan |
| L_gamma ↔ L_RDM | -0.09 |
| L_alpha ↔ L_LOCO | nan |
| L_alpha ↔ L_RDM | nan |
| L_LOCO ↔ L_RDM | nan |

#### Inter-loss Pearson r (2-comp norm)
| Pair | r |
|---|---|
| L_gamma ↔ L_alpha | nan |
| L_gamma ↔ L_LOCO | nan |
| L_gamma ↔ L_RDM | 0.41 |
| L_alpha ↔ L_LOCO | nan |
| L_alpha ↔ L_RDM | nan |
| L_LOCO ↔ L_RDM | nan |

### V4

#### R+C 1-DOF (Δλ = DPS_lit)
| Loss | mean g | SD (a) | sep rate (b) | HC mean | train-test MSE (e) |
|---|---|---|---|---|---|
| L_gamma | 1.61 | 1.10 | 0.43 | 1.75 | 0.647 |
| L_alpha | 2.00 | 0.00 | 0.00 | 2.00 | 0.000 |
| L_LOCO | 1.10 | 0.00 | 0.29 | 0.54 | 0.193 |
| L_RDM | 1.09 | 0.92 | 0.00 | 1.40 | 1.166 |

#### 2-Component (β_s, β_c)
| Loss | mean norm | norm SD (a) | β_s SD | β_c SD | sep rate (b) | HC mean | train-test MSE (e) |
|---|---|---|---|---|---|---|---|
| L_gamma | 59.7 | 2.9 | 5.0 | 2.7 | 1.00 | 21.2 | 205.84 |
| L_alpha | 17.9 | 0.0 | 0.0 | 0.0 | 1.00 | 6.6 | 22.15 |
| L_LOCO | 70.7 | 0.0 | 0.0 | 0.0 | 1.00 | 44.5 | 307.13 |
| L_RDM | 60.0 | 2.0 | 1.0 | 3.3 | 0.14 | 38.6 | 467.00 |

#### Inter-loss Pearson r (R+C g, Δλ=DPS_lit)
| Pair | r |
|---|---|
| L_gamma ↔ L_alpha | nan |
| L_gamma ↔ L_LOCO | nan |
| L_gamma ↔ L_RDM | -0.21 |
| L_alpha ↔ L_LOCO | nan |
| L_alpha ↔ L_RDM | nan |
| L_LOCO ↔ L_RDM | nan |

#### Inter-loss Pearson r (2-comp norm)
| Pair | r |
|---|---|
| L_gamma ↔ L_alpha | nan |
| L_gamma ↔ L_LOCO | nan |
| L_gamma ↔ L_RDM | 0.25 |
| L_alpha ↔ L_LOCO | nan |
| L_alpha ↔ L_RDM | nan |
| L_LOCO ↔ L_RDM | nan |

---

## sub-09 (protan)

### V1

#### R+C 1-DOF (Δλ = DPS_lit)
| Loss | mean g | SD (a) | sep rate (b) | HC mean | train-test MSE (e) |
|---|---|---|---|---|---|
| L_gamma | 2.59 | 0.06 | 1.00 | 1.97 | 0.166 |
| L_alpha | 2.00 | 0.00 | 0.00 | 1.98 | 0.002 |
| L_LOCO | 3.00 | 0.00 | 1.00 | 1.71 | 0.560 |
| L_RDM | 2.28 | 0.75 | 0.29 | 1.89 | 1.095 |

#### 2-Component (β_s, β_c)
| Loss | mean norm | norm SD (a) | β_s SD | β_c SD | sep rate (b) | HC mean | train-test MSE (e) |
|---|---|---|---|---|---|---|---|
| L_gamma | 26.7 | 2.0 | 1.8 | 1.5 | 0.14 | 15.2 | 148.00 |
| L_alpha | 0.0 | 0.0 | 0.0 | 0.0 | 0.00 | 7.3 | 22.49 |
| L_LOCO | 70.7 | 0.0 | 0.0 | 0.0 | 1.00 | 46.0 | 426.71 |
| L_RDM | 48.6 | 1.8 | 1.8 | 1.9 | 0.71 | 18.2 | 329.57 |

#### Inter-loss Pearson r (R+C g, Δλ=DPS_lit)
| Pair | r |
|---|---|
| L_gamma ↔ L_alpha | nan |
| L_gamma ↔ L_LOCO | nan |
| L_gamma ↔ L_RDM | 0.44 |
| L_alpha ↔ L_LOCO | nan |
| L_alpha ↔ L_RDM | nan |
| L_LOCO ↔ L_RDM | nan |

#### Inter-loss Pearson r (2-comp norm)
| Pair | r |
|---|---|
| L_gamma ↔ L_alpha | nan |
| L_gamma ↔ L_LOCO | nan |
| L_gamma ↔ L_RDM | -0.45 |
| L_alpha ↔ L_LOCO | nan |
| L_alpha ↔ L_RDM | nan |
| L_LOCO ↔ L_RDM | nan |

### V2

#### R+C 1-DOF (Δλ = DPS_lit)
| Loss | mean g | SD (a) | sep rate (b) | HC mean | train-test MSE (e) |
|---|---|---|---|---|---|
| L_gamma | 2.59 | 0.06 | 1.00 | 1.97 | 0.166 |
| L_alpha | 2.00 | 0.00 | 0.00 | 1.98 | 0.002 |
| L_LOCO | 1.05 | 0.00 | 0.00 | 1.36 | 0.768 |
| L_RDM | 1.18 | 0.03 | 0.00 | 1.64 | 0.846 |

#### 2-Component (β_s, β_c)
| Loss | mean norm | norm SD (a) | β_s SD | β_c SD | sep rate (b) | HC mean | train-test MSE (e) |
|---|---|---|---|---|---|---|---|
| L_gamma | 26.7 | 2.0 | 1.8 | 1.5 | 0.14 | 15.2 | 148.00 |
| L_alpha | 0.0 | 0.0 | 0.0 | 0.0 | 0.00 | 7.3 | 22.49 |
| L_LOCO | 70.7 | 0.0 | 0.0 | 0.0 | 0.29 | 39.4 | 669.82 |
| L_RDM | 12.5 | 6.9 | 3.7 | 6.3 | 0.00 | 18.2 | 441.50 |

#### Inter-loss Pearson r (R+C g, Δλ=DPS_lit)
| Pair | r |
|---|---|
| L_gamma ↔ L_alpha | nan |
| L_gamma ↔ L_LOCO | nan |
| L_gamma ↔ L_RDM | 0.04 |
| L_alpha ↔ L_LOCO | nan |
| L_alpha ↔ L_RDM | nan |
| L_LOCO ↔ L_RDM | nan |

#### Inter-loss Pearson r (2-comp norm)
| Pair | r |
|---|---|
| L_gamma ↔ L_alpha | nan |
| L_gamma ↔ L_LOCO | nan |
| L_gamma ↔ L_RDM | 0.32 |
| L_alpha ↔ L_LOCO | nan |
| L_alpha ↔ L_RDM | nan |
| L_LOCO ↔ L_RDM | nan |

### V3

#### R+C 1-DOF (Δλ = DPS_lit)
| Loss | mean g | SD (a) | sep rate (b) | HC mean | train-test MSE (e) |
|---|---|---|---|---|---|
| L_gamma | 2.59 | 0.06 | 1.00 | 1.97 | 0.166 |
| L_alpha | 2.00 | 0.00 | 0.00 | 1.98 | 0.002 |
| L_LOCO | 0.60 | 0.00 | 0.00 | 1.21 | 0.338 |
| L_RDM | 0.91 | 0.14 | 0.00 | 1.76 | 0.779 |

#### 2-Component (β_s, β_c)
| Loss | mean norm | norm SD (a) | β_s SD | β_c SD | sep rate (b) | HC mean | train-test MSE (e) |
|---|---|---|---|---|---|---|---|
| L_gamma | 26.7 | 2.0 | 1.8 | 1.5 | 0.14 | 15.2 | 148.00 |
| L_alpha | 0.0 | 0.0 | 0.0 | 0.0 | 0.00 | 7.3 | 22.49 |
| L_LOCO | 70.7 | 0.0 | 0.0 | 0.0 | 0.00 | 50.3 | 497.40 |
| L_RDM | 16.3 | 8.0 | 11.9 | 7.9 | 0.00 | 24.9 | 506.32 |

#### Inter-loss Pearson r (R+C g, Δλ=DPS_lit)
| Pair | r |
|---|---|
| L_gamma ↔ L_alpha | nan |
| L_gamma ↔ L_LOCO | nan |
| L_gamma ↔ L_RDM | 0.02 |
| L_alpha ↔ L_LOCO | nan |
| L_alpha ↔ L_RDM | nan |
| L_LOCO ↔ L_RDM | nan |

#### Inter-loss Pearson r (2-comp norm)
| Pair | r |
|---|---|
| L_gamma ↔ L_alpha | nan |
| L_gamma ↔ L_LOCO | nan |
| L_gamma ↔ L_RDM | 0.02 |
| L_alpha ↔ L_LOCO | nan |
| L_alpha ↔ L_RDM | nan |
| L_LOCO ↔ L_RDM | nan |

### V4

#### R+C 1-DOF (Δλ = DPS_lit)
| Loss | mean g | SD (a) | sep rate (b) | HC mean | train-test MSE (e) |
|---|---|---|---|---|---|
| L_gamma | 2.59 | 0.06 | 1.00 | 2.10 | 0.078 |
| L_alpha | 2.00 | 0.00 | 0.00 | 2.00 | 0.000 |
| L_LOCO | 0.50 | 0.00 | 0.00 | 1.03 | 0.507 |
| L_RDM | 1.12 | 0.38 | 0.00 | 0.88 | 0.905 |

#### 2-Component (β_s, β_c)
| Loss | mean norm | norm SD (a) | β_s SD | β_c SD | sep rate (b) | HC mean | train-test MSE (e) |
|---|---|---|---|---|---|---|---|
| L_gamma | 26.7 | 2.0 | 1.8 | 1.5 | 0.14 | 17.0 | 148.47 |
| L_alpha | 0.0 | 0.0 | 0.0 | 0.0 | 0.00 | 6.2 | 24.68 |
| L_LOCO | 55.5 | 0.0 | 0.0 | 0.0 | 0.00 | 49.6 | 334.08 |
| L_RDM | 4.0 | 0.0 | 0.0 | 0.0 | 0.00 | 36.7 | 315.63 |

#### Inter-loss Pearson r (R+C g, Δλ=DPS_lit)
| Pair | r |
|---|---|
| L_gamma ↔ L_alpha | nan |
| L_gamma ↔ L_LOCO | nan |
| L_gamma ↔ L_RDM | 0.14 |
| L_alpha ↔ L_LOCO | nan |
| L_alpha ↔ L_RDM | nan |
| L_LOCO ↔ L_RDM | nan |

#### Inter-loss Pearson r (2-comp norm)
| Pair | r |
|---|---|
| L_gamma ↔ L_alpha | nan |
| L_gamma ↔ L_LOCO | nan |
| L_gamma ↔ L_RDM | nan |
| L_alpha ↔ L_LOCO | nan |
| L_alpha ↔ L_RDM | nan |
| L_LOCO ↔ L_RDM | nan |

---
