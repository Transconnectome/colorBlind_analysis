# CVD Individual Confusion Report (decoder-LOCO, ForwardEncoding)

Source: `analysis/future_phase2_filter_optimization/results/decoder_loco/decoder_loco_long.csv` (11,520 trials total; 48 trials/cell per sub×ROI)

Per-CVD subject × ROI decoder-LOCO confusion. Each subject is analyzed
independently — no leave-one-subject-out needed (LOCO is already within-subject).

Columns: accuracy = P(pred=true|true); confused_to = argmax off-diagonal;
confused_to_prob = P(pred=confused_to|true); circ_mean_err = circular mean
of (pred_hue − true_hue) ∈ (−180°, +180°]; positive = CCW / hue-advance.

Chance exact accuracy = 0.125. Chance mean abs error ≈ 90°.

## sub-08 (deutan, confusion axis ≈ 150°)

### sub-08 · V1

| True | Acc | Top-1 confusion → | Prob | Mean signed err (°) | Mean |err| (°) |
|---|---:|---|---:|---:|---:|
| 0 red | 0.17 | red → cyan | 0.50 | -145.0 | 126.0 |
| 1 orange | 0.17 | orange → cyan | 0.33 | +131.8 | 105.3 |
| 2 yellow | 0.00 | yellow → cyan | 0.50 | +128.1 | 120.3 |
| 3 yel-grn | 0.00 | yel-grn → blue | 0.50 | +97.1 | 95.7 |
| 4 cyan | 0.00 | cyan → yellow | 0.33 | -163.2 | 107.5 |
| 5 blu-cy | 0.17 | blu-cy → blue | 0.50 | +17.8 | 56.5 |
| 6 blue | 0.67 | blue → cyan | 0.33 | -36.5 | 44.7 |
| 7 magenta | 0.33 | magenta → blue | 0.33 | -45.8 | 60.8 |

**Confusion-axis-aligned errors**: orange (|err|=105°, pred_dir=177°)

### sub-08 · V2

| True | Acc | Top-1 confusion → | Prob | Mean signed err (°) | Mean |err| (°) |
|---|---:|---|---:|---:|---:|
| 0 red | 0.17 | red → cyan | 0.50 | -152.2 | 125.0 |
| 1 orange | 0.00 | orange → cyan | 0.50 | +165.6 | 141.5 |
| 2 yellow | 0.00 | yellow → cyan | 0.50 | +121.8 | 121.8 |
| 3 yel-grn | 0.00 | yel-grn → cyan | 0.33 | +89.7 | 86.7 |
| 4 cyan | 0.33 | cyan → orange | 0.17 | -41.7 | 74.7 |
| 5 blu-cy | 0.17 | blu-cy → blue | 0.50 | +31.7 | 55.8 |
| 6 blue | 0.33 | blue → cyan | 0.50 | -59.4 | 59.5 |
| 7 magenta | 0.50 | magenta → yel-grn | 0.17 | -44.5 | 54.5 |

**Confusion-axis-aligned errors**: cyan (|err|=75°, pred_dir=138°)

### sub-08 · V3

| True | Acc | Top-1 confusion → | Prob | Mean signed err (°) | Mean |err| (°) |
|---|---:|---|---:|---:|---:|
| 0 red | 0.33 | red → cyan | 0.33 | -154.6 | 103.3 |
| 1 orange | 0.17 | orange → cyan | 0.33 | +147.2 | 110.8 |
| 2 yellow | 0.00 | yellow → cyan | 0.50 | +75.4 | 78.5 |
| 3 yel-grn | 0.33 | yel-grn → cyan | 0.33 | +37.4 | 55.7 |
| 4 cyan | 0.17 | cyan → orange | 0.33 | -93.3 | 89.2 |
| 5 blu-cy | 0.17 | blu-cy → orange | 0.17 | -58.4 | 76.2 |
| 6 blue | 0.33 | blue → cyan | 0.50 | -57.8 | 57.8 |
| 7 magenta | 0.50 | magenta → blu-cy | 0.33 | -43.6 | 59.2 |

**Confusion-axis-aligned errors**: yellow (|err|=78°, pred_dir=165°), yel-grn (|err|=56°, pred_dir=172°), blu-cy (|err|=76°, pred_dir=167°)

### sub-08 · V4

| True | Acc | Top-1 confusion → | Prob | Mean signed err (°) | Mean |err| (°) |
|---|---:|---|---:|---:|---:|
| 0 red | 0.00 | red → cyan | 0.50 | -149.3 | 144.7 |
| 1 orange | 0.33 | orange → blue | 0.33 | -170.3 | 102.0 |
| 2 yellow | 0.17 | yellow → cyan | 0.50 | +100.5 | 99.5 |
| 3 yel-grn | 0.00 | yel-grn → blue | 0.67 | +89.4 | 86.3 |
| 4 cyan | 0.67 | cyan → orange | 0.17 | -11.5 | 40.8 |
| 5 blu-cy | 0.50 | blu-cy → cyan | 0.33 | -17.2 | 41.2 |
| 6 blue | 0.00 | blue → blu-cy | 0.67 | -47.8 | 49.7 |
| 7 magenta | 0.17 | magenta → cyan | 0.67 | -114.7 | 107.5 |

## sub-09 (protan, confusion axis ≈ 16°)

### sub-09 · V1

| True | Acc | Top-1 confusion → | Prob | Mean signed err (°) | Mean |err| (°) |
|---|---:|---|---:|---:|---:|
| 0 red | 0.67 | red → yellow | 0.17 | +3.9 | 27.8 |
| 1 orange | 0.00 | orange → red | 0.83 | -53.0 | 65.5 |
| 2 yellow | 0.17 | yellow → magenta | 0.33 | -89.1 | 90.5 |
| 3 yel-grn | 0.17 | yel-grn → red | 0.67 | -104.7 | 97.7 |
| 4 cyan | 0.33 | cyan → blue | 0.50 | +41.9 | 57.3 |
| 5 blu-cy | 0.17 | blu-cy → red | 0.33 | +108.0 | 104.0 |
| 6 blue | 0.17 | blue → cyan | 0.33 | -59.1 | 83.0 |
| 7 magenta | 0.33 | magenta → red | 0.50 | +13.1 | 45.7 |

**Confusion-axis-aligned errors**: orange (|err|=66°, pred_dir=352°), yellow (|err|=90°, pred_dir=1°), yel-grn (|err|=98°, pred_dir=30°), cyan (|err|=57°, pred_dir=222°), blue (|err|=83°, pred_dir=211°)

### sub-09 · V2

| True | Acc | Top-1 confusion → | Prob | Mean signed err (°) | Mean |err| (°) |
|---|---:|---|---:|---:|---:|
| 0 red | 0.67 | red → cyan | 0.17 | -12.7 | 44.5 |
| 1 orange | 0.17 | orange → red | 0.50 | -52.3 | 77.0 |
| 2 yellow | 0.00 | yellow → blue | 0.67 | +160.2 | 134.3 |
| 3 yel-grn | 0.17 | yel-grn → red | 0.67 | -112.2 | 104.7 |
| 4 cyan | 0.17 | cyan → blue | 0.67 | +86.9 | 86.7 |
| 5 blu-cy | 0.33 | blu-cy → blue | 0.33 | -0.5 | 36.0 |
| 6 blue | 0.50 | blue → cyan | 0.33 | -5.6 | 50.7 |
| 7 magenta | 0.17 | magenta → red | 0.33 | -6.7 | 51.5 |

**Confusion-axis-aligned errors**: orange (|err|=77°, pred_dir=353°), yel-grn (|err|=105°, pred_dir=23°)

### sub-09 · V3

| True | Acc | Top-1 confusion → | Prob | Mean signed err (°) | Mean |err| (°) |
|---|---:|---|---:|---:|---:|
| 0 red | 0.50 | red → yel-grn | 0.33 | +42.5 | 59.2 |
| 1 orange | 0.17 | orange → red | 0.67 | -50.6 | 58.3 |
| 2 yellow | 0.00 | yellow → cyan | 0.33 | +132.6 | 112.8 |
| 3 yel-grn | 0.33 | yel-grn → red | 0.67 | -96.1 | 86.3 |
| 4 cyan | 0.17 | cyan → blue | 0.50 | +63.9 | 80.0 |
| 5 blu-cy | 0.00 | blu-cy → red | 0.33 | +55.1 | 80.5 |
| 6 blue | 0.50 | blue → yel-grn | 0.33 | +8.5 | 67.2 |
| 7 magenta | 0.00 | magenta → red | 0.67 | +22.2 | 44.5 |

**Confusion-axis-aligned errors**: red (|err|=59°, pred_dir=42°), orange (|err|=58°, pred_dir=354°), yellow (|err|=113°, pred_dir=223°), yel-grn (|err|=86°, pred_dir=39°)

### sub-09 · V4

| True | Acc | Top-1 confusion → | Prob | Mean signed err (°) | Mean |err| (°) |
|---|---:|---|---:|---:|---:|
| 0 red | 0.83 | red → blue | 0.17 | -7.5 | 14.7 |
| 1 orange | 0.17 | orange → red | 0.50 | -0.6 | 46.7 |
| 2 yellow | 0.17 | yellow → cyan | 0.33 | +174.8 | 102.7 |
| 3 yel-grn | 0.33 | yel-grn → red | 0.50 | -88.9 | 83.3 |
| 4 cyan | 0.17 | cyan → blue | 0.50 | +105.9 | 96.0 |
| 5 blu-cy | 0.00 | blu-cy → cyan | 0.50 | -85.7 | 88.5 |
| 6 blue | 0.33 | blue → red | 0.17 | -2.4 | 71.7 |
| 7 magenta | 0.00 | magenta → red | 0.50 | +12.7 | 54.3 |

**Confusion-axis-aligned errors**: orange (|err|=47°, pred_dir=44°)

## sub-10 (deutan_mild, confusion axis ≈ 150°)

### sub-10 · V1

| True | Acc | Top-1 confusion → | Prob | Mean signed err (°) | Mean |err| (°) |
|---|---:|---|---:|---:|---:|
| 0 red | 0.50 | red → blue | 0.33 | -16.1 | 42.8 |
| 1 orange | 0.67 | orange → cyan | 0.33 | +39.2 | 49.0 |
| 2 yellow | 0.50 | yellow → blu-cy | 0.33 | +56.5 | 68.3 |
| 3 yel-grn | 0.33 | yel-grn → orange | 0.33 | -19.3 | 64.8 |
| 4 cyan | 0.50 | cyan → blue | 0.33 | +12.7 | 37.7 |
| 5 blu-cy | 0.17 | blu-cy → red | 0.33 | +119.7 | 104.8 |
| 6 blue | 0.00 | blue → yellow | 0.33 | -167.2 | 120.0 |
| 7 magenta | 0.50 | magenta → orange | 0.33 | +33.7 | 57.3 |

**Confusion-axis-aligned errors**: yellow (|err|=68°, pred_dir=147°), blu-cy (|err|=105°, pred_dir=345°), magenta (|err|=57°, pred_dir=349°)

### sub-10 · V2

| True | Acc | Top-1 confusion → | Prob | Mean signed err (°) | Mean |err| (°) |
|---|---:|---|---:|---:|---:|
| 0 red | 0.50 | red → blue | 0.33 | -19.3 | 43.2 |
| 1 orange | 0.33 | orange → magenta | 0.50 | -44.1 | 69.8 |
| 2 yellow | 0.17 | yellow → blu-cy | 0.33 | +75.1 | 83.5 |
| 3 yel-grn | 0.50 | yel-grn → orange | 0.33 | -56.0 | 60.5 |
| 4 cyan | 0.33 | cyan → blue | 0.50 | +35.2 | 54.0 |
| 5 blu-cy | 0.50 | blu-cy → magenta | 0.33 | +47.6 | 62.2 |
| 6 blue | 0.00 | blue → red | 0.33 | +145.1 | 109.2 |
| 7 magenta | 0.00 | magenta → orange | 0.33 | +144.7 | 97.2 |

**Confusion-axis-aligned errors**: yellow (|err|=84°, pred_dir=165°)

### sub-10 · V3

| True | Acc | Top-1 confusion → | Prob | Mean signed err (°) | Mean |err| (°) |
|---|---:|---|---:|---:|---:|
| 0 red | 0.17 | red → magenta | 0.33 | -7.9 | 58.3 |
| 1 orange | 0.33 | orange → yel-grn | 0.50 | +55.2 | 66.2 |
| 2 yellow | 0.33 | yellow → blue | 0.33 | -99.1 | 94.5 |
| 3 yel-grn | 0.50 | yel-grn → orange | 0.17 | -35.5 | 54.3 |
| 4 cyan | 0.00 | cyan → blue | 0.50 | +112.8 | 105.2 |
| 5 blu-cy | 0.17 | blu-cy → orange | 0.17 | +71.5 | 86.5 |
| 6 blue | 0.17 | blue → yellow | 0.33 | -129.0 | 115.5 |
| 7 magenta | 0.83 | magenta → cyan | 0.17 | -19.9 | 32.3 |

**Confusion-axis-aligned errors**: red (|err|=58°, pred_dir=352°), yellow (|err|=94°, pred_dir=351°), blue (|err|=116°, pred_dir=141°)

### sub-10 · V4

| True | Acc | Top-1 confusion → | Prob | Mean signed err (°) | Mean |err| (°) |
|---|---:|---|---:|---:|---:|
| 0 red | 0.83 | red → yellow | 0.17 | +13.0 | 16.7 |
| 1 orange | 0.17 | orange → red | 0.50 | -16.0 | 41.5 |
| 2 yellow | 0.50 | yellow → orange | 0.17 | -13.9 | 58.0 |
| 3 yel-grn | 0.17 | yel-grn → blue | 0.33 | -79.4 | 84.8 |
| 4 cyan | 0.33 | cyan → orange | 0.33 | -57.8 | 73.7 |
| 5 blu-cy | 0.00 | blu-cy → blue | 0.33 | +97.8 | 99.0 |
| 6 blue | 0.00 | blue → yellow | 0.33 | -169.8 | 130.7 |
| 7 magenta | 0.00 | magenta → blu-cy | 0.67 | -89.3 | 89.5 |

**Confusion-axis-aligned errors**: cyan (|err|=74°, pred_dir=122°), blu-cy (|err|=99°, pred_dir=323°)

---

## Cross-reference with sub-08 R+C qualitative report (hV4)

Sub-08 reported after R+C filter: c3≡c4 merge (yellow / yellow-green),
c5≡c6 merge (cyan / blue-cyan). These map to decoder labels 2≡3 and 4≡5.

| Predicted merge | HC pooled P(true→conf) | sub-08 V4 P(true→conf) | Sub-08 pooled ROI P(true→conf) |
|---|---|---|---|
| yellow → yel-grn (label 2→3) | 0.232 | 0.000 | 0.083 |
| yel-grn → yellow (label 3→2) | 0.077 | 0.000 | 0.000 |
| cyan → blu-cy (label 4→5) | 0.077 | 0.167 | 0.125 |
| blu-cy → cyan (label 5→4) | 0.089 | 0.333 | 0.208 |

_If sub-08 values meaningfully exceed HC pooled P, the decoder-confusion signal supports the R+C qualitative report. If not, perceptual merge (stimulus → perception) is decoupled from BOLD-decoder confusion (voxel pattern → class)._
