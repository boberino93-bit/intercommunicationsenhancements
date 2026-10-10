# IPG3 External Interoperability Adapter Contract

Status: **NON-AUTHORITATIVE DESIGN**

IPG3 treats external agent protocols as interoperability surfaces, not authorization roots.

A2A, AGNTCY/SLIM, MCP-adjacent agent tooling, brokers, Slack, HTTP APIs or future transports may carry requests and artifacts, but they do not replace the Organization Agent Mesh project/control-plane rules.

## Boundary model

`REMOTE AGENT / PROTOCOL`

→ transport/authentication adapter

→ untrusted normalized ingress envelope

→ local principal verification

→ local project binding

→ capability/delegation/approval checks

→ local task/effect control plane

→ mutation

The reverse path exports only explicitly authorized and policy-sanitized information.

## Adapter responsibilities

Every adapter must:

1. identify the remote protocol and version;
2. preserve the original remote request/artifact identity;
3. preserve or generate a stable local idempotency identity;
4. map correlation/task context without inventing authority;
5. preserve expiry/deadline information where supplied;
6. capture remote identity/capability declarations as claims;
7. classify remote content as `EXTERNAL_UNTRUSTED` until locally validated;
8. expose unsupported semantics explicitly;
9. validate message size/scope before persistence/execution;
10. prevent direct remote writes to internal control-plane stores;
11. produce attributable evidence for translation and rejection decisions;
12. fail closed when a required IPG3 semantic cannot be represented safely.

## Remote capability claims

Remote Agent Cards, capability descriptors, service advertisements or equivalent metadata are discovery evidence.

They are not local permissions.

A remote declaration such as `can_write_repository=true` may help choose a compatible service, but local authorization still requires the relevant project binding, local capability, delegation and approval rules.

## Identity mapping

The adapter should map authenticated remote identity into an IPG3 principal only when a configured trust mechanism validates:

- issuer/trust domain;
- credential validity period;
- key/signature binding;
- revocation/version state;
- remote subject identity;
- mapping to the intended local project/agent relationship.

Unknown or unauthenticated identities remain external/untrusted principals with no mutation capability.

## A2A-style mapping

A future A2A adapter should evaluate mappings for:

- Agent Card -> remote capability/discovery record;
- A2A task -> IPG3 task/delegation context;
- A2A message -> IPG3 message payload/envelope;
- A2A artifact -> IPG3 artifact/provenance record;
- task lifecycle -> local task state projection;
- context/session identity -> trace/correlation context.

Where A2A semantics are less restrictive than IPG3, local IPG3 policy wins.

Where A2A carries information IPG3 does not understand, preserve it as bounded extension evidence rather than silently discarding security-relevant fields.

## AGNTCY/SLIM-style mapping

A future AGNTCY/SLIM adapter should evaluate:

- authenticated/verifiable agent identity -> IPG3 principal evidence;
- discovery directory -> non-authoritative service discovery;
- secure session/group identity -> transport/session evidence;
- encrypted messaging -> transport protection;
- observability/evaluation events -> IPG3 observability inputs.

Transport authentication proves the source endpoint/principal according to that trust domain. It does not prove the request is authorized for the local project.

## MCP/tool boundary

Tool protocols expose capabilities to an agent. Tool availability does not imply authority to invoke a tool for every task.

Before invocation, IPG3 still checks:

- bound project/session;
- delegated tool allowance;
- capability ceiling;
- target scope;
- human approval if required;
- effect idempotency identity;
- sensitivity/data policy.

## Translation loss policy

Each adapter produces a translation report containing:

- remote protocol/version;
- source object IDs;
- mapped IPG3 IDs;
- fields mapped losslessly;
- fields transformed;
- fields omitted;
- unsupported semantics;
- trust assumptions;
- validation/rejection outcomes.

If a missing semantic is required for a protected operation, the adapter rejects the operation.

## Cross-project rule

External interoperability never becomes an implicit cross-project bridge.

If a remote call would move data or authority between two Organization Agent Mesh projects, the explicit Cross-Project Exchange v2 contract applies in addition to the external protocol.

## Adapter conformance tests

Every interoperability adapter must be tested for:

- forged remote identity;
- stale/revoked credential;
- spoofed project claim;
- duplicate/replayed task;
- same idempotency key with altered payload;
- expired request;
- unsupported required semantic;
- oversized artifact;
- malicious capability descriptor;
- transport downgrade/version mismatch;
- remote attempt to escalate local capabilities;
- remote attempt to bypass human approval;
- external artifact with poisoned instructions;
- loss of causation/correlation;
- adapter crash/retry;
- local project pause/drain while remote retries continue.

## Selection rule

IPG3 should support multiple external adapters. No external standard should become a mandatory internal transport unless empirical deployment evidence shows that doing so preserves the framework's isolation, portability and failure semantics better than an adapter boundary.
