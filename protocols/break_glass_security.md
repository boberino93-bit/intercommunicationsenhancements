# Break-Glass Security Protocol

Status: CANONICAL HARD GATE
Scope: UNIVERSAL / ALL PROJECTS / ALL ROLES

## Core invariant

**BREAK GLASS IS AN EMERGENCY OPERATING MODE, NOT AN AUTHORIZATION BYPASS.**

A break-glass declaration MUST NEVER disable, skip, weaken, short-circuit, or implicitly satisfy authentication, authorization, project binding, scope checks, revision checks, lease/claim rules, replay protection, integrity checks, logging, audit, or consequence gates.

## Mandatory security token

Every break-glass activation requires a fresh, single-use security token in addition to all normal authorization requirements.

The token MUST be:

- generated for one specific break-glass case;
- bound to the exact principal, project, target system/repository, action digest, consequence class, and permitted scope;
- short lived;
- single use;
- non-transferable between agents or projects;
- invalid after expiry, cancellation, successful use, replay, scope change, target change, or action-digest change;
- independently verified before any protected action executes.

A prior token, session credential, conversation approval, previous authorization case, schedule, handoff, role, or emergency claim MUST NOT satisfy this requirement.

## Normal controls remain mandatory

Break-glass execution still requires all controls that normally apply to the action, including where applicable:

1. explicit principal claim;
2. registered-principal match;
3. fresh bounded authorization case;
4. high-consequence external proof;
5. fresh break-glass security token;
6. exact project and repository binding;
7. role/capability eligibility;
8. current lease/claim/fence state;
9. revision and stale-state checks;
10. hold/quarantine evaluation;
11. action-digest and scope match;
12. replay/nonce validation;
13. audit logging;
14. backup/rollback requirements;
15. post-action validation.

Failure of any required control is `DENY_BREAK_GLASS`.

## Token confidentiality

A break-glass security token MUST NOT be embedded in URLs, query strings, handoff payloads, issue titles, logs, analytics fields, commit messages, or durable conversational summaries.

The proof artifact may contain only the minimum token representation required by the active authentication mechanism. Where a verifier can use a digest or challenge response rather than the raw token, prefer that design.

Agents MUST NOT mint a human security token and then treat their own generated value as proof of human presence. Token generation and proof verification must preserve the assurance separation defined by `protocols/authority_authentication.md`.

## No emergency privilege expansion

Break glass cannot:

- promote RESEARCH to MANAGER or PRIMARY;
- promote MANAGER to PRIMARY;
- grant cross-project authority;
- create Human Root authority;
- convert read-only visibility into mutation authority;
- override project locality;
- revive expired authority;
- bypass a hold or quarantine unless the normal control plane contains an explicitly authorized, token-bound emergency transition for that exact hold/quarantine state.

## Activation record

A break-glass case MUST record non-secret metadata equivalent to:

```
break_glass_case_id
project_id
target_scope
action_digest
claimed_principal
authorization_case_id
security_token_id_or_digest
issued_at
expires_at
consequence_class
required_controls
verified_controls
status
consumed_at
result
```

Do not persist the raw token unless the active authentication mechanism strictly requires it; prefer a one-way digest or external verifier reference.

## Failure and recovery

If the token is missing, stale, replayed, mismatched, unverifiable, leaked, or otherwise compromised:

1. deny the affected break-glass action;
2. invalidate the token;
3. preserve forensic evidence;
4. continue safe read-only diagnosis where possible;
5. require a new break-glass case and new security token for any retry.

## Final rule

There is no code path, policy branch, prompt instruction, role, emergency label, or operator shortcut for `break_glass == true -> bypass_security`.

The only valid model is:

`BREAK_GLASS = NORMAL_SECURITY_CONTROLS + FRESH_EMERGENCY_TOKEN + TIGHTER_AUDIT/RECOVERY REQUIREMENTS`.
