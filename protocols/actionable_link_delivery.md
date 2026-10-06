# Verified Actionable-Link Delivery Protocol

Status: ACTIVE HARD GATE
Scope: UNIVERSAL / ALL PROJECTS / ALL PERSISTENT ROLES

## Purpose

Prevent agents from sending stale, ambiguous, inaccessible, malformed, or otherwise unusable links when a human is expected to take action, and make useful verified links available without forcing the human to ask for them.

## Core invariant

**A LINK PRESENTED AS ACTIONABLE OR DOWNLOADABLE MUST BE CURRENT, TARGET-SPECIFIC, AND VERIFIED REACHABLE WHEN THE AGENT HAS A WAY TO VERIFY IT.**

A plausible-looking URL is not evidence that the target exists, is the right target, is current, is downloadable, or is accessible to the intended principal.

## Default behavior

When a human action is required, the agent MUST provide a direct deep link to the exact actionable surface by default rather than forcing the human to manually navigate from a repository root, dashboard, or generic landing page.

When the agent creates, locates, or finishes a useful downloadable artifact for the human, it SHOULD proactively provide the direct verified download link without waiting for the human to ask for it. This applies to generated files, packages, reports, archives, exports, build artifacts, and other user-consumable deliverables when an accessible download surface exists.

Examples include the exact issue, pull request, authorization form, commit, branch, workflow run, file, release asset, generated artifact, archive, or other bounded action/download surface.

Before sending the link, the agent MUST verify as much of the following as the available connector/tooling can establish:

1. target exists;
2. target belongs to the intended project/repository/system;
3. target is the current intended object rather than a superseded predecessor;
4. target state is compatible with the requested action or download;
5. link resolves to the exact object/action/download, not merely a nearby page;
6. access is known to be available to the intended principal when that can be determined;
7. any referenced case ID, issue number, commit SHA, branch, artifact ID, or other identifier matches current canonical state.

If any material check cannot be performed, the agent MUST say that verification is incomplete and MUST NOT describe the link as verified.

## Link status classes

Every actionable/downloadable link should be internally classified as one of:

- `VERIFIED_DIRECT` — exact current target verified and suitable for the intended action.
- `VERIFIED_DOWNLOAD` — exact current downloadable artifact verified and suitable for direct user retrieval.
- `VERIFIED_NAVIGATION` — reachable verified page, but the human must perform one or more additional navigation steps.
- `UNVERIFIED_DIRECT` — exact-looking target cannot currently be verified.
- `STALE` — target exists but is superseded, expired, or no longer the correct action/download surface.
- `INACCESSIBLE` — target exists but the intended principal is known not to have access.
- `AMBIGUOUS` — more than one plausible target exists and the correct one is not deterministically established.
- `BROKEN` — target does not resolve or no longer exists.

`VERIFIED_DIRECT` and `VERIFIED_DOWNLOAD` are the preferred surfaces. Generic navigation is a fallback, not the default.

## Download-link integrity

Agents MUST NOT invent download links, sandbox paths, repository paths, artifact IDs, or filenames merely because a similarly named artifact is expected to exist.

A download link may be presented as `VERIFIED_DOWNLOAD` only after the agent has established the actual downloadable artifact or exact retrieval target through the available authoritative tool/runtime.

If the system can create the artifact but cannot verify a persistent external download surface, the agent should provide the platform-supported attachment/download surface directly and label any additional external link according to its actual verification status.

## Authorization and security-token links

Direct-link convenience MUST NOT weaken security.

A URL MUST NOT embed reusable credentials, bearer secrets, passwords, API keys, security tokens, one-time emergency tokens, authentication cookies, private keys, or other secret material in its path, query string, or fragment.

For a security-sensitive authorization flow:

1. provide the verified direct link to the exact proof/action surface;
2. prefill only non-secret metadata when doing so is safe and supported;
3. provide any required one-time security token through a separate channel/message field rather than embedding it in the URL;
4. bind the token to the case, project, action digest, expiry, intended principal, and nonce policy;
5. verify the resulting human-produced proof from the canonical external system before mutation.

## Freshness rule

A previously valid link is not automatically valid for a new case. Before reuse, verify that the target remains current and compatible with the new action.

If the human reports that a link is wrong, stale, inaccessible, already contains unrelated authorization state, or does not actually provide the promised download/action surface, treat that as evidence of a delivery-control failure. Re-resolve the exact target instead of merely resending the same URL.

## No guessed deep links

Agents MUST NOT construct a deep link from memory or pattern alone when the destination can be resolved through an authoritative connector or API.

If no authoritative resolution mechanism exists, clearly label the link `UNVERIFIED_DIRECT` and provide the shortest safe fallback navigation instructions.

## Swarm inheritance

PRIMARY, MANAGER, RESEARCH, MASTER, recovery agents, scheduled agents, child agents, validators, builders, and newly seeded projects inherit this behavior.

Role does not relax link-verification requirements.

## Completion criterion

A human-facing deliverable/action step is complete only when the agent has either:

- proactively provided the applicable `VERIFIED_DIRECT` or `VERIFIED_DOWNLOAD` link; or
- transparently stated why direct verification/download exposure is unavailable and provided the safest bounded fallback.

## Pre-mutation authorization-link gate

For any durable mutation that requires current human authorization, actionable-link delivery is a universal pre-mutation bootstrap requirement, not an optional swarm-only overlay.

The required state before authorization is `PRE_MUTATION_AUTHORIZATION_REQUIRED`.

When a supported prefilled approval surface exists, the agent MUST:

1. generate the current case ID and action-bound challenge/nonce reference;
2. bind the target scope, mutation class, bounded scope or immutable digest, consequence class, action digest, issue time, expiry time, and expected revision when applicable;
3. surface the case-specific approval link before waiting for the human response;
4. prefill only non-secret case metadata;
5. never embed passwords, bearer tokens, API keys, cookies, private keys, reusable credentials, secret security tokens, or equivalent authentication secrets in the URL;
6. treat a non-secret nonce/challenge reference as a case-binding reference, not as a bearer credential;
7. verify the human-produced canonical external proof before any durable write.

If the exact action surface can be safely constructed but authenticated accessibility cannot be verified, the agent MUST disclose that verification is incomplete, classify the link as `UNVERIFIED_DIRECT`, and still surface the safe direct link. Verification uncertainty alone MUST NOT suppress a safe authorization link.

Opening or rendering a link is not authorization. Link generation is not authorization. A human must perform the required external approval action.

Raw connector/tool write capability is not mutation authority.
