# SIP-to-SMS Transport Contract

Status: **EXPERIMENTAL HARDENING CONTRACT**

This transport is a restricted delivery mechanism for `SMS_OTP`. It does not change the assurance of SMS and can never satisfy the independent strong-factor requirement for high-consequence mutations.

## Provider boundary

The provider MUST explicitly document that SIP `MESSAGE` traffic is bridged to the cellular SMS network. A generic SIP account or successful SIP registration is insufficient evidence of SMS interworking.

The adapter follows RFC 3428 MESSAGE semantics:
- use an out-of-dialog `MESSAGE` request unless the provider explicitly requires otherwise;
- use `text/plain; charset=utf-8`;
- a `200` response means the final SIP destination accepted the message;
- a `202` response means a gateway/store-and-forward service accepted the message and MUST NOT be represented as confirmed handset delivery;
- other final responses fail closed.

## Secrets and destinations

SIP username, password/token, client certificate/private key, raw telephone number, SMS pepper, OTP value, and attestation signing key MUST NOT be stored in the repository or bootstrap package.

The transport receives only a protected destination reference such as `vault://...`, `secret://...`, or `principal://...`. A runtime resolver returns the E.164 destination and provider SIP URI.

## Network controls

Production defaults:
- `sips:`/TLS required;
- exact gateway-host allowlist required;
- provider credentials loaded from the external secret subsystem;
- bounded connect/request timeout;
- bounded message size;
- same idempotency key preserved across retries/failover;
- failover permitted only for retryable transport/provider failures;
- no OTP or destination logging.

Carrier-specific adapters may narrow these controls but MUST NOT weaken them.
