from __future__ import annotations

from dataclasses import dataclass

from .project_role_routing import ResolvedRoute, RoutingError


@dataclass(frozen=True)
class CommunicationAssessment:
    project_id: str
    role_id: str
    forum_namespace: str
    forum_authority: str
    access_mode: str
    coverage: str
    authoritative_live_access: bool
    repository_view_mode: str
    repository_view_path: str | None
    repository_view_observed: bool
    repository_view_fresh: bool | None
    handoff_observed: bool
    confidence: str
    full_project_forum_visibility_proven: bool
    mutation_blocked: bool
    reason: str

    def acknowledgement(self) -> str:
        return (
            "COMMUNICATIONS ASSESSED: "
            f"project={self.project_id}; role={self.role_id}; forum={self.forum_namespace}; "
            f"access={self.access_mode}; coverage={self.coverage}; confidence={self.confidence}; "
            f"full_forum_visibility={str(self.full_project_forum_visibility_proven).lower()}; "
            f"mutation_blocked={str(self.mutation_blocked).lower()}"
        )


def assess_communication_visibility(
    route: ResolvedRoute,
    *,
    direct_forum_access: bool = False,
    direct_forum_namespace: str | None = None,
    direct_scope_complete: bool = False,
    repository_view_observed: bool = False,
    repository_view_fresh: bool | None = None,
    handoff_observed: bool = False,
) -> CommunicationAssessment:
    """Classify what this execution can truthfully claim to see for its registered project forum.

    Observation arguments describe capabilities/evidence actually verified by the current runtime.
    They are never mutation authority and do not override project identity or routing.
    """
    if direct_scope_complete and not direct_forum_access:
        raise RoutingError("full_scope_without_direct_forum_access")
    if direct_forum_access and not direct_forum_namespace:
        raise RoutingError("direct_forum_namespace_required")
    if not direct_forum_access and direct_forum_namespace is not None:
        raise RoutingError("direct_forum_namespace_without_access")
    if repository_view_fresh is not None and not repository_view_observed:
        raise RoutingError("repository_view_freshness_without_observation")
    if repository_view_observed and route.forum_repository_view_mode == "NONE":
        raise RoutingError("unexpected_repository_forum_view")

    if direct_forum_access:
        if direct_forum_namespace != route.forum_namespace:
            return CommunicationAssessment(
                project_id=route.project_id,
                role_id=route.role_id,
                forum_namespace=route.forum_namespace,
                forum_authority=route.forum_authority,
                access_mode="CONFLICT",
                coverage="WRONG_PROJECT_OR_NAMESPACE",
                authoritative_live_access=False,
                repository_view_mode=route.forum_repository_view_mode,
                repository_view_path=route.forum_repository_view_path,
                repository_view_observed=repository_view_observed,
                repository_view_fresh=repository_view_fresh,
                handoff_observed=handoff_observed,
                confidence="HIGH",
                full_project_forum_visibility_proven=False,
                mutation_blocked=True,
                reason="direct forum namespace does not match the resolved project",
            )
        return CommunicationAssessment(
            project_id=route.project_id,
            role_id=route.role_id,
            forum_namespace=route.forum_namespace,
            forum_authority=route.forum_authority,
            access_mode="DIRECT",
            coverage="FULL_REGISTERED_PROJECT_FORUM" if direct_scope_complete else "PARTIAL_REGISTERED_PROJECT_FORUM",
            authoritative_live_access=True,
            repository_view_mode=route.forum_repository_view_mode,
            repository_view_path=route.forum_repository_view_path,
            repository_view_observed=repository_view_observed,
            repository_view_fresh=repository_view_fresh,
            handoff_observed=handoff_observed,
            confidence="HIGH",
            full_project_forum_visibility_proven=direct_scope_complete,
            mutation_blocked=False,
            reason=(
                "direct authoritative forum access and full forum scope were verified"
                if direct_scope_complete
                else "direct authoritative forum access was verified, but full forum scope was not proven"
            ),
        )

    mode = route.forum_repository_view_mode
    if repository_view_observed and mode == "LIVE_MIRROR":
        if repository_view_fresh is False:
            access_mode = "STALE_MIRROR"
            coverage = "STALE_REPOSITORY_MIRROR"
            confidence = "LOW"
            reason = "registered live mirror was observed but freshness failed"
        else:
            access_mode = "LIVE_MIRROR"
            coverage = (
                "CURRENT_REPOSITORY_MIRROR"
                if repository_view_fresh is True
                else "UNVERIFIED_FRESHNESS_REPOSITORY_MIRROR"
            )
            confidence = "MEDIUM"
            reason = "registered live mirror is visible; it is not the authoritative internal forum"
    elif repository_view_observed and mode == "SNAPSHOT_BACKUP":
        access_mode = "SNAPSHOT_ONLY"
        coverage = "HISTORICAL_REPOSITORY_SNAPSHOT"
        confidence = "LOW"
        reason = "only the registered snapshot/backup is visible; current forum state is not proven"
    elif handoff_observed:
        access_mode = "HANDOFF_ONLY"
        coverage = "ACCEPTED_STATE_OR_HANDOFF_ONLY"
        confidence = "LOW"
        reason = "handoff/state is visible, but no project forum view was observed"
    else:
        access_mode = "NONE"
        coverage = "NO_PROJECT_COMMUNICATION_SOURCE_OBSERVED"
        confidence = "HIGH"
        reason = "no direct forum, registered repository view, or handoff communication source was observed"

    return CommunicationAssessment(
        project_id=route.project_id,
        role_id=route.role_id,
        forum_namespace=route.forum_namespace,
        forum_authority=route.forum_authority,
        access_mode=access_mode,
        coverage=coverage,
        authoritative_live_access=False,
        repository_view_mode=route.forum_repository_view_mode,
        repository_view_path=route.forum_repository_view_path,
        repository_view_observed=repository_view_observed,
        repository_view_fresh=repository_view_fresh,
        handoff_observed=handoff_observed,
        confidence=confidence,
        full_project_forum_visibility_proven=False,
        mutation_blocked=False,
        reason=reason,
    )
