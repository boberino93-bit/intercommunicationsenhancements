from datetime import datetime, timedelta, timezone
import unittest

from org_agent_mesh.hybrid_admission import (
    AdmissionDisposition,
    DemandDigest,
    HybridAdmissionError,
    LAUNCH_SCHEMA_V2,
    build_priority_frontier,
    evaluate_generic_admission,
    launch_fingerprint,
    validate_launch_context_v2,
)
from org_agent_mesh.project_work_control import ProjectWorkDecision, ProjectWorkState

UTC = timezone.utc
NOW = datetime(2026, 10, 6, 2, 49, tzinfo=UTC)


def ctx(mode, project_id=None, role_id=None):
    p = {
        "schema": LAUNCH_SCHEMA_V2,
        "mode": mode,
        "project_id": project_id,
        "role_id": role_id,
        "occurrence_id": "occ-1",
        "route_id": "route-1",
        "routing_contract_version": "2",
        "registry_revision": "reg-1",
        "issued_at": (NOW - timedelta(seconds=5)).isoformat(),
        "expires_at": (NOW + timedelta(minutes=2)).isoformat(),
    }
    p["context_fingerprint"] = launch_fingerprint(p)
    return p


def dd(**kw):
    values = dict(
        project_id="intercommunicationsenhancements", project_state="ACTIVE",
        source_revision="src-1", registry_revision="reg-1", global_run_id="run-1",
        generated_at=NOW - timedelta(seconds=5), expires_at=NOW + timedelta(minutes=1),
        priority_tier=2, priority_provenance="DERIVED", provenance_ref="state:src-1",
        impact=.8, information_gain=.9, evidence_gap=.8, contradiction=.2,
        duplicate_risk=.1, manager_backpressure=.2, primary_backpressure=.1,
        candidate_roles=("research",), candidate_lanes=("lane-a",),
    )
    values.update(kw)
    return DemandDigest(**values)


class HybridAdmissionTests(unittest.TestCase):
    def test_modes_fail_closed(self):
        validate_launch_context_v2(ctx("PROJECT_CAPACITY", "p"), now=NOW)
        validate_launch_context_v2(ctx("PORTFOLIO_CAPACITY"), now=NOW)
        with self.assertRaises(HybridAdmissionError):
            validate_launch_context_v2(ctx("PROJECT_CAPACITY", "p", "research"), now=NOW)
        with self.assertRaises(HybridAdmissionError):
            validate_launch_context_v2(ctx("PORTFOLIO_CAPACITY", "p"), now=NOW)

    def test_replay_and_tamper_fail_closed(self):
        with self.assertRaises(HybridAdmissionError):
            validate_launch_context_v2(ctx("PORTFOLIO_CAPACITY"), now=NOW, consumed_occurrence_ids={"occ-1"})
        p = ctx("PORTFOLIO_CAPACITY")
        p["route_id"] = "changed"
        with self.assertRaises(HybridAdmissionError):
            validate_launch_context_v2(p, now=NOW)

    def test_priority_provenance_is_validated(self):
        with self.assertRaises(HybridAdmissionError):
            dd(priority_provenance="HUMAN_SET").validate(now=NOW, expected_registry_revision="reg-1", expected_global_run_id="run-1")
        with self.assertRaises(HybridAdmissionError):
            dd(priority_tier=0).validate(now=NOW, expected_registry_revision="reg-1", expected_global_run_id="run-1")

    def test_frontier_is_non_authoritative(self):
        f = build_priority_frontier([dd()], now=NOW, registry_revision="reg-1", global_run_id="run-1")
        self.assertFalse(f.authority_conveyed)
        self.assertEqual(len(f.entries), 1)
        self.assertEqual(build_priority_frontier([dd(manager_backpressure=1.0)], now=NOW, registry_revision="reg-1", global_run_id="run-1").entries, ())

    def test_project_local_roles_and_hold_gate_admission(self):
        registry = {"projects": {"p": {"self_admissible_roles": ["research", "manager"]}}}
        active = ProjectWorkDecision("p", ProjectWorkState.ACTIVE, True, True, True, "NO_ACTIVE_HOLD")
        admitted = evaluate_generic_admission(
            project_id="p", requested_role="research", lane_id="lane", source_revision="s1", expected_source_revision="s1",
            registry=registry, registry_revision="reg", project_work_decision=active, frontier_snapshot_id="pf", started_at=NOW, now=NOW)
        self.assertEqual(admitted.disposition, AdmissionDisposition.ADMITTED)
        self.assertFalse(admitted.authority_conveyed)
        self.assertFalse(admitted.mutation_authority)
        denied = evaluate_generic_admission(
            project_id="p", requested_role="administrator", lane_id="lane", source_revision="s1", expected_source_revision="s1",
            registry=registry, registry_revision="reg", project_work_decision=active, frontier_snapshot_id="pf", started_at=NOW, now=NOW)
        self.assertEqual(denied.disposition, AdmissionDisposition.ADMISSION_BLOCKED)
        held = ProjectWorkDecision("p", ProjectWorkState.HOLD, False, False, False, "PROJECT_HOLD_ACTIVE")
        blocked = evaluate_generic_admission(
            project_id="p", requested_role="research", lane_id="lane", source_revision="s1", expected_source_revision="s1",
            registry=registry, registry_revision="reg", project_work_decision=held, frontier_snapshot_id="pf", started_at=NOW, now=NOW)
        self.assertEqual(blocked.disposition, AdmissionDisposition.ADMISSION_BLOCKED)

    def test_empty_peer_roles_and_sla_fail_closed(self):
        registry = {"projects": {"peer": {"self_admissible_roles": []}}}
        active = ProjectWorkDecision("peer", ProjectWorkState.ACTIVE, True, True, True, "NO_ACTIVE_HOLD")
        blocked = evaluate_generic_admission(
            project_id="peer", requested_role="research", lane_id="lane", source_revision="s1", expected_source_revision="s1",
            registry=registry, registry_revision="reg", project_work_decision=active, frontier_snapshot_id="pf", started_at=NOW, now=NOW)
        self.assertEqual(blocked.disposition, AdmissionDisposition.ADMISSION_BLOCKED)
        late = evaluate_generic_admission(
            project_id="peer", requested_role="research", lane_id="lane", source_revision="s1", expected_source_revision="s1",
            registry=registry, registry_revision="reg", project_work_decision=active, frontier_snapshot_id="pf", started_at=NOW - timedelta(seconds=46), now=NOW)
        self.assertTrue(late.sla_normal_max_exceeded)


if __name__ == "__main__":
    unittest.main()
