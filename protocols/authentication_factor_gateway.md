# Authentication Factor Gateway

Status: **EXPERIMENTAL HARD GATE — branch scoped**

This protocol extends the canonical authority-authentication boundary without merging authentication and authorization.

`AUTHENTICATION EVIDENCE != HUMAN AUTHORIZATION != EXECUTION AUTHORITY`

## Mandatory placement

Every deployable bootstrap package MUST include:

- `governance/AUTHENTICATION_FACTOR_POLICY.json`;
- `org_agent_mesh/authentication_gateway.py`;
- `org_agent_mesh/totp_verifier.py`;
- `schemas/authentication_attestation.schema.json`;
- this protocol.

The package builder MUST fail closed when these components or their required policy invariants are absent or weakened.

Agents MAY bootstrap, recover context, research, inspect, test, and perform other safe/read-only work without an interactive factor challenge. The factor gateway is invoked immediately before a protected mutation authorization envelope is accepted.

## TOTP baseline

RFC-6238 TOTP is mandatory for every protected mutation. The verifier is portable; the seed is not. TOTP seeds MUST come from an external credential resolver at runtime and MUST NOT be stored in the repository, bootstrap package, prompts, logs, handoffs, attestations, or audit records.

The accepted TOTP counter MUST be captured exactly and consumed once. A Boolean-only replay key based on the verifier's current timestep is insufficient when a drift window is enabled because an adjacent-window code could otherwise be accepted more than once.

A successful TOTP check produces only a short-lived signed attestation bound to the principal, authorization case, challenge ID, and exact action digest.

## High-consequence step-up

For a high-consequence mutation, the required authentication expression is:

`TOTP_RFC6238 AND (REGISTERED_GITHUB_EXTERNAL_CHALLENGE OR MICROSOFT_ENTRA_AUTHENTICATOR)`

The registered-GitHub path remains the process-separated independent proof already defined by `protocols/authority_authentication.md`.

Microsoft Authenticator is integrated through Microsoft Entra OIDC/OAuth and tenant-configured Conditional Access authentication context. Portable packages MUST NOT hard-code a tenant-specific authentication-context identifier. Before normalized Microsoft evidence reaches the gateway, the OIDC adapter MUST validate the token cryptographically, including signature, issuer, audience, expiry, tenant, nonce/state, principal mapping, and the required authentication context.

## SMS fallback

SMS OTP is a restricted fallback. A provider API is preferred. A SIP MESSAGE adapter MAY be used only where the selected provider explicitly supports SIP-to-SMS interworking; generic SIP messaging MUST NOT be assumed to reach the PSTN SMS network.

SMS controls:

- 8 CSPRNG-generated decimal digits;
- maximum 5-minute lifetime;
- maximum 3 failed attempts by canonical policy;
- single use;
- HMAC digest storage only, using an external pepper;
- protected destination reference only, not a raw phone number in bootstrap material;
- deployment rate limits and resend throttling required;
- no account-existence disclosure.

SMS MUST NOT satisfy the independent strong-factor requirement for root, universal-governance, production/deployment, security/credential-boundary, financial, destructive/irreversible, schedule-enable/re-enable, or cross-project mutations.

## Failure behavior

Missing TOTP, stale/replayed factor evidence, binding mismatch, invalid Microsoft evidence, unavailable secret material, or an unsafe SMS downgrade MUST deny only the affected protected mutation. Safe/read-only work may continue.
