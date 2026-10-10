"""Design-only A2A 1.0 -> IPG3 normalization prototype.

This module maps interoperability objects into untrusted local evidence. It does not implement
an A2A server/client and does not grant local capabilities from Agent Card declarations.
"""

from __future__ import annotations

from copy import deepcopy


class A2AMappingError(ValueError):
    pass


def normalize_agent_card(card: dict, *, source_url: str | None = None) -> dict:
    if not isinstance(card, dict) or not card.get("name") or not card.get("version"):
        raise A2AMappingError("A2A Agent Card requires name and version")
    interfaces = card.get("supportedInterfaces") or card.get("supported_interfaces") or []
    capabilities = deepcopy(card.get("capabilities") or {})
    security = deepcopy(card.get("securitySchemes") or card.get("security_schemes") or {})
    return {
        "schema": "org-agent-mesh/external-agent-discovery/v1-draft",
        "protocol": "A2A",
        "protocol_version": card.get("protocolVersion") or card.get("protocol_version") or "1.0",
        "remote_identity": {"name": card["name"], "version": card["version"]},
        "interfaces": deepcopy(interfaces),
        "remote_capability_claims": capabilities,
        "remote_security_requirements": security,
        "skills": deepcopy(card.get("skills") or []),
        "source_url": source_url,
        "trust_class": "EXTERNAL_UNTRUSTED",
        "local_capability_grants": [],
        "authorization_note": "A2A Agent Card capabilities are discovery claims, not local Organization Agent Mesh permissions.",
    }


def normalize_task(task: dict, *, remote_agent_ref: str) -> dict:
    if not task.get("id"):
        raise A2AMappingError("A2A Task requires id")
    status = deepcopy(task.get("status") or {})
    return {
        "schema": "org-agent-mesh/external-task/v1-draft",
        "protocol": "A2A",
        "remote_agent_ref": remote_agent_ref,
        "remote_task_id": task["id"],
        "remote_context_id": task.get("contextId") or task.get("context_id"),
        "remote_status": status,
        "remote_artifacts": deepcopy(task.get("artifacts") or []),
        "remote_history": deepcopy(task.get("history") or []),
        "trust_class": "EXTERNAL_UNTRUSTED",
        "local_task_id": None,
        "local_delegation_contract_id": None,
        "local_authorized": False,
    }


def normalize_message(message: dict, *, remote_agent_ref: str, remote_task_id: str | None = None) -> dict:
    message_id = message.get("messageId") or message.get("message_id") or message.get("id")
    if not message_id:
        raise A2AMappingError("A2A Message requires message identity")
    return {
        "schema": "org-agent-mesh/external-message/v1-draft",
        "protocol": "A2A",
        "remote_agent_ref": remote_agent_ref,
        "remote_message_id": message_id,
        "remote_task_id": remote_task_id or message.get("taskId") or message.get("task_id"),
        "remote_context_id": message.get("contextId") or message.get("context_id"),
        "role": message.get("role"),
        "parts": deepcopy(message.get("parts") or []),
        "metadata": deepcopy(message.get("metadata") or {}),
        "trust_class": "EXTERNAL_UNTRUSTED",
        "local_project_id": None,
        "local_authorized": False,
    }


def normalize_artifact(artifact: dict, *, remote_agent_ref: str, remote_task_id: str) -> dict:
    artifact_id = artifact.get("artifactId") or artifact.get("artifact_id") or artifact.get("id")
    if not artifact_id:
        raise A2AMappingError("A2A Artifact requires identity")
    return {
        "schema": "org-agent-mesh/external-artifact/v1-draft",
        "protocol": "A2A",
        "remote_agent_ref": remote_agent_ref,
        "remote_task_id": remote_task_id,
        "remote_artifact_id": artifact_id,
        "name": artifact.get("name"),
        "description": artifact.get("description"),
        "parts": deepcopy(artifact.get("parts") or []),
        "metadata": deepcopy(artifact.get("metadata") or {}),
        "trust_class": "EXTERNAL_UNTRUSTED",
        "provenance_required": True,
        "local_artifact_id": None,
        "local_authorized": False,
    }


def bind_external_request_to_local_authority(normalized: dict, *, project_id: str, delegation_contract_id: str, approved_capabilities: set[str]) -> dict:
    """Create an authorization projection only after local control-plane policy has approved it.

    The caller must supply capabilities derived from local policy. Remote claims are never unioned in.
    """
    if not project_id or not delegation_contract_id:
        raise A2AMappingError("local project binding and delegation contract are required")
    bound = deepcopy(normalized)
    bound["local_project_id"] = project_id
    bound["local_delegation_contract_id"] = delegation_contract_id
    bound["local_capabilities"] = sorted(set(approved_capabilities))
    bound["local_authorized"] = True
    return bound
