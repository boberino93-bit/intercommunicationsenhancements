import copy
import unittest

from ipg3_swarm_validators import (
    SwarmValidationError,
    validate_allocation_decision,
    validate_assistance_request,
    validate_swarm_transition,
)


PRIMARY = {"project_id":"intercommunicationsenhancements","agent_id":"primary","agent_instance_id":"p-1","role":"PRIMARY","state":"ACTIVE"}
RESEARCH = {"project_id":"intercommunicationsenhancements","agent_id":"research-1","agent_instance_id":"r-1","role":"RESEARCH","state":"ACTIVE"}


def assistance_fixture():
    return {
        "schema":"org-agent-mesh/research-assistance-request/v1-draft",
        "request_id":"assist-1","project_id":"intercommunicationsenhancements",
        "requesting_agent":{"agent_id":"research-1","agent_instance_id":"r-1","role":"RESEARCH"},
        "task_id":"task-1","created_at_utc":"2026-10-04T05:00:00Z","problem":"conflicting architecture evidence",
        "signals":{"confidence":0.45,"independent_workstreams":4,"domains":2,"conflicting_evidence":True,"stall_count":2,"consequence":"HIGH","verification_needed":True,"tool_gap":False,"context_pressure":0.5,"attempt_count":2,"dependency_density":0.2,"novelty":0.8},
        "attempts":["reviewed baseline","compared external evidence"],
        "evidence_gaps":["independent verification"],"proposed_workstreams":["verify-a","verify-b"],
        "source_refs":["task:task-1"],"requested_by_policy":"ipg3-swarm-v3","status":"REQUESTED"
    }


def decision_fixture():
    return {
        "schema":"org-agent-mesh/swarm-allocation-decision/v1-draft",
        "decision_id":"decision-1","project_id":"intercommunicationsenhancements","assistance_request_id":"assist-1",
        "decided_by":{"agent_id":"primary","agent_instance_id":"p-1","role":"PRIMARY"},
        "research_agents":4,"manager_agents":1,"topology":"SINGLE_MANAGER_CELL",
        "cells":[{"cell_id":"cell-1","manager_id":"manager-1","research_agents":4,"workstreams":["verify-a","verify-b"]}],
        "reasoning_summary":"parallel verification plus cross-domain integration",
        "budget":{"max_research_agents":6,"max_manager_agents":1,"max_cycles":3},"status":"AUTHORIZED"
    }


def state_fixture(status="ACTIVE", revision=1, research=4, managers=1):
    topology = "PRIMARY_DIRECT" if managers == 0 else ("SINGLE_MANAGER_CELL" if managers == 1 else "MULTI_MANAGER_CELLS")
    return {
        "schema":"org-agent-mesh/swarm-state/v1-draft","swarm_id":"swarm-1","project_id":"intercommunicationsenhancements","task_id":"task-1",
        "allocation_decision_id":"decision-1","revision":revision,"research_agents":research,"manager_agents":managers,"topology":topology,
        "status":status,"resize_reason":None,"authorized_by":{"agent_id":"primary","agent_instance_id":"p-1","role":"PRIMARY"}
    }


class AssistanceRequestValidationTests(unittest.TestCase):
    def test_valid_research_request(self):
        self.assertTrue(validate_assistance_request(assistance_fixture(), bound_session=RESEARCH))

    def test_forged_requester_rejected(self):
        record = assistance_fixture(); record["requesting_agent"]["agent_instance_id"] = "other"
        with self.assertRaises(SwarmValidationError):
            validate_assistance_request(record, bound_session=RESEARCH)

    def test_attempt_evidence_mismatch_rejected(self):
        record = assistance_fixture(); record["signals"]["attempt_count"] = 9
        with self.assertRaises(SwarmValidationError):
            validate_assistance_request(record, bound_session=RESEARCH)


class AllocationAuthorityTests(unittest.TestCase):
    def test_primary_can_authorize_within_budget(self):
        self.assertTrue(validate_allocation_decision(decision_fixture(), assistance_request=assistance_fixture(), primary_session=PRIMARY))

    def test_research_agent_cannot_pose_as_primary(self):
        fake = dict(RESEARCH); fake["role"] = "RESEARCH"
        with self.assertRaises(SwarmValidationError):
            validate_allocation_decision(decision_fixture(), assistance_request=assistance_fixture(), primary_session=fake)

    def test_budget_overrun_rejected(self):
        decision = decision_fixture(); decision["research_agents"] = 7; decision["cells"][0]["research_agents"] = 7
        with self.assertRaises(SwarmValidationError):
            validate_allocation_decision(decision, assistance_request=assistance_fixture(), primary_session=PRIMARY)

    def test_topology_mismatch_rejected(self):
        decision = decision_fixture(); decision["manager_agents"] = 0
        with self.assertRaises(SwarmValidationError):
            validate_allocation_decision(decision, assistance_request=assistance_fixture(), primary_session=PRIMARY)


class SwarmLifecycleTests(unittest.TestCase):
    def test_primary_can_scale(self):
        old = state_fixture("ACTIVE",1,4,1)
        new = state_fixture("SCALING",2,6,1); new["resize_reason"] = "two unresolved fronts"
        self.assertTrue(validate_swarm_transition(old,new,primary_session=PRIMARY))

    def test_stale_revision_replay_rejected(self):
        old = state_fixture("ACTIVE",2,4,1)
        replay = state_fixture("SCALING",2,5,1)
        with self.assertRaises(SwarmValidationError):
            validate_swarm_transition(old,replay,primary_session=PRIMARY)

    def test_research_cannot_resize_swarm(self):
        old = state_fixture("ACTIVE",1,4,1); new = state_fixture("SCALING",2,5,1)
        with self.assertRaises(SwarmValidationError):
            validate_swarm_transition(old,new,primary_session=RESEARCH)

    def test_draining_cannot_scale_up(self):
        old = state_fixture("DRAINING",2,3,0); new = state_fixture("DRAINING",3,4,0)
        with self.assertRaises(SwarmValidationError):
            validate_swarm_transition(old,new,primary_session=PRIMARY)

    def test_termination_zeroes_capacity(self):
        old = state_fixture("DRAINING",2,2,0)
        new = state_fixture("TERMINATED",3,0,0)
        self.assertTrue(validate_swarm_transition(old,new,primary_session=PRIMARY))


if __name__ == "__main__":
    unittest.main()
