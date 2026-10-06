import json
import unittest
from dataclasses import dataclass, replace
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.epistemic_coordination import *

NOW = "2026-10-06T18:00:00Z"


def src(sid, *, h=None, origin=None, derived=()):
    return SourceIdentity(sid, origin, "Vendor", "Feature Guide", "2026-09-01", "2026.5", origin, h, derived)


def ev(eid, sid, tier=EvidenceTier.CURRENT_AUTHORITATIVE, **kw):
    return EvidenceItem(eid, "inst-" + eid, sid, tier, eid, **kw)


def mdl(*, project="p", generation=0, parent=None, sources=(), evidence=(), source_instances=None, claims=(), **kwargs):
    if source_instances is None:
        seen = set()
        instances = []
        for item in evidence:
            if item.source_instance_id not in seen:
                instances.append(SourceInstance(item.source_instance_id, item.source_identity_id, "memory://" + item.source_instance_id))
                seen.add(item.source_instance_id)
        source_instances = tuple(instances)
    return SharedEpistemicModel(project, generation, parent, sources=tuple(sources), source_instances=tuple(source_instances), evidence=tuple(evidence), claims=tuple(claims), **kwargs)


class Rec:
    def __init__(self, namespace, project_id, resource_id, version, payload):
        self.namespace = namespace; self.project_id = project_id; self.resource_id = resource_id; self.version = version; self.payload = payload


class FakeBackend:
    def __init__(self): self.rows = {}
    def read(self, n, p, r): return self.rows.get((n, p, r))
    def create(self, n, p, r, payload, **kw):
        k = (n, p, r)
        if k in self.rows:
            class StaleVersion(RuntimeError): pass
            raise StaleVersion("exists")
        rec = Rec(n, p, r, 1, payload); self.rows[k] = rec; return rec
    def compare_and_set(self, n, p, r, *, expected_version, payload, **kw):
        k = (n, p, r); cur = self.rows.get(k)
        if cur is None or cur.version != expected_version:
            class StaleVersion(RuntimeError): pass
            raise StaleVersion("stale")
        rec = Rec(n, p, r, cur.version + 1, payload); self.rows[k] = rec; return rec


@dataclass(frozen=True)
class Session:
    project_id: str
    role: str
    capabilities: frozenset[str]


def canonical_require_session(session, project_id, *, operation, capability):
    if not isinstance(session, Session):
        raise AuthorityError("canonical session required")
    if session.project_id != project_id:
        raise AuthorityError("project isolation")
    if session.role != "PRIMARY":
        raise AuthorityError("accepted state is Primary-only")
    if capability not in session.capabilities:
        raise AuthorityError("missing capability")
    return session


@dataclass(frozen=True)
class Permit:
    project_id: str
    role: str
    authority_conveyed: bool = False
    artifactory_allowed: bool = True
    github_backup_allowed: bool = False


