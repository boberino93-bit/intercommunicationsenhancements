# Relational Memory Continuity Lab — Ethics and Safety

## 1. Human dignity first

The project exists to support connection, orientation, and continuity—not to force autobiographical performance.

Core rule:

> **Do not test the person. Help the person.**

A failed recall attempt is not a project failure and must not be treated as evidence that a relationship no longer matters.

## 2. No memory fabrication

The system must not fill missing autobiographical details merely because a generated story is plausible.

Required distinctions:

```text
VERIFIED_SOURCE
FAMILY_REPORTED
PARTICIPANT_REPORTED
CLINICIAN_RECORDED
INFERRED_ASSOCIATION
DISPUTED
UNKNOWN
AI_GENERATED_SUMMARY
```

Only source-supported material may be presented as biographical fact.

If a generated summary is shown, it must remain traceable to source material and must never silently create a new autobiographical claim.

## 3. Cueing is not confirmation

A person smiling at a photograph, responding to a voice, or becoming emotionally engaged does not prove factual recognition.

```text
AFFECTIVE_RESPONSE != FACTUAL_CONFIRMATION
FAMILIARITY != IDENTITY_VERIFICATION
VOICE_RESPONSE != RELATIONSHIP_PROOF
CUE_SUCCESS != MEMORY_RESTORATION
```

## 4. Avoid coercive correction

The system should not repeatedly tell a person that their recollection is wrong, force them to accept an identity claim, or continue cueing when the interaction is increasing distress.

Candidate stop conditions include:

- expressed refusal;
- visible or reported distress;
- repeated confusion aggravated by cueing;
- escalating agitation;
- caregiver/clinician stop request;
- unresolved provenance conflict in the cue being presented.

The exact clinical stop protocol must be designed with qualified experts before any patient-facing study.

## 5. Consent, assent, and fluctuating capacity

Any future human-subject work involving MCI or dementia requires formal ethics review and a protocol appropriate to fluctuating decisional capacity.

The project should distinguish:

- legal/ethics-board consent requirements;
- participant assent;
- participant objection/refusal;
- surrogate or substitute decision-maker authorization where applicable;
- clinician/site requirements.

Surrogate permission must not erase a participant's contemporaneous distress or refusal.

## 6. Privacy and family-history sensitivity

Relational memory data can expose exceptionally sensitive information about:

- family relationships;
- health;
- bereavement;
- sexuality;
- adoption;
- estrangement;
- abuse;
- finances;
- location history;
- religion;
- legal disputes;
- identity.

Therefore:

- collect the minimum data required for the research question;
- separate raw media from derived cue metadata;
- encrypt sensitive data at rest and in transit in any future implementation;
- use role-based access;
- record provenance and access;
- support deletion/withdrawal where legally and scientifically appropriate;
- avoid public repositories for participant data;
- never include identifiable family stories in public project documentation without explicit permission and appropriate review.

## 7. Family disagreement and contested history

Families do not always share one account of the past.

The system must be able to preserve disagreement:

```text
CLAIM A — supported by source X
CLAIM B — reported by person Y
STATUS — DISPUTED
```

It must not average conflicting family narratives into a synthetic certainty.

## 8. No autonomous diagnosis or capacity judgment

RMCL must not use voice, facial expression, response latency, recall failure, or cue-response patterns to independently diagnose Alzheimer's disease, dementia, depression, delirium, or decisional incapacity.

Those signals may eventually be research observations if ethically approved, but:

```text
BEHAVIORAL_SIGNAL != DIAGNOSIS
PHYSIOLOGICAL_SIGNAL != CAPACITY
MEMORY_ERROR != CONSENT FAILURE
```

## 9. Personalization risks

Personalization can increase usefulness and also increase harm.

Risks include:

- repeatedly surfacing grief or trauma;
- reinforcing incorrect family narratives;
- overfitting to short-term responses;
- narrowing interaction to a small set of repeatedly rewarded cues;
- making caregivers dependent on the system;
- creating the impression that the system understands a person's inner state.

Every personalization mechanism should have a reset path, provenance record, and human-review route.

## 10. Clinical boundary

Until formally validated for a defined use, RMCL is research infrastructure only.

It must not provide treatment recommendations, medication advice, diagnostic conclusions, emergency triage, or claims of disease modification.

## 11. Human-subject maturity gate

No vulnerable-population study should begin until the project has, at minimum:

1. a defined scientific question;
2. a prespecified protocol and stopping rules;
3. appropriate clinical collaborators;
4. data-protection and privacy review;
5. informed-consent/capacity plan;
6. formal REB/IRB approval where required;
7. distress and adverse-event procedures;
8. a plan for false-memory/confabulation risk;
9. predefined outcomes and analysis;
10. an independent safety/research-ethics review.

## 12. Governing principle

> **The system should help a person find a path toward connection. It must never manufacture a past for them.**