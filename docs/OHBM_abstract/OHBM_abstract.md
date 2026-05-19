# OHBM Abstract

## Overview
Based on this project, we will write an abstract and make two figures for submitting OHBM conference. 
This will not include filter designing part. Therefore, the overall objective will be different with our primary objective which is building color adjustment filter for CVD. 

## Workflow direction
1. We should strictly follow `OHBM_2026_Abstract_Guidelines_FINAL.pdf` 
2. Below are outlines
- This was based on the question: "Individuals with CVD can't distinguish certain color pairs, but do thier neurological activation patterns & representations also fail?"
- Based on our result, not only Healthy controls, but also one participant with protanomaly and two with Deuteranopia, their neurological activation patterns distinguished among colors. 
- Therefore, this would be our overall logical flow
    1. Whether neural activation of individuals with CVD differ among colors is discussed.
    2. We insist their neural discriminability exist in primary visual cortex. 
    3. Color decoding result from fMRI experiment didn't differ significantly between CVD and HC.
- But, I'm open to additional implication - such as even though it is non-significant, margianl difference exists.

**Guidelines**
● Enter your abstract exactly as you would like it to appear in the Annual Meeting abstract book
and related publications (Examples are in the same folder, file names starting with `ex`).
● Avoid using all capital letters, except for standard acronyms (e.g., MRI, PET, PRESTO).

**Structure & Limits**
● Title: Maximum 100 characters; refrain from using all caps.
● Authors and Affiliations: Up to 40.
● Body: Introduction (2,000-character limit), Methods, Results, and Conclusions (4,000-character
limit each). Character limits include spaces.
● Figures: Optional; up to 2 (see figure guidelines below).
● References: Maximum of 5, formatted in AMA style.

2. These are informations with Authors and Affiliations
Authors: Jinil Kim, Minkue Cho, Jungwoo Seo, Jiook Cha(Corresponding Author)
Affiliation: Seoul National University, Seoul, South Korea

3. Writing style (even though you would do well without this guide)

## DETAILED WRITING RULES (Extracted from Examples)

### COMMON RULES
- **First sentence principle**: Each section's opening sentence must state the main point/theme directly and comprehensively
  - Example: "Disease progression is variable in multiple sclerosis (MS)" (example1)
  - Example: "Electroconvulsive therapy (ECT) is an effective treatment for major depression" (example2)
- **Precision**: Keep all sentences clear, concise, and precise
- **Tense**: Use past tense for completed work, present tense for established facts
- **Avoid**:
  - All capital letters (except standard acronyms: fMRI, BOLD, ROI, CVD, HC, etc.)
  - Future tense ("will be") - only report completed work
  - Vague statements without supporting data
  - Incomplete analyses or preliminary findings
- **Active voice preferred**: "We investigated..." rather than "It was investigated..."

### INTRODUCTION (2,000 characters max)
**Structure**:
1. Opening sentence: State the broad context/phenomenon (1 sentence)
2. Current knowledge/controversy: What is known and what is debated (2-3 sentences)
3. Knowledge gap: What remains unclear or unresolved (1-2 sentences)
4. Study objective: "Here, we investigated..." or "We examined..." (1 sentence)

**Content rules**:
- Cite key prior work using superscript numbers (max 5 references total)
- Brief CVD background: prevalence, genetic basis, behavioral phenotype
- Prior neural studies: Mention Tregillus et al. (2020) - V1 differences but V2/V3 compensation
- Controversy: Whether neural representations fail like behavioral perception
- Our goal: Test if color decoding differs between CVD and healthy controls across V1-hV4

### METHODS (4,000 characters max)
**Essential elements** (based on examples):
1. **IRB statement**: MUST include "Under an IRB-approved protocol" in first paragraph
2. **Participants**:
   - Total N with demographics: "N=9 participants (6 healthy controls: 3M/3F, age X±Y years; 3 CVD: 2 deuteranopes, 1 protanomalous, 2M/1F, age X±Y)"
   - CVD diagnosis method if applicable
3. **MRI acquisition parameters**:
   - Scanner: "3T scanner (manufacturer, model)"
   - Structural: "T1-weighted MPRAGE (TR=X ms, TE=Y ms, voxel size=A×B×C mm³)"
   - Functional: "T2*-weighted EPI (TR=X ms, TE=Y ms, flip angle=X°, voxel size=A×B×C mm³, X slices)"
   - Task details: Based on Brouwer & Heeger (2009)¹
4. **Experimental design**:
   - Task description: "Participants viewed 8 isoluminant colors..."
   - Number of runs, trials, timing
5. **Analysis pipeline**:
   - Preprocessing: "fMRIPrep version X.Y.Z"²
   - ROI definition: "V1, V2, V3, hV4 from Wang et al. (2015) probabilistic atlas"
   - GLM: "Beta maps estimated using..."
   - Feature selection: "ANOVA F-test (k=1-200 voxels, optimized per subject/ROI)"
   - Decoding: "Forward encoding model (Brouwer & Heeger, 2009)¹ with cross-validation"
   - Statistics: "Independent samples t-tests, Cohen's d effect sizes"

**Writing style**:
- Use specific numbers and parameters (not "high resolution" but "2×2×2 mm³")
- Connect analysis steps logically: "First... Next... Finally..."
- Be comprehensive but concise

### RESULTS (4,000 characters max)
**Structure** (based on examples):
1. **Lead with main finding**: State the primary result in first sentence
   - Example: "No significant differences in color decoding were found between CVD and healthy controls"
2. **Quantitative support**: Provide statistics for each claim
   - Format: "ROI (group1: M±SD, group2: M±SD, t(df)=X.XX, p=.XXX, d=X.XX)"
   - Example from our data: "V1 classification (HC: 56.6±18.6%, CVD: 55.6±2.4%, p=.930, d=-0.06)"
3. **Organize by analysis**:
   - Reconstruction error results (all 4 ROIs)
   - Classification accuracy results (all 4 ROIs)
   - Additional analyses if space permits
4. **Report hierarchy**: If hierarchical effects exist, describe the pattern
   - Example: "Reconstruction error increased hierarchically (V1 < V2 < V3 ≈ hV4)"

**Statistical reporting requirements**:
- ALWAYS include: mean ± SD, test statistic, degrees of freedom, exact p-value, effect size
- For non-significant results: Still report all statistics (don't just say "ns")
- Compare to chance/baseline when relevant: "significantly above chance (12.5%)"

### CONCLUSIONS (4,000 characters max, but typically shorter)
**Structure** (2-4 sentences):
1. Restate main finding in context (1 sentence)
2. Theoretical implication (1-2 sentences)
3. Future direction or broader impact (1 sentence)

**Content for our abstract**:
- Main finding: CVD and HC show comparable color decoding across V1-hV4
- Implication: Neural-behavioral dissociation - signals exist but decision/integration fails
- Broader impact: Informs understanding of CVD pathophysiology and potential interventions

**Avoid**:
- Overstating findings
- Discussing limitations (save for full paper)
- Introducing new information not in Results

---

## CONTENT SPECIFICS FOR OUR ABSTRACT

**INTRODUCTION**
- Brief CVD background: "Color vision deficiency (CVD) affects ~8% of males, impairing red-green discrimination"
- Prior studies on neural discriminability
- Controversy between whether their brain activation pattern differ with HC
    - This should be based on papers in `priorworks`.
    - Review is in `ELICIT_OVERALL_REPORT.pdf`. But this is made from AI so we shouldn't directly cite it
    - Including `Tregillus et al. (2020)` which suggest no difference in high-level visual cortex(V2, V3) and `Lina(2024)` suggesting V4 indiscriminability in CVD would be nice. but `Lina(2024)` is preprint so I'm searching for better way.
- Our goal and how we discovered

**METHODS**
- `example1.pdf` would be a good guide
- MRI Methods are written in `final_IRB.pdf` chapter 4. 연구수행과정 - MRI 촬영 part.
- Explicitly write the task and design is based on Brouwer & Heeger(2009) and "Under an IRB-approved protocol"
- Analysis procedure is based `GUIDE_to_fMRIprep.md` and `GUIDE_to_classify_reconstruct.md` for preprocessing & analysis. Concrete settings might change. Then I'll let you know.
- Analysis procedure was `fMRIPrep —> beta-map —> ANOVA feature selection —> color regression`
- Tell me if more specific information of MRI scanning is needed.

**RESULTS**
- Main statistical results are in `FULL_STATISTICS_SUMMARY.md` and `CVD_NEURAL_DISSOCIATION_ANALYSIS_KR.md`

**CONCLUSIONS**
- `CVD_NEURAL_DISSOCIATION_ANALYSIS_KR.md` has some implications we targetted. 

**FIGURES**
WE MUST MAKE TWO FIGURES AS BELOW
1. Experiment-analysis overview (just as `Brouwer&Heeger(2009)`) and main result(`circular_graph`)
    - We will divide into three parts, experiment, analysis, and result
2. control analysis overview based on permutation test (TBA)

**REFERENCES**
- Must have `Brouwer&Heeger(2009)` 