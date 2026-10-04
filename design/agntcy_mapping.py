"""Design-only AGNTCY/SLIM -> IPG3 identity/discovery normalization prototype.

SLIM transport/application identity verification is represented as evidence. Local Organization
Agent Mesh authority is still derived from project binding and local capability/delegation policy.
"""

from __future__ import annotations

from copy import deepcopy


class AGNTCYMappingError(ValueError):
    pass


_STRENGTH = {
    "SHARED_SECRET": "GROUP_AUTHENTICATED",
    "JWT": "INDIVIDUAL_CREDENTIAL",
    "SPIRE": "WORKLOAD_ATTESTED",
}


def normalize_slim_identity(identity: dict) -> dict:
    method = str(identity.get("credential_method", "")).upper()
    if method not in _STRENGTH:
        raise AGNTCYMappingError("unsupported SLIM credential method")
    application_identity = identity.get("application_identity")
    if not application_identity:
        raise AGNTCYMappingError("SLIM application identity is required")
    verified = bool(identity.get("verified", False))
    return {
        "schema": "org-agent-mesh/external-principal-evidence/v1-draft",
        "protocol": "AGNTCY_SLIM",
        "credential_method": method,
        "application_identity": application_identity,
        "issuer": identity.get("issuer"),
        "trust_domain": identity.get("trust_domain"),
        "verification": {
            "verified": verified,
            "strength": _STRENGTH[method] if verified else "UNVERIFIED",
            "evidence_ref": identity.get("evidence_ref"),
        },
        "trust_class": "VERIFIED_FACT" if verified else "EXTERNAL_UNTRUSTED",
        "local_project_id": None,
        "local_agent_id": None,
        "local_agent_instance_id": None,
        "local_capability_grants": [],
        "local_authorized": False,
    }


def normalize_directory_record(record: dict, *, signature_verified: bool, verification_ref: str | None = None) -> dict:
    remote_id = record.get("id") or record.get("cid") or record.get("name")
    if not remote_id:
        raise AGNTCYMappingError("directory record requires remote identity")
    return {
        "schema": "org-agent-mesh/external-agent-discovery/v1-draft",
        "protocol": "AGNTCY_DIRECTORY",
        "remote_identity": remote_id,
        "schema_version": record.get("schema_version"),
        "skills": deepcopy(record.get("skills") or []),
        "locators": deepcopy(record.get("locators") or []),
        "annotations": deepcopy(record.get("annotations") or {}),
        "signature_verified": bool(signature_verified),
        "verification_ref": verification_ref,
        "trust_class": "VERIFIED_FACT" if signature_verified else "EXTERNAL_UNTRUSTED",
        "local_capability_grants": [],
        "local_authorized": False,
    }


def map_verified_identity_to_principal_claim(
    evidence: dict,
    *,
    project_id: str,
    agent_id: str,
    agent_instance_id: str,
    local_capability_ceiling: set[str],
    requested_capabilities: set[str] | None = None,
) -> dict:
    """Map verified remote identity to a bounded principal claim.

    This still does not cryptographically issue an IPG3 Agent Principal. It creates input to the
    local issuer/authorization service. Requested capabilities are intersected with local policy.
    """
    verification = evidence.get("verification") or {}
    if evidence.get("protocol") != "AGNTCY_SLIM" or not verification.get("verified"):
        raise AGNTCYMappingError("only verified SLIM identity evidence may enter principal issuance")
    requested = set(requested_capabilities or ())
    ceiling = set(local_capability_ceiling)
    approved = requested & ceiling
    return {
        "schema": "org-agent-mesh/principal-issuance-request/v1-draft",
        "source_protocol": "AGNTCY_SLIM",
        "source_identity": evidence["application_identity"],
        "source_strength": verification["strength"],
        "project_id": project_id,
        "agent_id": agent_id,
        "agent_instance_id": agent_instance_id,
        "requested_capabilities": sorted(requested),
        "local_capability_ceiling": sorted(ceiling),
        "candidate_capabilities": sorted(approved),
        "requires_local_issuer": True,
        "authorized": False,
    }
