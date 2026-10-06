from __future__ import annotations
from dataclasses import dataclass
from pathlib import PurePosixPath
from .project_scope import ProjectScopeError, require_project_id, require_repository_identity
CAPABILITY="NON_AUTHORITATIVE_COORDINATION_PUBLICATION"; LEGACY_CAPABILITY="PUBLISH_MESSAGE"
ALLOWED_ROLES={"PRIMARY","MANAGER","RESEARCH","RESEARCHER_1","RESEARCHER_2","RESEARCHER_3","RECOVERY","VALIDATOR","VALIDATION","QA","BUILDER"}
DEFAULT_GITHUB_PREFIX="agentbus-backup/coordination-messages/"
class CoordinationPublicationError(PermissionError): pass
@dataclass(frozen=True)
class CoordinationRoute:
    project_id:str; repository:str; artifactory_namespace:str|None; github_backup_prefix:str=DEFAULT_GITHUB_PREFIX
    def __post_init__(self): require_project_id(self.project_id); require_repository_identity(self.repository); _validated_prefix(self.github_backup_prefix)
def _validated_prefix(prefix:str)->str:
    if not isinstance(prefix,str) or not prefix.strip(): raise CoordinationPublicationError("backup prefix is required")
    raw=prefix.strip().replace("\\","/")
    if raw.startswith("/"): raise CoordinationPublicationError("backup prefix must be repository-relative")
    parts=PurePosixPath(raw).parts
    if any(part in {"",".",".."} for part in parts): raise CoordinationPublicationError("backup prefix contains unsafe traversal")
    return raw.rstrip("/")+"/"
def _validated_new_file_path(path:str,prefix:str)->str:
    if not isinstance(path,str) or not path.strip(): raise CoordinationPublicationError("backup path is required")
    raw=path.strip().replace("\\","/")
    if raw.startswith("/"): raise CoordinationPublicationError("backup path must be repository-relative")
    parts=PurePosixPath(raw).parts
    if any(part in {"",".",".."} for part in parts): raise CoordinationPublicationError("backup path contains unsafe traversal")
    normalized="/".join(parts); required=_validated_prefix(prefix)
    if not normalized.startswith(required) or normalized==required.rstrip("/"): raise CoordinationPublicationError("backup path is outside/incomplete coordination namespace")
    return normalized
def require_coordination_publication(*,actor_project_id:str,actor_role:str,actor_capabilities,route:CoordinationRoute,target_repository:str,target_artifactory_namespace:str|None=None,github_backup_path:str|None=None,operation:str="CREATE_NEW_MESSAGE",authority_conveyed:bool=False)->bool:
    project_id=require_project_id(actor_project_id); role=str(actor_role).strip().upper(); capabilities=frozenset(actor_capabilities or ())
    if role not in ALLOWED_ROLES: raise CoordinationPublicationError("role is not eligible for bounded coordination persistence")
    if CAPABILITY not in capabilities and LEGACY_CAPABILITY not in capabilities: raise CoordinationPublicationError("coordination publication capability is missing")
    if route.project_id != project_id: raise ProjectScopeError("coordination route belongs to a foreign project")
    if require_repository_identity(target_repository) != route.repository: raise ProjectScopeError("coordination backup repository does not match bound project")
    if operation != "CREATE_NEW_MESSAGE": raise CoordinationPublicationError("coordination publication is create-new-message only")
    if authority_conveyed: raise CoordinationPublicationError("coordination messages cannot convey authority")
    if route.artifactory_namespace is None: raise CoordinationPublicationError("DUAL_PERSISTENCE_ROUTE_INCOMPLETE:ARTIFACTORY_NAMESPACE_MISSING")
    if target_artifactory_namespace is None or github_backup_path is None: raise CoordinationPublicationError("DUAL_PERSISTENCE_DESTINATIONS_REQUIRED")
    if target_artifactory_namespace != route.artifactory_namespace: raise ProjectScopeError("Artifactory namespace does not match bound project")
    _validated_new_file_path(github_backup_path,route.github_backup_prefix); return True
