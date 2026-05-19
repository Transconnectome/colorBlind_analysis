# PaperBanana Figure Generation Guide

## 파일 목록

| 파일 | Figure | 유형 | 도구 |
|------|--------|------|------|
| `prompt1_method.txt` + `prompt1_caption.txt` | Pipeline 통합 (Prompt 1) | Diagram | PaperBanana web |
| `fig1_panel_a_method.txt` + `fig1_panel_a_caption.txt` | Fig 1 panel (a) | Diagram | PaperBanana web |
| `fig1_panels_bcd.py` | Fig 1 panels (b-d) | Chart | Matplotlib |
| `fig_hc_specificity.py` | HC Specificity (appendix) | Chart | Matplotlib |
| `fig2_collapse_method.txt` + `fig2_collapse_caption.txt` | Fig 2 (appendix) | Diagram | PaperBanana web |

## PaperBanana 설정값

### Prompt 1 (Pipeline 통합)
- Aspect Ratio: **21:9**
- Pipeline Mode: **demo_full**
- Max Critic Rounds: **3**
- Target Resolution: **2K**

### Fig 1 panel (a) (ICML main, single-column)
- Aspect Ratio: **4:3** (3.25 x 2.5 in에 근접)
- Pipeline Mode: **demo_full**

### Fig 2 (ICML appendix, full-width)
- Aspect Ratio: **21:9** (6.75 x 3.0 in에 근접)
- Pipeline Mode: **demo_full**

## 사용법

### Diagram (PaperBanana)
1. https://paper-banana.org/ 또는 HuggingFace Spaces 접속
2. "Method Section Content"에 `*_method.txt` 내용 붙여넣기
3. "Figure Caption"에 `*_caption.txt` 내용 붙여넣기
4. 설정 조정 (위 표 참조)
5. Generate -> 3회 Critic refinement 후 결과 다운로드

### Chart (Matplotlib)
```bash
conda activate srm
cd docs/ICML_workshop/icml2026/paperbanana_inputs/
python fig1_panels_bcd.py   # -> fig1_panels_bcd.pdf
python fig_hc_specificity.py # -> fig_hc_specificity.pdf
```

### 합성 (Fig 1 = panel a + panels b-d)
Panel (a) PNG + panels (b-d) PDF를 PowerPoint/Keynote에서 상하 배치 후 PDF 내보내기.
또는 LaTeX에서 subfigure로 합성.
