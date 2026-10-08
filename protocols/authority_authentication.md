# Authority Authentication and Single-Use Authorization Cases

Status: **CANONICAL HARD GATE**

## Core separation

The swarm SHALL treat these as four different states:

`CLAIMED IDENTITY != AUTHENTICATED IDENTITY != AUTHORIZATION != EXECUTION AUTHORITY`

No state implies the next one.

## 1. Principal claim is mandatory

Before evaluating permission for an externally durable mutation, the acting agent MUST ask or otherwise obtain an explicit claim identifying who is providing the authority. The agent MUST NOT infer that the current speaker is an authorized principal from conversation history, account history, writing style, project ownership, previous authorizations, personal knowledge, repository access, or familiarity with the system.

The claimed principal MUST match a registered human principal before the authorization can proceed.

## 2. Static personal facts are prohibited as authentication

Knowledge-based personal questions are not acceptable authentication. Agents MUST NOT use dates of birth, government identification numbers, family or maiden names, addresses, phone numbers, email addresses, personal history, or other static personal facts as proof of identity.

Such information may already be visible to agents, may be discoverable, and creates unnecessary sensitive-data exposure. Agents MUST NOT persist, reproduce, or log personal-fact values as authentication material.

## 3. Every mutation case requires a fresh authorization case

Every externally durable mutation case SHALL have a unique case identifier before execution. The case record MUST bind:

- the claimed principal;
- exact target project/repository/system;
- mutation class;
- bounded scope;
- consequence class;
- action digest or equivalent immutable action description;
- issue and expiry time;
- authentication disposition.

The human authorization MUST explicitly reference the case identifier.

Example:

`Principal: <registered principal>. I authorize AUTH-<case-id>.`

A timestamp supplied by the human may be recorded as context, but the system SHOULD record its own issuance and consumption timestamps.

## 4. Authorization is single-use and non-persistent

There is no session-wide, conversation-wide, project-wide, role-wide, or schedule-wide mutation authorization.

An authorization issued seconds earlier does not authorize a distinct mutation case. A previous approval for the same repository does not authorize a new operation. A parent agent cannot carry human authority into a new case. A scheduled task firing does not inherit write authority from the schedule definition.

A case is consumed or invalidated by successful execution, cancellation, denial, expiry, replay attempt, target change, mutation-class change, consequence-class change, or material scope change.

Multiple low-level writes may share one case only when they are explicitly enumerated or are strictly necessary atomic steps of the single bounded action described by that case. A newly discovered materially different action requires a new case.

## 5. Standard assurance

For ordinary bounded mutations, the minimum ceremony is:

1. obtain the explicit registered-principal claim;
2. generate and present the specific authorization case;
3. receive a fresh human authorization naming that case;
4. validate case freshness, target, scope, and non-replay immediately before execution;
5. consume the case after the bounded mutation completes or is abandoned.

This is an identity claim plus fresh action authorization. It MUST NOT be described as independent cryptographic authentication.

## 6. High-consequence step-up

Root authority changes, universal governance changes, production promotion/deployment, security or credential-boundary changes, financial actions, destructive or irreversible operations, scheduled-task enable/re-enable operations, and cross-project mutations require independent external principal proof in addition to the case authorization.

The default process-separated proof is a human-performed registered-GitHub challenge:

1. the agent generates a fresh nonce bound to the authorization case;
2. the human performs the proof through the registered GitHub principal outside the swarm execution path;
3. the agent verifies that the author matches the registered GitHub principal, the proof contains the current case ID and nonce, and it postdates challenge issuance;
4. the proof is consumed after that case.

The swarm and its agents MUST NOT create, edit, or satisfy their own proof artifact. Another agent, memory, repository data, or personal information cannot answer the challenge.

This is a process-separated external attestation, not a cryptographic passkey. A future passkey or equivalent user-presence mechanism is preferred when available.

## 7. Scheduled, recursive, and delegated agents

Schedules may launch agents and agents may research, inspect, simulate, validate, prepare patches, and formulate authorization cases without mutation authority.

A schedule firing, task contract, parent-agent instruction, role, claim, lease, prior case, prior authentication, or previous success MUST NOT create a new human authorization case.

A child may participate under the exact same unconsumed case only if the case explicitly includes that bounded delegated operation. A distinct mutation requires a new human authorization case.

## 8. Failure behavior

If the principal is missing, unknown, unverified at the required assurance tier, or if the case is missing, stale, replayed, expired, or scope-mismatched, the affected mutation MUST fail closed.

The agent SHOULD continue safe read-only work and preserve useful prepared state. It SHOULD present the exact blocked action and the minimum required authentication/authorization ceremony instead of repeatedly asking broad permission questions.

## 9. Swarm inheritance

PRIMARY, MANAGER, RESEARCH, MASTER, recovery agents, scheduled agents, child agents, validators, builders, and newly seeded projects are all subject to this protocol. No role, consensus, learning result, or local project rule may weaken it.

## 10. Mandatory bootstrap factor chain — experimental branch extension

The bootstrap-loaded policy `governance/AUTHORITY_AUTHENTICATION_POLICY.json` points to `governance/AUTHENTICATION_FACTOR_POLICY.json`, `protocols/authentication_factor_gateway.md`, `org_agent_mesh.authentication_gateway`, and `schemas/authentication_attestation.schema.json`. Deployable packages MUST contain all of them and the package builder MUST fail if the factor contract is absent or weakened.

Safe/read-only bootstrap remains non-interactive. Immediately before any protected mutation authorization is accepted, the factor gateway requires a fresh RFC-6238 TOTP attestation bound to the registered principal, current authorization case, challenge, and exact action digest. TOTP seeds are runtime-only credential material and MUST NOT be embedded in bootstrap packages.

For high-consequence operations the authentication expression is:

`TOTP_RFC6238 AND (REGISTERED_GITHUB_EXTERNAL_CHALLENGE OR MICROSOFT_ENTRA_AUTHENTICATOR)`

Microsoft Authenticator is a tertiary strong provider through Microsoft Entra OIDC/OAuth plus a tenant-configured Conditional Access authentication context. Tenant-specific authentication-context identifiers and Microsoft client secrets are runtime configuration and MUST NOT be hard-coded into portable packages.

SMS OTP is a restricted fallback through an authenticated SMS provider or a SIP MESSAGE-to-SMS adapter only when the provider explicitly supports that interworking. SMS MUST NOT replace the independent strong factor for high-consequence operations.

A factor success is authentication evidence only. It does not grant mutation authority and does not weaken the single-use human authorization case requirement.
