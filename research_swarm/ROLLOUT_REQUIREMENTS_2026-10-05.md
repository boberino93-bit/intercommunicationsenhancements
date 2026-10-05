# Research Swarm Rollout Requirements — 2026-10-05

Before the first scheduled research-swarm invocation runs:

1. This canonical Intercommunication Enhancements revision must be committed to `main`.
2. All registered adjoining project repositories must receive a local rollout overlay naming this canonical revision and the 16 GiB combined storage operating cap.
3. The rollout must cover: `duo-open`, `benefitflow`, `samsungpowerbootstrap` (`fold7-power-lab`), `warp-propulsion-lab`, and `ai-behaviour-control-lab`.
4. Each local overlay must require the project's canonical bootstrap/handoff/communication authority to remain primary and must not create a second control plane.
5. Each local overlay must require hourly agents to read the central role prompt and storage policy, perform lightweight hygiene checks, avoid redundant artifacts, and prune only with verified backup plus local destructive authority.
6. The five recurring tasks may be created only after all five project rollouts are verified on their default/main branches.
7. First scheduled execution must be set later than completion of the rollout.

The 20 GiB account quota is not the operating target. The swarm operating cap is 16 GiB, preserving 4 GiB / 20% headroom.
