from __future__ import annotations

from .control_plane import StaleVersion, require_active_session
from .durable_backend import CorruptDurableRecord, DurableRecordBackend
from .project_scope import require_project_id, require_resource_id


class ThematicRouteRegistry:
    """Durable project-local subscriptions for theme-aware information routing."""
    NAMESPACE = "thematic-routes"

    def __init__(self, backend: DurableRecordBackend):
        if not isinstance(backend, DurableRecordBackend):
            raise TypeError("backend must implement DurableRecordBackend")
        self.backend = backend

    def publish(self, session, target_project_id, route_id, *, themes, destination, priority=100, expected_version=None, enabled=True, now=None):
        binding = require_active_session(session, target_project_id, operation="thematic route publication", capability="WRITE_ACCEPTED_STATE")
        route_id = require_resource_id(route_id, field="route_id")
        normalized = sorted({require_resource_id(t.lower(), field="theme") for t in themes})
        if not normalized:
            raise ValueError("at least one theme is required")
        destination = require_resource_id(destination, field="destination")
        priority = int(priority)
        payload = {
            "route_id": route_id,
            "project_id": target_project_id,
            "themes": normalized,
            "destination": destination,
            "priority": priority,
            "enabled": bool(enabled),
            "updated_by_agent_instance_id": binding.agent_instance_id,
        }
        current = self.backend.read(self.NAMESPACE, target_project_id, route_id)
        if current is None:
            if expected_version not in (None, 0):
                raise StaleVersion("thematic route does not exist")
            return self.backend.create(self.NAMESPACE, target_project_id, route_id, payload, now=now)
        if current.payload == payload:
            return current
        if expected_version is None:
            raise StaleVersion("expected_version required to replace thematic route")
        return self.backend.compare_and_set(self.NAMESPACE, target_project_id, route_id, expected_version=expected_version, payload=payload, now=now)

    def resolve(self, project_id, themes):
        project_id = require_project_id(project_id)
        wanted = {require_resource_id(t.lower(), field="theme") for t in themes}
        matches = []
        for rec in self.backend.list_records(self.NAMESPACE, project_id=project_id):
            if not isinstance(rec.payload, dict):
                raise CorruptDurableRecord("thematic route payload corrupt")
            payload = rec.payload
            if payload.get("enabled") and wanted.intersection(payload.get("themes", [])):
                matches.append(rec)
        matches.sort(key=lambda rec: (int(rec.payload.get("priority", 100)), rec.payload.get("route_id", "")))
        return matches
