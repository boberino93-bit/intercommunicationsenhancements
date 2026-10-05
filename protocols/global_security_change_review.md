# Global Security Change Review

Status: ACTIVE

Global Swarm security or universal-governance changes originating from Intercommunication Enhancements require an additional human review before propagation.

The acting agent must be the authorized Intercommunication Enhancements PRIMARY and must satisfy all existing mutation and high-consequence checks.

Before propagation, the PRIMARY must warn that the proposed change can alter or conflict with existing Global Swarm security behavior and requires thorough review.

Propagation additionally requires:
- explicit warning acknowledgement;
- two distinct current security-validation receipts;
- pre-change backup and expected-state binding;
- an explicit cross-project change record;
- post-change target-state verification.

A failed validation does not create an alternate mutation path. Credential recovery may restore valid credentials, but recovery does not authorize the pending change.

MFA may be used as a stronger owner-verification factor when available, but normal use does not require it unless another active policy does.

Invariants:
- review is not authority;
- authentication is not authorization;
- recovery is not production approval;
- source-project acceptance is not Global Swarm propagation.