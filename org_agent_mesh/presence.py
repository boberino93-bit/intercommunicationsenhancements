from pathlib import Path
import json
from datetime import datetime, timezone

from .project_scope import require_project_id, qualify


def append_presence(presence_dir, frame, *, expected_project_id=None):
    required = {
        "frame_id", "project_id", "agent_id", "agent_instance_id", "timestamp_utc",
        "declared_state", "lease_seconds", "project_state"
    }
    missing = required - set(frame)
    if missing:
        raise ValueError(f"Presence frame missing: {sorted(missing)}")

    project_id = require_project_id(frame["project_id"])
    if expected_project_id is not None and project_id != expected_project_id:
        raise PermissionError("Presence project mismatch")

    directory = Path(presence_dir)
    directory.mkdir(parents=True, exist_ok=True)
    qualified_id = qualify(project_id, frame["frame_id"])
    path = directory / f"{frame['timestamp_utc'].replace(':', '-')}__{qualified_id.replace('::', '--')}.json"
    if path.exists():
        raise FileExistsError("Presence frames are immutable")
    path.write_text(json.dumps(frame, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def derive_status(frame, now=None):
    state = frame.get("declared_state", "UNKNOWN")
    if state in {"RELEASED", "FAILED", "BLOCKED", "IDLE"}:
        return state
    now = now or datetime.now(timezone.utc)
    timestamp = datetime.fromisoformat(frame["timestamp_utc"].replace("Z", "+00:00"))
    age = (now - timestamp).total_seconds()
    if age > int(frame["lease_seconds"]):
        return "LATE"
    return "ACTIVE" if state == "ACTIVE" else "UNKNOWN"
