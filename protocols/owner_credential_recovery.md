# Owner Credential Recovery Protocol

Status: ACTIVE

## Purpose

The human owner must retain a safe recovery path when a normal security credential becomes unavailable without lowering the production security bar.

Recovery restores authenticated credential access. It does not authorize a protected mutation.

## Recovery sequence

1. create an owner recovery request;
2. verify the registered human owner using the configured recovery-factor quorum;
3. invalidate or revoke the unavailable credential;
4. issue a cryptographically new credential with the correct owner/project/scope binding;
5. record the rotation event without storing secret material;
6. return to the normal action-specific authorization path.

The old credential is never revealed or reconstructed.

## Factors

Preferred factors include standards-compatible authenticator TOTP, passkey or hardware security key, offline recovery material, registered GitHub ownership proof, verified email, and verified mobile challenge.

Privileged recovery requires at least two independent factors and at least one strong factor when available. Email alone, SMS alone, GitHub username alone, chat history, or knowledge of a token identifier is insufficient.

Two authenticator enrollments may be supported, but two factors on the same physical device are not treated as independent failure domains.

## Authenticator material

Authenticator seed material, QR enrollment secrets, manual setup keys, live one-time codes, backup codes, and private keys must not be written to Git, prompts, AgentBus, Context Fabric, handoff packets, or ordinary logs.

Agents may construct or invoke the recovery interface, but sensitive factor material belongs only in the designated credential subsystem and authentication UI.

## Degraded recovery

When preferred strong factors are unavailable, a documented degraded recovery flow may use a higher quorum of independent ownership signals. The result remains credential rotation only and must trigger enhanced audit and re-enrollment of a strong factor.

## Invariants

- lost credential is not lost ownership;
- recovery is not a security bypass;
- recovery is not production authorization;
- authenticator success is not mutation authority;
- recovery success produces a new credential, not disclosure of the old credential;
- agent failure must not lock out the owner.