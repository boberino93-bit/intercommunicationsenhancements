"""Design-only relational checks for IPG3 authenticated agent principals."""

from __future__ import annotations

from datetime import datetime, timezone

from ipg3_validators import IPG3ValidationError, _parse_utc


def validate_agent_principal(
    principal: dict,
    *,
    expected_project_id: str,
    expected_agent_id: str | None = None,
    expected_agent_instance_id: str | None = None,
    local_capability_ceiling: set[str] | None = None,
    allowed_algorithms: set[str] | None = None,
    now: datetime | None = None,
) -> bool:
    if principal.get("schema") != "org-agent-mesh/agent-principal/v1-draft":
        raise IPG3ValidationError("wrong agent principal schema")
    if principal.get("project_id") != expected_project_id:
        raise IPG3ValidationError("principal project does not match local project binding")
    if expected_agent_id is not None and principal.get("agent_id") != expected_agent_id:
        raise IPG3ValidationError("principal logical agent does not match expected agent")
    if expected_agent_instance_id is not None and principal.get("agent_instance_id") != expected_agent_instance_id:
        raise IPG3ValidationError("principal execution instance does not match expected instance")

    issued = _parse_utc(principal["issued_at_utc"])
    expires = _parse_utc(principal["expires_at_utc"])
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise IPG3ValidationError("now must be timezone-aware")
    current = current.astimezone(timezone.utc)
    if expires <= issued:
        raise IPG3ValidationError("principal expiry must follow issue time")
    if issued > current:
        raise IPG3ValidationError("principal is not yet valid")
    if expires <= current:
        raise IPG3ValidationError("principal is expired")

    claimed = set(principal.get("capability_claims", []))
    if local_capability_ceiling is not None and not claimed.issubset(set(local_capability_ceiling)):
        raise IPG3ValidationError("remote principal claims capabilities outside local ceiling")

    key_binding = principal.get("key_binding") or {}
    integrity = principal.get("integrity") or {}
    signature = integrity.get("signature") or {}
    if key_binding.get("key_id") != signature.get("key_id"):
        raise IPG3ValidationError("principal signature key does not match bound key")
    if key_binding.get("algorithm") != signature.get("algorithm"):
        raise IPG3ValidationError("principal signature algorithm does not match bound algorithm")
    if allowed_algorithms is not None and key_binding.get("algorithm") not in allowed_algorithms:
        raise IPG3ValidationError("principal signature algorithm is not locally allowed")

    revocation = principal.get("revocation") or {}
    if revocation.get("credential_version", 0) < 1 or not revocation.get("registry"):
        raise IPG3ValidationError("principal lacks valid revocation metadata")

    # Cryptographic signature verification and revocation lookup are deployment services.
    # Passing this validator therefore proves relational consistency only, not authenticity.
    return True
