"""Relational validation for IPG3 adaptive research/swarm regulation.

Design-only. These checks enforce authority and lifecycle invariants that JSON Schema
cannot safely express by itself. They never spawn agents or grant capabilities.
"""

from __future__ import annotations


class SwarmValidationError(ValueError):
    pass


def _topology(research: int, managers: int) -> str:
    if research <= 0:
        return "REJECTED"
    if managers == 0:
        return "PRIMARY_DIRECT"
    if managers == 1:
        return "SINGLE_MANAGER_CELL"
    return "MULTI_MANAGER_CELLS"


def validate_assistance_request(record: dict, *, bound_session: dict) -> bool:
    if record.get("schema") != "org-agent-mesh/research-assistance-request/v1-draft":
        raise SwarmValidationError("wrong assistance request schema")
    if record.get("project_id") != bound_session.get("project_id"):
        raise SwarmValidationError("assistance request project differs from bound session")
    requester = record.get("requesting_agent") or {}
    if requester.get("agent_id") != bound_session.get("agent_id"):
        raise SwarmValidationError("requester agent does not match bound session")
    if requester.get("agent_instance_id") != bound_session.get("agent_instance_id"):
        raise SwarmValidationError("requester execution instance does not match bound session")
    if requester.get("role") not in {"PRIMARY", "MANAGER", "RESEARCH"}:
        raise SwarmValidationError("invalid requesting role")
    if bound_session.get("state") != "ACTIVE":
        raise SwarmValidationError("only ACTIVE sessions may submit assistance requests")
    signals = record.get("signals") or {}
    attempts = record.get("attempts") or []
    if signals.get("attempt_count") != len(attempts):
        raise SwarmValidationError("attempt_count must equal recorded attempts")
    if not record.get("evidence_gaps"):
        raise SwarmValidationError("assistance request must identify evidence gaps")
    if not record.get("proposed_workstreams"):
        raise SwarmValidationError("assistance request must propose at least one workstream")
    if record.get("status") != "REQUESTED":
        raise SwarmValidationError("new assistance request must begin REQUESTED")
    return True


def validate_allocation_decision(
    decision: dict,
    *,
    assistance_request: dict,
    primary_session: dict,
) -> bool:
    if decision.get("schema") != "org-agent-mesh/swarm-allocation-decision/v1-draft":
        raise SwarmValidationError("wrong allocation decision schema")
    if primary_session.get("state") != "ACTIVE":
        raise SwarmValidationError("Primary session must be ACTIVE")
    if primary_session.get("role") != "PRIMARY":
        raise SwarmValidationError("only Primary may authorize swarm allocation")
    if decision.get("project_id") != primary_session.get("project_id"):
        raise SwarmValidationError("allocation project differs from Primary binding")
    if decision.get("project_id") != assistance_request.get("project_id"):
        raise SwarmValidationError("allocation project differs from assistance request")
    if decision.get("assistance_request_id") != assistance_request.get("request_id"):
        raise SwarmValidationError("allocation references wrong assistance request")
    decider = decision.get("decided_by") or {}
    if decider.get("role") != "PRIMARY":
        raise SwarmValidationError("allocation decider must declare PRIMARY role")
    if decider.get("agent_id") != primary_session.get("agent_id"):
        raise SwarmValidationError("allocation decider agent mismatch")
    if decider.get("agent_instance_id") != primary_session.get("agent_instance_id"):
        raise SwarmValidationError("allocation decider execution instance mismatch")

    research = int(decision.get("research_agents", -1))
    managers = int(decision.get("manager_agents", -1))
    budget = decision.get("budget") or {}
    if research > int(budget.get("max_research_agents", -1)):
        raise SwarmValidationError("research allocation exceeds authorized budget")
    if managers > int(budget.get("max_manager_agents", -1)):
        raise SwarmValidationError("manager allocation exceeds authorized budget")
    if research < 0 or managers < 0:
        raise SwarmValidationError("negative allocation")

    expected_topology = _topology(research, managers)
    if decision.get("topology") != expected_topology:
        raise SwarmValidationError("allocation topology does not match agent counts")
    status = decision.get("status")
    if status == "AUTHORIZED" and research <= 0:
        raise SwarmValidationError("authorized swarm requires at least one research agent")
    if status == "REJECTED" and (research != 0 or managers != 0 or decision.get("topology") != "REJECTED"):
        raise SwarmValidationError("rejected allocation must authorize zero agents")

    cells = decision.get("cells") or []
    if managers == 0 and len(cells) > 1:
        raise SwarmValidationError("Primary-direct topology may not create multiple unmanaged cells")
    if managers > 0 and len(cells) != managers:
        raise SwarmValidationError("managed topology requires one cell per manager")
    if cells and sum(int(cell.get("research_agents", 0)) for cell in cells) != research:
        raise SwarmValidationError("cell researcher counts do not equal total allocation")
    return True


_ALLOWED_TRANSITIONS = {
    "AUTHORIZED": {"ACTIVE", "TERMINATED"},
    "ACTIVE": {"ACTIVE", "SCALING", "DRAINING", "TERMINATED"},
    "SCALING": {"ACTIVE", "SCALING", "DRAINING", "TERMINATED"},
    "DRAINING": {"DRAINING", "TERMINATED"},
    "TERMINATED": set(),
}


def validate_swarm_transition(previous: dict, current: dict, *, primary_session: dict) -> bool:
    if previous.get("schema") != "org-agent-mesh/swarm-state/v1-draft" or current.get("schema") != "org-agent-mesh/swarm-state/v1-draft":
        raise SwarmValidationError("wrong swarm-state schema")
    if primary_session.get("state") != "ACTIVE" or primary_session.get("role") != "PRIMARY":
        raise SwarmValidationError("only ACTIVE Primary may authorize swarm-state transition")
    for key in ("swarm_id", "project_id", "task_id"):
        if previous.get(key) != current.get(key):
            raise SwarmValidationError(f"swarm transition changed immutable {key}")
    if current.get("project_id") != primary_session.get("project_id"):
        raise SwarmValidationError("swarm project differs from Primary binding")
    auth = current.get("authorized_by") or {}
    if auth.get("role") != "PRIMARY":
        raise SwarmValidationError("swarm transition authorizer must be PRIMARY")
    if auth.get("agent_id") != primary_session.get("agent_id") or auth.get("agent_instance_id") != primary_session.get("agent_instance_id"):
        raise SwarmValidationError("swarm transition authorizer does not match active Primary instance")
    if int(current.get("revision", -1)) != int(previous.get("revision", -1)) + 1:
        raise SwarmValidationError("swarm revision must increment exactly once")
    before = previous.get("status")
    after = current.get("status")
    if after not in _ALLOWED_TRANSITIONS.get(before, set()):
        raise SwarmValidationError(f"invalid swarm transition: {before} -> {after}")
    research = int(current.get("research_agents", -1))
    managers = int(current.get("manager_agents", -1))
    if after == "TERMINATED":
        if research != 0 or managers != 0:
            raise SwarmValidationError("terminated swarm must have zero active agents")
    else:
        if research <= 0:
            raise SwarmValidationError("non-terminated swarm requires research capacity")
        if current.get("topology") != _topology(research, managers):
            raise SwarmValidationError("swarm topology does not match current counts")
    if before == "DRAINING" and (research > int(previous.get("research_agents", 0)) or managers > int(previous.get("manager_agents", 0))):
        raise SwarmValidationError("draining swarm cannot scale up")
    return True
