# ICML 2026 · SD4H (Structured Data 4 Health) — Workshop Profile

> Source: workshop call-for-papers / "About SD4H". Saved as framing ground-truth for the poster.

## About SD4H

Structured data lies at the core of modern healthcare, encompassing **tabular electronic
health records, high-frequency physiological time-series, and irregular clinical
measurements** collected over time. Together, these modalities provide complementary yet
**fragmented** views of an individual's health, making **holistic modeling** both essential
and challenging. While recent advances in **foundation models, multimodal learning, and
large language models** offer new opportunities to unify these data sources, the health
domain presents unique constraints — including **privacy, interpretability, irregular
sampling, and clinical deployment** — that remain largely underexplored.

## Workshop goal

The Structured Data 4 Health workshop unites researchers across structured health data
domains (from tabular EHR to biosignals and irregular clinical measurements) to address
shared challenges through:

1. **Unifying fragmented data modalities**
2. **Bridging geographic and methodological divides**
3. **Fostering convergence via interactive formats**

By encouraging cross-domain collaboration on **holistic and deployable health data
modeling**, the workshop aims to bridge cutting-edge machine learning with **real-world
healthcare impact**.

---

## What SD4H cares about (extracted keywords for framing)

| Theme | SD4H phrasing | Our hook |
|---|---|---|
| Structured data | high-dim, multimodal, time-series, irregular | fMRI **hue-geometry** (RDM) = structured neural representation |
| Fragmented → holistic | complementary yet fragmented views | we **fuse behavioral JND + neural ΔRDM** into one fit |
| Individual-level | "an individual's health" | **single-case** statistics; per-subject filter |
| Interpretability | "largely underexplored" constraint | **2-parameter** cortical model (β_s, β_c), not a black box |
| Deployment | "deployable health data modeling" | analytic **inversion → implementable correction LUT** |
| Irregular sampling | irregular clinical measurements | small-N, sparse hues; held-out generalization not in-sample p |

## What SD4H is NOT centrally about (honest gaps)

- Their canonical modality is **tabular EHR / biosignals**, not task-fMRI. We are an
  **atypical, adjacent** submission — the bridge must be made *explicitly* in the framing,
  not assumed.
- No LLM / foundation-model component in our work. Don't pretend there is one.
- "Color vision" is the *vehicle*; the *transferable* contribution is **structured-
  distortion inference + analytic inversion of an interpretable individual model**.
