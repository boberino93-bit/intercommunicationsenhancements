import json
import re
import unittest
from dataclasses import dataclass, replace
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from org_agent_mesh.epistemic_coordination import *

NOW = "2026-10-06T18:00:00Z"


class SchemaValidationError(AssertionError):
    pass


_ALLOWED_SCHEMA_KEYWORDS = {
    "$schema", "$id", "title", "format", "type", "required", "properties",
    "additionalProperties", "const", "enum", "minimum", "maximum", "minLength",
    "maxLength", "pattern", "items", "uniqueItems", "allOf", "if", "then",
}
_ALLOWED_TYPES = {"object", "array", "string", "integer", "null"}


def _check_schema_node(schema):
    if not isinstance(schema, dict):
        raise SchemaValidationError("schema node must be an object")
    unknown = set(schema) - _ALLOWED_SCHEMA_KEYWORDS
    if unknown:
        raise SchemaValidationError(f"unsupported schema keywords: {sorted(unknown)}")
    declared_type = schema.get("type")
    if declared_type is not None:
        types = [declared_type] if isinstance(declared_type, str) else declared_type
        if not isinstance(types, list) or not types or any(t not in _ALLOWED_TYPES for t in types):
            raise SchemaValidationError("unsupported type declaration")
    if "required" in schema and (not isinstance(schema["required"], list) or any(not isinstance(x, str) for x in schema["required"])):
        raise SchemaValidationError("required must be a list of strings")
    if "properties" in schema:
        if not isinstance(schema["properties"], dict):
            raise SchemaValidationError("properties must be an object")
        for child in schema["properties"].values():
            _check_schema_node(child)
    if "additionalProperties" in schema and not isinstance(schema["additionalProperties"], bool):
        _check_schema_node(schema["additionalProperties"])
    if "items" in schema:
        _check_schema_node(schema["items"])
    if "allOf" in schema:
        if not isinstance(schema["allOf"], list):
            raise SchemaValidationError("allOf must be an array")
        for child in schema["allOf"]:
            _check_schema_node(child)
    if "if" in schema:
        _check_schema_node(schema["if"])
    if "then" in schema:
        _check_schema_node(schema["then"])


def validate_schema_contract(schema):
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise SchemaValidationError("schema must declare JSON Schema draft 2020-12")
    _check_schema_node(schema)
    return True


def _type_matches(value, declared):
    if declared == "object":
        return isinstance(value, dict)
    if declared == "array":
        return isinstance(value, list)
    if declared == "string":
        return isinstance(value, str)
    if declared == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if declared == "null":
        return value is None
    return False


def _validate_instance(instance, schema):
    declared = schema.get("type")
    if declared is not None:
        types = [declared] if isinstance(declared, str) else declared
        if not any(_type_matches(instance, t) for t in types):
            raise SchemaValidationError(f"value {instance!r} does not match declared type {types!r}")
    if "const" in schema and instance != schema["const"]:
        raise SchemaValidationError("const mismatch")
    if "enum" in schema and instance not in schema["enum"]:
        raise SchemaValidationError("enum mismatch")
    if isinstance(instance, int) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            raise SchemaValidationError("minimum violated")
        if "maximum" in schema and instance > schema["maximum"]:
            raise SchemaValidationError("maximum violated")
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            raise SchemaValidationError("minLength violated")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            raise SchemaValidationError("maxLength violated")
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            raise SchemaValidationError("pattern mismatch")
    if isinstance(instance, list):
        if schema.get("uniqueItems"):
            canonical = [json.dumps(x, sort_keys=True, separators=(",", ":")) for x in instance]
            if len(canonical) != len(set(canonical)):
                raise SchemaValidationError("uniqueItems violated")
        if "items" in schema:
            for item in instance:
                _validate_instance(item, schema["items"])
    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                raise SchemaValidationError(f"missing required property: {key}")
        properties = schema.get("properties", {})
        for key, value in instance.items():
            if key in properties:
                _validate_instance(value, properties[key])
                continue
            additional = schema.get("additionalProperties", True)
            if additional is False:
                raise SchemaValidationError(f"additional property not allowed: {key}")
            if isinstance(additional, dict):
                _validate_instance(value, additional)
    for child in schema.get("allOf", []):
        _validate_instance(instance, child)
    if "if" in schema and "then" in schema:
        try:
            _validate_instance(instance, schema["if"])
        except SchemaValidationError:
            pass
        else:
            _validate_instance(instance, schema["then"])


def validate_json_schema(schema, instance):
    validate_schema_contract(schema)
    _validate_instance(instance, schema)
    return True


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


