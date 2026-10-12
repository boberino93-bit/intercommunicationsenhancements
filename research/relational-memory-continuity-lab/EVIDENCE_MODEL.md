# Relational Memory Continuity Lab — Evidence Model

## 1. Design goal

Represent autobiographical and relational support material as a provenance-aware graph in which **source evidence, interpretation, cueing, and participant response remain separate**.

The model must support useful reconstruction without converting plausible association into autobiographical fact.

## 2. Core node classes

Candidate node types:

- `PERSON`
- `RELATIONSHIP`
- `EVENT`
- `PLACE`
- `TIME_PERIOD`
- `OBJECT`
- `PHOTOGRAPH`
- `AUDIO`
- `VOICE_RECORDING`
- `MUSIC`
- `ROUTINE`
- `STORY_FRAGMENT`
- `DOCUMENT`
- `SOURCE_RECORD`
- `CUE_PRESENTATION`
- `PARTICIPANT_RESPONSE`
- `CAREGIVER_OBSERVATION`
- `CLINICIAN_OBSERVATION`

## 3. Relationship classes

Examples:

- `PARENT_OF`
- `CHILD_OF`
- `SPOUSE_OF`
- `SIBLING_OF`
- `FRIEND_OF`
- `RAISED_BY`
- `LIVED_WITH`
- `PARTICIPATED_IN`
- `OCCURRED_AT`
- `OCCURRED_DURING`
- `APPEARS_IN`
- `SPEAKS_IN`
- `ASSOCIATED_WITH`
- `REPORTED_BY`
- `SUPPORTED_BY`
- `CONTRADICTED_BY`
- `DERIVED_FROM`
- `CUE_FOR`
- `ELICITED_RESPONSE`

Relationship semantics must remain explicit. `ASSOCIATED_WITH` must not silently become `PARENT_OF`, `WAS_PRESENT_AT`, or any stronger factual claim.

## 4. Provenance state

Every autobiographical claim should identify a source class and confidence basis.

Candidate source states:

```text
PRIMARY_DOCUMENTARY_SOURCE
PARTICIPANT_REPORTED
FAMILY_REPORTED
MULTIPLE_FAMILY_REPORTED_SHARED_ORIGIN_UNKNOWN
CLINICIAN_RECORDED
PHOTO_OR_AUDIO_SUPPORTED
INFERRED_ASSOCIATION
DISPUTED
UNKNOWN
AI_GENERATED_SUMMARY
```

A source's existence does not prove the factual correctness of the claim it contains.

## 5. Context envelope

Each meaningful claim or cue should preserve, where available:

```text
WHO
WHAT
WHEN
WHERE
WHY / STATED_RATIONALE
HOW_KNOWN
SOURCE
CONFIDENCE_BASIS
ALTERNATIVE_INTERPRETATIONS
DISPUTE_STATUS
LAST_VERIFIED
```

Missing context remains missing; it is not silently completed by the model.

## 6. Cue-response records

A cue presentation should be a separate record from the autobiographical fact being cued.

Candidate `CuePresentation` fields:

```text
cue_id
participant_id_pseudonymous
session_id
cue_modality
source_object_id
intended_target
presentation_order
presentation_time
prior_cues_in_session
adaptation_rule_used
```

Candidate `ParticipantResponse` fields:

```text
response_id
cue_id
response_time
verbal_response_raw_or_coded
recognition_response_if_explicit
subjective_familiarity_if_asked
observable_engagement_code
observable_distress_code
caregiver_observation
clinician_observation
stop_triggered
confidence_in_coding
```

Affective or behavioral response must not be backfilled as factual recognition.

## 7. Retrieval-path representation

The project may derive a **cue-route profile** such as:

```text
VOICE -> high observed utility
PLACE -> moderate observed utility
PHOTOGRAPH -> variable
DATE -> low observed utility
MUSIC -> high engagement / uncertain autobiographical specificity
```

This profile is an empirical summary of prior sessions, not a permanent trait.

Therefore:

```text
PAST_CUE_UTILITY != CURRENT_CUE_UTILITY
RESPONSE_PATTERN != DIAGNOSIS
INDIVIDUAL_PROFILE != POPULATION_TRUTH
```

Profiles need freshness, uncertainty, and reset semantics.

## 8. False-memory protection

Generated text may summarize source-backed material but must retain links to the source graph.

No model-generated relationship or event should be promoted to autobiographical truth without an external source path.

Required rule:

```text
GENERATED_ASSOCIATION -> CANDIDATE_ONLY
CANDIDATE_ONLY + NO_SOURCE -> MUST_NOT_PRESENT_AS_FACT
```

If a model proposes a potentially useful association that is not source-backed, it may be routed to a caregiver/researcher verification queue rather than shown to the participant as history.

## 9. Disputed-memory handling

When accounts conflict, preserve competing claims.

Example:

```text
Claim A: Person X attended Event E
Source: Family member A
Status: FAMILY_REPORTED

Claim B: Person X did not attend Event E
Source: Family member B
Status: FAMILY_REPORTED

Reconciled status: DISPUTED
```

The system should not generate a definitive narrative until the dispute is resolved by appropriate external evidence, if it can be resolved at all.

## 10. Graph-value test

The graph architecture must itself be falsifiable.

A core experiment should compare:

- personalized media set with no graph traversal;
- the same media linked by a relational graph;
- relational graph with fixed cue order;
- relational graph with adaptive cue order.

If graph structure adds no measurable value, the simpler system should be preferred.

## 11. Separation of evidence layers

```text
SOURCE
  -> AUTOBIOGRAPHICAL CLAIM
      -> CUE OBJECT
          -> CUE PRESENTATION
              -> OBSERVED RESPONSE
                  -> CODED OUTCOME
                      -> RESEARCH INFERENCE
```

Each transition must remain auditable.

The participant's response is evidence about the response—not automatic evidence that the autobiographical claim is true.

## 12. Parent-project lineage

This model borrows provenance, uncertainty, context, and anti-silent-inference principles from Intercommunication Enhancements. Cross-project reuse is design ancestry, not independent scientific corroboration.