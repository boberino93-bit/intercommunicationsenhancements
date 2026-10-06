from __future__ import annotations

from dataclasses import asdict
from enum import Enum

from ._epistemic_base import EpistemicError, StaleModelRevision, _digest
from ._epistemic_reconciliation import SharedEpistemicModel

class AcceptedEpistemicStore:
    """Accepted epistemic head layered on the existing durable backend abstraction.

    The canonical active-session authorization function is mandatory; there is no caller-supplied
    ActorContext fallback for durable accepted-state writes.
    """
    NAMESPACE = "epistemic-model"
    RESOURCE_ID = "accepted-head"

    def __init__(self, backend, *, require_session):
        required=("create","read","compare_and_set")
        if not all(callable(getattr(backend,name,None)) for name in required):
            raise TypeError("backend must satisfy DurableRecordBackend create/read/compare_and_set")
        if not callable(require_session):
            raise TypeError("canonical require_active_session callback is required")
        self.backend=backend
        self.require_session=require_session

    def _authorize(self, session, project_id: str):
        return self.require_session(
            session, project_id,
            operation="accepted epistemic model mutation",
            capability="WRITE_ACCEPTED_STATE",
        )

    @staticmethod
    def _jsonable(value):
        if isinstance(value,Enum):
            return value.value
        if hasattr(value,"__dataclass_fields__"):
            return {k:AcceptedEpistemicStore._jsonable(v) for k,v in asdict(value).items()}
        if isinstance(value,dict):
            return {str(k):AcceptedEpistemicStore._jsonable(v) for k,v in value.items()}
        if isinstance(value,(tuple,list,set,frozenset)):
            return [AcceptedEpistemicStore._jsonable(v) for v in value]
        return value

    def read(self, project_id: str):
        return self.backend.read(self.NAMESPACE,project_id,self.RESOURCE_ID)

    def accept(self, session, model: SharedEpistemicModel, *, expected_version: int | None, event_id: str):
        self._authorize(session,model.project_id)
        if not event_id:
            raise EpistemicError("event_id required")
        model_payload=self._jsonable(model)
        dg=_digest(model_payload)
        current=self.read(model.project_id)
        if current is None:
            if expected_version not in (None,0):
                raise StaleModelRevision("expected version mismatch")
            payload={"generation":model.generation,"model":model_payload,"event_digests":{event_id:dg},"authority":False}
            try:
                return self.backend.create(self.NAMESPACE,model.project_id,self.RESOURCE_ID,payload)
            except Exception as exc:
                if exc.__class__.__name__ == "StaleVersion":
                    raise StaleModelRevision("durable create raced with another writer") from exc
                raise
        seen=dict(current.payload.get("event_digests",{}))
        if event_id in seen:
            if seen[event_id] != dg:
                raise EpistemicError("event id collision")
            return "IDEMPOTENT"
        if expected_version != current.version:
            raise StaleModelRevision("stale writer rejected")
        if model.generation <= int(current.payload.get("generation",-1)):
            raise StaleModelRevision("model generation must increase")
        seen[event_id]=dg
        next_payload={"generation":model.generation,"model":model_payload,"event_digests":seen,"authority":False}
        try:
            return self.backend.compare_and_set(self.NAMESPACE,model.project_id,self.RESOURCE_ID,expected_version=expected_version,payload=next_payload)
        except Exception as exc:
            if exc.__class__.__name__ == "StaleVersion":
                raise StaleModelRevision("durable CAS rejected stale writer") from exc
            raise

