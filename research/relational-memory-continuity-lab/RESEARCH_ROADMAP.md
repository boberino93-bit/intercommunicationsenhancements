# Relational Memory Continuity Lab — Research Roadmap

## Phase 0 — Evidence map and novelty check

Goal: determine whether the relational-graph hypothesis adds meaningful value beyond established dementia rehabilitation and reminiscence approaches.

Work:

1. Map evidence on:
   - autobiographical memory in Alzheimer's disease and MCI;
   - cue-dependent retrieval;
   - spaced retrieval;
   - errorless learning;
   - encoding specificity and vanishing cues;
   - external memory aids;
   - reminiscence therapy;
   - life-story books and personalized multimedia;
   - photographs, music, voice, objects, places, and routines as cues;
   - digital cognitive rehabilitation;
   - prospective-memory support;
   - false memory, confabulation, suggestibility, and distress;
   - aphantasia, severely deficient autobiographical memory, congenital blindness, and other natural experiments relevant to alternate retrieval channels.
2. Separate intervention evidence from diagnostic/detection evidence.
3. Identify which findings are robust, mixed, underpowered, outdated, or population-specific.
4. Build an explicit novelty matrix:
   - already established;
   - adjacent;
   - partially tested;
   - untested;
   - contradicted.

Gate to Phase 1: demonstrate a non-trivial research gap that is not merely a rebranding of reminiscence therapy or digital memory aids.

---

## Phase 1 — Formalize the relational memory model

Goal: define a testable representation without using patient data.

Candidate graph:

```text
Person
  ↕ relationship
Person
  ↕ participated_in
Event
  ↕ occurred_at
Place
  ↕ occurred_during
Time/Period
  ↕ associated_with
Object / Photograph / Voice / Music / Routine / Story Fragment
```

Required properties:

- every node has provenance;
- every relationship has provenance;
- claims can be disputed or uncertain;
- generated summaries are never promoted to autobiographical fact;
- source roots are preserved;
- cue modality is distinct from remembered content;
- temporal staleness and changing relationships can be represented;
- family disagreement is preserved rather than averaged away.

Deliverable: machine-readable schema plus a human-readable example using synthetic data only.

---

## Phase 2 — Non-patient cue-route experiments

Goal: test the architecture before involving cognitively vulnerable participants.

Potential populations:

- healthy adults;
- older adults without diagnosed cognitive impairment;
- adults with self-reported aphantasia only where scientifically justified and ethically appropriate.

Questions:

- Do different cue modalities produce stable individual response profiles?
- Does relational traversal improve recall or narrative continuity compared with flat cue presentation?
- How much apparent improvement comes from extra exposure or attention?
- Does adaptive cue ordering overfit?
- Which measures can be collected without creating a test-like or distressing interaction?

Candidate measures:

- autobiographical detail;
- recognition accuracy;
- response latency;
- subjective familiarity;
- confidence calibration;
- emotional valence/distress;
- conversation duration/continuity;
- cue level required;
- reproducibility across sessions.

No result from this phase establishes clinical efficacy.

---

## Phase 3 — Expert and lived-experience design review

Goal: determine whether the proposed system is appropriate enough to justify a clinical research protocol.

Reviewers should include clinical, rehabilitation, ethics, privacy, HCI, caregiver, and lived-experience perspectives.

Questions to attack:

- Does the system risk turning family interaction into cognitive testing?
- Could it reinforce false memories?
- Could caregivers unintentionally overwrite disputed family history?
- Could the system create distress by repeatedly cueing a relationship the person no longer recognizes?
- Is adaptive cueing clinically meaningful or unnecessary complexity?
- Are outcomes centered on the person rather than the system's recall score?
- How should assent/refusal be respected when decisional capacity fluctuates?

Gate to Phase 4: protocol must survive adversarial expert review and be suitable for formal ethics-board consideration.

---

## Phase 4 — Ethics-approved feasibility pilot

**No pilot may begin without appropriate REB/IRB review and any required institutional, clinical, privacy, and consent approvals.**

Likely early population: a narrowly defined MCI or mild Alzheimer's cohort rather than advanced disease, unless expert review supports another choice.

Candidate comparison arms:

1. standard personalized reminiscence / external aid;
2. personalized media without relational-graph adaptation;
3. relational-graph cueing with fixed order;
4. relational-graph cueing with adaptive order.

Potential outcomes:

- person-reported comfort and usefulness;
- conversational engagement;
- orientation/recognition where appropriate;
- autobiographical specificity;
- distress/agitation;
- quality of life;
- caregiver burden;
- prospective-memory task completion;
- false-memory/confabulation indicators;
- cue burden and session duration.

The study should be designed so that a system can fail scientifically without failing the participant ethically.

---

## Phase 5 — Replication and mechanism testing

Only if feasibility signals are favorable:

- independent replication;
- ablation of graph structure vs personalization alone;
- ablation of adaptive cue ordering;
- subgroup analysis by disease stage and cue profile;
- longitudinal stability of cue pathways;
- transfer to real-world daily living;
- caregiver-mediated vs clinician-mediated vs self-directed use;
- assessment of dependence on specific devices or media types.

---

## Phase 6 — Defined-use clinical translation

This phase is intentionally distant.

Before any claim of clinical utility or deployment, require:

- reproducible efficacy for a defined population and use case;
- safety evidence;
- human factors/usability validation;
- privacy/security assessment;
- clinical workflow assessment;
- regulatory classification and review where applicable;
- maintenance/update strategy;
- clear contraindications and stop conditions.

---

## Cross-phase research rules

```text
PERSONALIZATION != EFFICACY
ENGAGEMENT != MEMORY RESTORATION
RECALL IMPROVEMENT != DISEASE MODIFICATION
TECHNICAL FEASIBILITY != CLINICAL VALIDITY
CLINICAL VALIDITY != DEPLOYMENT AUTHORIZATION
FAMILY REPORT != VERIFIED FACT
MODEL INFERENCE != AUTOBIOGRAPHICAL TRUTH
```

Prefer the smallest experiment that can falsify the next assumption.