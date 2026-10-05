# Artifact Completeness Protocol

Status: ACTIVE

## Purpose

User-facing artifacts must not be described as ready to use, ready to submit, ready to execute, or complete while required fields or dependencies remain unresolved.

## Readiness states

Allowed readiness states are:
- DRAFT
- TEMPLATE
- PARTIALLY_POPULATED
- REQUIRES_HUMAN_INPUT
- READY_TO_USE
- READY_TO_SUBMIT
- READY_TO_EXECUTE

Only the applicable READY state permits language implying immediate use without modification.

## Pre-delivery checks

Before a READY classification, verify:
1. every mandatory field is populated;
2. no unresolved placeholder or template marker remains;
3. required identifiers match current canonical state;
4. referenced resources are current and reachable where verification is possible;
5. required human input has been incorporated or clearly declared outstanding;
6. secret-handling rules remain satisfied;
7. instructions accurately describe any remaining human action;
8. the exact final rendered artifact, not only its source components, was checked.

Common unresolved markers include TODO, TBD, REPLACE_ME, bracketed insert/paste instructions, angle-bracket variables, shell-style template variables, and empty mandatory fields.

A deliberately out-of-band secret does not need to be embedded to make an artifact safe. In that case the artifact must state the required human assembly step and must not be labeled fully ready until that step is complete.

Completeness never creates authorization or execution authority.