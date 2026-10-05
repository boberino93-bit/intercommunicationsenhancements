# Verified Actionable-Link Delivery Protocol

Status: ACTIVE HARDENING CONTROL
Scope: UNIVERSAL / ALL PROJECTS / ALL PERSISTENT ROLES

## Purpose

Prevent agents from sending stale, ambiguous, inaccessible, malformed, or otherwise unusable links when a human is expected to take action.

## Core invariant

**A LINK PRESENTED AS ACTIONABLE MUST BE CURRENT, TARGET-SPECIFIC, AND VERIFIED REACHABLE WHEN THE AGENT HAS A WAY TO VERIFY IT.**

A plausible-looking URL is not evidence that the target exists, is the right target, is current, or is accessible to the intended principal.

## Default behavior

When a human action is required, the agent SHOULD provide a direct deep link to the exact actionable surface by default rather than forcing the human to manually navigate from a repository root, dashboard, or generic landing page.

Examples include the exact issue, pull request, authorization form, commit, branch, workflow run, file, settings page, or other bounded action surface.

Before sending the link, the agent MUST verify as much of the following as the available connector/tooling can establish:

1. target exists;
2. target belongs to the intended project/repository/system;
3. target is the current intended object rather than a superseded predecessor;
4. target state is compatible with the requested action;
5. link resolves to the exact object/action, not merely a nearby page;
6. access is known to be available to the intended principal when that can be determined;
7. any referenced case ID, issue number, commit SHA, branch, or other identifier matches current canonical state.

If any material check cannot be performed, the agent MUST say that verification is incomplete and MUST NOT describe the link as verified.

## Link status classes

Every actionable link should be internally classified as one of:

- `VERIFIED_DIRECT` — exact current target verified and suitable for the intended action.
- `VERIFIED_NAVIGATION` — reachable verified page, but the human must perform one or more additional navigation steps.
- `UNVERIFIED_DIRECT` — exact-looking target cannot currently be verified.
- `STALE` — target exists but is superseded, expired, or no longer the correct action surface.
- `INACCESSIBLE` — target exists but the intended principal is known not to have access.
- `AMBIGUOUS` — more than one plausible target exists and the correct one is not deterministically established.
- `BROKEN` — target does not resolve or no longer exists.

Only `VERIFIED_DIRECT` should be presented as the preferred action link.

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

If the human reports that a link is wrong, stale, inaccessible, or already contains unrelated authorization state, treat that as evidence of a delivery-control failure. Re-resolve the exact target instead of merely resending the same URL.

## No guessed deep links

Agents MUST NOT construct a deep link from memory or pattern alone when the destination can be resolved through an authoritative connector or API.

If no authoritative resolution mechanism exists, clearly label the link `UNVERIFIED_DIRECT` and provide the shortest safe fallback navigation instructions.

## Swarm inheritance

PRIMARY, MANAGER, RESEARCH, MASTER, recovery agents, scheduled agents, child agents, validators, builders, and newly seeded projects inherit this behavior.

Role does not relax link-verification requirements.

## Completion criterion

The link-delivery step is complete only when the agent has either:

- provided a `VERIFIED_DIRECT` link; or
- transparently stated why direct verification is unavailable and provided the safest bounded fallback.
