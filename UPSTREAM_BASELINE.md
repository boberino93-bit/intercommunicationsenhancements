# Upstream Seed Baseline

The project was initialized from the user-supplied `org-agent-mesh-framework-v1.0.0` package.

## Seed characteristics verified before hardening

- Framework: **Organization Agent Mesh**
- Seed version: **1.0.0**
- Distribution file count declared by seed: **129**
- Seed package status: **COMPLETE**
- Seed tests: **18 run / 18 pass / 0 failures / 0 errors**
- Seed integrity model: fail-closed, sanitization required, declared dependency closure, SHA-256 verification
- Existing authority tiers: ORCHESTRATOR, REVIEWER, SPECIALIST
- Existing control-plane areas: message bus, evidence, authority, lanes, presence/liveness, continuity, contradiction resolution, review, successor generation, initialization, schemas, adapters, protocols, synthetic examples, reference project

## Hardening gap identified

The seed already placed `project_id` on important records, but the first hardening review found that project identity was not yet consistently enforced as an authorization boundary across message routing, agent execution instances, paths/repositories, lane/presence coordination, cross-project communication, and deployable role packages.

This repository therefore treats the seed as upstream evidence and evolves the intercommunications layer toward deterministic multi-project isolation rather than modifying Duo Open or BenefitFlow directly.
