# Relational Memory Continuity Lab

**Project status:** ALPHA / RESEARCH INCUBATION  
**Clinical status:** NOT A CLINICAL TOOL / NOT A MEDICAL DEVICE / NOT FOR PATIENT CARE  
**Human-subject status:** NO HUMAN-SUBJECT EXPERIMENTATION AUTHORIZED  
**Repository state:** Incubated inside `intercommunicationsenhancements` for governed review; intended to remain separable from the parent project.

## Purpose

The Relational Memory Continuity Lab (RMCL) investigates whether a person's autobiographical and relational continuity can be better supported by preserving the **structure around memories**—people, places, voices, objects, routines, chronology, emotions, and verified relationships—rather than treating memory support as a flat list of reminders.

The motivating research question is:

> Can a personalized relational cue graph help people with mild cognitive impairment (MCI) or Alzheimer's disease access preserved routes into autobiographical and relational memory more effectively, safely, and humanely than conventional reminder or reminiscence approaches?

The project is especially interested in the possibility that different people retain different retrieval channels over time—for example voice, place, music, object, semantic relationship, routine, or photograph—and that a support system could adaptively present **verified cues** without fabricating autobiographical content.

## Why this is plausible enough to study

Existing research already supports several pieces of the problem:

- Aphantasia research shows that markedly reduced visual imagery can alter autobiographical memory while leaving other cognitive routes available, making it a useful comparative model for studying alternate retrieval strategies rather than an analogue of Alzheimer's disease.
- Dementia and Alzheimer's rehabilitation literature has examined spaced retrieval, errorless learning, cueing, encoding-specific support, external memory aids, reminiscence therapy, life-story work, photographs, music, and digital interventions.
- Personalized reminiscence materials appear more promising than generic materials in several studies, though effects are variable and often modest.
- Digital cognitive interventions show promise, particularly in MCI, but added benefit over active interventions remains uncertain.

This project therefore starts from **convergence of partial evidence**, not from a claim that the core hypothesis has been proven.

## Core hypothesis

A person's memory should not be modeled only as isolated facts or episodes. A useful support system may need to preserve and navigate a **relational graph**:

```text
PERSON ↔ PLACE ↔ EVENT ↔ TIME ↔ OBJECT ↔ VOICE ↔ MUSIC ↔ ROUTINE ↔ RELATIONSHIP
```

The experimental question is whether traversing this graph through individually effective cue pathways improves outcomes such as:

- recognition or orientation where appropriate;
- conversational continuity;
- autobiographical detail;
- emotional connection;
- quality of life;
- reduction of distress during family interaction;
- caregiver burden;
- successful completion of everyday prospective-memory tasks.

No single outcome is assumed to be the right objective for every person.

## Foundational boundaries

The project adopts the following safety invariants:

```text
CUE != MEMORY
RECONSTRUCTION != ORIGINAL EXPERIENCE
PLAUSIBLE BIOGRAPHICAL DETAIL != VERIFIED HISTORY
EXTERNAL MEMORY != HUMAN MEMORY
RETRIEVAL FAILURE != MEMORY ABSENCE
RECOGNITION FAILURE != RELATIONSHIP ABSENCE
AFFECTIVE RESPONSE != FACTUAL CONFIRMATION
AI-GENERATED NARRATIVE != AUTOBIOGRAPHICAL EVIDENCE
```

And the central human-facing principle:

> **Do not test the person. Help the person.**

A support system should not pressure someone to prove recognition, correct them aggressively, or treat a failed recall attempt as evidence that a relationship is gone.

## Aphantasia research role

Aphantasia is included only as a **comparative cognitive model** for alternate retrieval strategies. It is not treated as Alzheimer's disease, dementia, neurodegeneration, or a disease state.

The research question is whether strategies used successfully when vivid visual imagery is weak can inspire testable hypotheses about multimodal cueing and externalized memory support in neurodegenerative disease.

## Initial project structure

- `PROJECT_CHARTER.md` — research hypotheses, falsification conditions, scope, and maturity gates.
- `RESEARCH_ROADMAP.md` — phased plan from literature synthesis to ethical pilot design.
- `EVIDENCE_MODEL.md` — provenance-aware relational memory graph and cue-response model.
- `ETHICS_AND_SAFETY.md` — human dignity, privacy, consent, false-memory, and clinical boundaries.
- `SOURCES.md` — starting evidence base and source-class notes.

## What this project does not claim

RMCL does **not** currently claim that it can:

- restore memories lost to Alzheimer's disease;
- slow or reverse neurodegeneration;
- diagnose Alzheimer's disease or MCI;
- determine decisional capacity;
- infer family relationships from appearance or voice;
- reconstruct missing autobiographical history without source evidence;
- identify a person solely through voice, face, or emotion;
- replace clinicians, neuropsychologists, occupational therapists, caregivers, or family judgment;
- conduct human-subject research without appropriate ethics review and informed-consent/capacity safeguards.

## Current maturity

`CONCEPTUAL_OVERLAP -> RESEARCH_HYPOTHESIS`

No stronger state is justified yet.

The next milestone is not implementation. It is a rigorous evidence review and falsifiable experimental design.