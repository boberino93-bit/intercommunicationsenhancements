from .reliability_v18_core import *

@dataclass(frozen=True)
class ResourceRequest:
    project_id: str
    work_id: str
    priority: int = 0
    cpu: int = 0
    provider_calls: int = 0
    tool_calls: int = 0
    write_slots: int = 0
    validation_workers: int = 0
    optional: bool = False
    enqueue_seq: int = 0

    def resources(self) -> dict[str, int]:
        return {'cpu': self.cpu, 'provider_calls': self.provider_calls, 'tool_calls': self.tool_calls, 'write_slots': self.write_slots, 'validation_workers': self.validation_workers}

@dataclass(frozen=True)
class ResourceCeilings:
    cpu: int
    provider_calls: int
    tool_calls: int
    write_slots: int
    validation_workers: int

    def as_dict(self) -> dict[str, int]:
        return asdict(self)

class WeightedFairAdmissionController:
    """Bounded weighted-fair scheduler with starvation protection and backpressure."""

    def __init__(self, ceilings: ResourceCeilings, *, project_weights: Mapping[str, int] | None=None, starvation_turns: int=8, queue_limit: int=1000):
        self.ceilings = ceilings
        self.weights = {k: max(1, int(v)) for k, v in (project_weights or {}).items()}
        self.starvation_turns = max(1, starvation_turns)
        self.queue_limit = max(1, queue_limit)
        self._used = defaultdict(int)
        self._queues: dict[str, deque[ResourceRequest]] = defaultdict(deque)
        self._deficit = defaultdict(int)
        self._wait_turns = defaultdict(int)
        self._seq = 0
        self._inflight: dict[str, ResourceRequest] = {}
        self._lock = RLock()

    def _fits(self, req: ResourceRequest) -> bool:
        ceilings = self.ceilings.as_dict()
        return all((self._used[k] + v <= ceilings[k] for k, v in req.resources().items()))

    def _cost(self, req: ResourceRequest) -> int:
        return 1

    def submit(self, req: ResourceRequest) -> ControlDecision:
        with self._lock:
            if req.work_id in self._inflight or any((req.work_id == x.work_id for q in self._queues.values() for x in q)):
                raise AdmissionError('duplicate work_id')
            if sum((len(q) for q in self._queues.values())) >= self.queue_limit:
                if req.optional:
                    return ControlDecision('SHED', ReasonCode.SHED_OPTIONAL_WORK.value, 'admission', 'optional work shed because admission queue is saturated', 'retry after load falls')
                return ControlDecision('DEFER', ReasonCode.DEFER_RESOURCE_CAPACITY.value, 'admission', 'queue is saturated', 'retry after capacity returns')
            self._seq += 1
            self._queues[req.project_id].append(replace(req, enqueue_seq=self._seq))
            return ControlDecision('QUEUE', ReasonCode.QUEUE_FAIRNESS.value, 'admission', 'work queued under weighted fairness', 'await admission turn')

    def next_admissible(self) -> tuple[ResourceRequest | None, ControlDecision]:
        with self._lock:
            projects = [p for p, q in self._queues.items() if q]
            if not projects:
                return (None, ControlDecision('IDLE', ReasonCode.ADMIT_OK.value, 'admission', 'no queued work'))
            for p in projects:
                self._wait_turns[p] += 1
                self._deficit[p] += self.weights.get(p, 1)
            starved = sorted((p for p in projects if self._wait_turns[p] >= self.starvation_turns), key=lambda p: (-self._wait_turns[p], self._queues[p][0].enqueue_seq))
            ordered = starved + sorted((p for p in projects if p not in starved), key=lambda p: (-self._queues[p][0].priority, -self._deficit[p], self._queues[p][0].enqueue_seq))
            for p in ordered:
                req = self._queues[p][0]
                cost = self._cost(req)
                if self._deficit[p] < cost and p not in starved:
                    continue
                if not self._fits(req):
                    continue
                self._queues[p].popleft()
                self._deficit[p] = max(0, self._deficit[p] - cost)
                inherited = p in starved
                self._wait_turns[p] = 0
                for k, v in req.resources().items():
                    self._used[k] += v
                self._inflight[req.work_id] = req
                return (req, ControlDecision('ADMIT', ReasonCode.PRIORITY_INHERITANCE.value if inherited else ReasonCode.ADMIT_OK.value, 'admission', 'eligible queued work admitted within global resource ceilings', 'execute within granted ceiling'))
            return (None, ControlDecision('THROTTLE', ReasonCode.DEFER_RESOURCE_CAPACITY.value, 'admission', 'no queued work currently fits available aggregate capacity', 'release resources or wait'))

    def release(self, work_id: str) -> None:
        with self._lock:
            req = self._inflight.pop(work_id, None)
            if not req:
                return
            for k, v in req.resources().items():
                self._used[k] = max(0, self._used[k] - v)

    def snapshot(self) -> dict:
        with self._lock:
            return {'ceilings': self.ceilings.as_dict(), 'used': dict(self._used), 'queued': {p: len(q) for p, q in self._queues.items() if q}, 'inflight': sorted(self._inflight), 'wait_turns': dict(self._wait_turns)}

class LivenessState(str, Enum):
    HEALTHY = 'HEALTHY'
    DEGRADED = 'DEGRADED'
    DEADLOCK_SUSPECTED = 'DEADLOCK_SUSPECTED'
    DEADLOCK_CONFIRMED = 'DEADLOCK_CONFIRMED'
    SAFE_MINIMAL_MODE = 'SAFE_MINIMAL_MODE'
    RECOVERING = 'RECOVERING'

class GovernanceLivenessEngine:

    def __init__(self):
        self.state = LivenessState.HEALTHY
        self.last_findings: tuple[str, ...] = ()

    def evaluate(self, *, dependency_cycles: Sequence[Sequence[str]]=(), split_brain: bool=False, conflicting_owners: bool=False, schema_incompatible: bool=False, auth_dependency_unavailable: bool=False, self_referential_recovery: bool=False) -> LivenessState:
        findings = []
        if dependency_cycles:
            findings.append('cyclic_approval_or_control_dependency')
        if split_brain:
            findings.append('split_brain_control_state')
        if conflicting_owners:
            findings.append('conflicting_ownership_authorities')
        if schema_incompatible:
            findings.append('incompatible_schema_or_control_versions')
        if auth_dependency_unavailable:
            findings.append('authentication_dependency_unavailable')
        if self_referential_recovery:
            findings.append('recovery_requires_failed_subsystem')
        self.last_findings = tuple(findings)
        if not findings:
            self.state = LivenessState.HEALTHY
        elif split_brain or conflicting_owners or self_referential_recovery or dependency_cycles:
            self.state = LivenessState.DEADLOCK_CONFIRMED
        else:
            self.state = LivenessState.DEADLOCK_SUSPECTED
        return self.state

    def enter_safe_minimal(self) -> ControlDecision:
        if self.state not in {LivenessState.DEADLOCK_CONFIRMED, LivenessState.DEADLOCK_SUSPECTED, LivenessState.DEGRADED}:
            raise GovernanceError('safe minimal mode requires a degraded/deadlock condition')
        self.state = LivenessState.SAFE_MINIMAL_MODE
        return ControlDecision('ENTER_SAFE_MINIMAL', ReasonCode.SAFE_MODE_CONTROL_PLANE_INCONSISTENT.value, 'governance', 'control-plane inconsistency requires fail-closed minimal service', 'diagnose, reconcile, then pass return-to-service gate')

class ServiceMode(str, Enum):
    NORMAL = 'NORMAL'
    DEGRADED_OPTIONAL_WORK_SHED = 'DEGRADED_OPTIONAL_WORK_SHED'
    DEGRADED_READ_MOSTLY = 'DEGRADED_READ_MOSTLY'
    DEGRADED_NO_NEW_FANOUT = 'DEGRADED_NO_NEW_FANOUT'
    DEGRADED_NO_EXTERNAL_MUTATION = 'DEGRADED_NO_EXTERNAL_MUTATION'
    SAFE_MINIMAL_MODE = 'SAFE_MINIMAL_MODE'

_MODE_ALLOWED = {ServiceMode.NORMAL: None, ServiceMode.DEGRADED_OPTIONAL_WORK_SHED: {'READ', 'WRITE_INTERNAL', 'VALIDATE', 'RECOVERY', 'ESSENTIAL_FANOUT', 'EXTERNAL_MUTATION'}, ServiceMode.DEGRADED_READ_MOSTLY: {'READ', 'VALIDATE', 'RECOVERY', 'EVIDENCE_PERSIST', 'CHECKPOINT_PERSIST'}, ServiceMode.DEGRADED_NO_NEW_FANOUT: {'READ', 'WRITE_INTERNAL', 'VALIDATE', 'RECOVERY', 'EXTERNAL_MUTATION'}, ServiceMode.DEGRADED_NO_EXTERNAL_MUTATION: {'READ', 'WRITE_INTERNAL', 'VALIDATE', 'RECOVERY', 'FANOUT'}, ServiceMode.SAFE_MINIMAL_MODE: {'READ', 'DIAGNOSTIC', 'EVIDENCE_PERSIST', 'CHECKPOINT_PERSIST', 'RECOVERY', 'AUTHENTICATE_HUMAN'}}

class DegradedModeManager:

    def __init__(self):
        self.mode = ServiceMode.NORMAL
        self.reason = 'normal'

    def set_mode(self, mode: ServiceMode, *, reason: str) -> None:
        self.mode = ServiceMode(mode)
        self.reason = reason

    def authorize_effect(self, effect: str, *, optional: bool=False) -> bool:
        if self.mode == ServiceMode.NORMAL:
            return True
        if self.mode == ServiceMode.DEGRADED_OPTIONAL_WORK_SHED and optional:
            raise GovernanceError(ReasonCode.SHED_OPTIONAL_WORK.value)
        allowed = _MODE_ALLOWED[self.mode]
        if effect not in allowed:
            raise GovernanceError(ReasonCode.DEGRADED_MODE_DENY.value)
        return True

@dataclass(frozen=True)
class HumanIdentityAssertion:
    assertion_id: str
    human_subject: str
    auth_method: str
    issuer: str
    issued_at_utc: str
    expires_at_utc: str
    nonce: str
    signature: str

    def unsigned(self) -> dict:
        d = asdict(self)
        d.pop('signature')
        return d

class HumanRootAuthenticator:
    """Verifies externally issued strong-auth assertions; it cannot mint them."""
    STRONG_METHODS = frozenset({'FIDO2', 'WEBAUTHN', 'HARDWARE_KEY', 'MFA_ROOT_CONSOLE'})

    def __init__(self, verification_key: bytes, *, trusted_issuer: str='HUMAN_ROOT_IDP'):
        self._verification_key = bytes(verification_key)
        self.trusted_issuer = trusted_issuer
        self._used_assertions: set[str] = set()

    def verify(self, assertion: HumanIdentityAssertion, *, now: datetime, consume: bool=True) -> str:
        now = ensure_aware(now)
        if assertion.issuer != self.trusted_issuer or assertion.auth_method not in self.STRONG_METHODS:
            raise BreakGlassError(ReasonCode.BREAK_GLASS_AUTH_INVALID.value)
        if not verify_signature(assertion.unsigned(), assertion.signature, self._verification_key):
            raise BreakGlassError(ReasonCode.BREAK_GLASS_AUTH_INVALID.value)
        if now < parse_iso(assertion.issued_at_utc) or now >= parse_iso(assertion.expires_at_utc):
            raise BreakGlassError(ReasonCode.BREAK_GLASS_EXPIRED.value)
        if assertion.assertion_id in self._used_assertions:
            raise BreakGlassError(ReasonCode.BREAK_GLASS_REPLAY.value)
        if consume:
            self._used_assertions.add(assertion.assertion_id)
        return assertion.human_subject

@dataclass(frozen=True)
class BreakGlassGrant:
    grant_id: str
    human_subject: str
    project_id: str
    target: str
    reason: str
    expected_recovery_action: str
    capability_ceiling: tuple[str, ...]
    issued_at_utc: str
    expires_at_utc: str
    nonce: str
    assertion_id: str
    signature: str

    def unsigned(self) -> dict:
        d = asdict(self)
        d.pop('signature')
        return d

class HashChainAuditLog:
    """Append-only tamper-evident audit log. Optional path enables fsync persistence."""

    def __init__(self, path: str | os.PathLike | None=None):
        self.path = Path(path) if path else None
        self.entries: list[dict] = []
        self._head = '0' * 64
        self._lock = RLock()

    def append(self, event: Mapping) -> dict:
        with self._lock:
            record = {'seq': len(self.entries) + 1, 'prev_hash': self._head, 'event': dict(event)}
            record_hash = digest(record)
            wrapped = {**record, 'record_hash': record_hash}
            self.entries.append(wrapped)
            self._head = record_hash
            if self.path:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open('a', encoding='utf-8') as fh:
                    fh.write(json.dumps(wrapped, sort_keys=True) + '\n')
                    fh.flush()
                    os.fsync(fh.fileno())
            return wrapped

    def verify(self) -> bool:
        prev = '0' * 64
        for i, entry in enumerate(self.entries, 1):
            raw = {'seq': i, 'prev_hash': prev, 'event': entry['event']}
            if entry['prev_hash'] != prev or entry['record_hash'] != digest(raw):
                return False
            prev = entry['record_hash']
        return True

class BreakGlassAuthority:
    """Issues short-lived emergency grants only after an external human assertion verifies."""

    def __init__(self, authenticator: HumanRootAuthenticator, signing_key: bytes, audit_log: HashChainAuditLog):
        self.authenticator = authenticator
        self._signing_key = bytes(signing_key)
        self.audit = audit_log
        self._revoked: set[str] = set()
        self._consumed: set[str] = set()

    def issue(self, assertion: HumanIdentityAssertion, *, now: datetime, project_id: str, target: str, reason: str, expected_recovery_action: str, capability_ceiling: Iterable[str], ttl_seconds: int=300) -> BreakGlassGrant:
        if ttl_seconds <= 0 or ttl_seconds > 900:
            raise BreakGlassError('break-glass TTL must be 1..900 seconds')
        human_subject = self.authenticator.verify(assertion, now=now, consume=True)
        now = ensure_aware(now)
        unsigned = {'grant_id': f'bg-{secrets.token_hex(8)}', 'human_subject': human_subject, 'project_id': project_id, 'target': target, 'reason': reason, 'expected_recovery_action': expected_recovery_action, 'capability_ceiling': tuple(sorted(set(capability_ceiling))), 'issued_at_utc': iso(now), 'expires_at_utc': iso(now + timedelta(seconds=ttl_seconds)), 'nonce': secrets.token_hex(12), 'assertion_id': assertion.assertion_id}
        grant = BreakGlassGrant(**unsigned, signature=sign(unsigned, self._signing_key))
        self.audit.append({'type': 'BREAK_GLASS_ISSUED', 'grant': asdict(grant)})
        return grant

    def verify_and_consume(self, grant: BreakGlassGrant, *, now: datetime, project_id: str, target: str) -> bool:
        now = ensure_aware(now)
        if not verify_signature(grant.unsigned(), grant.signature, self._signing_key):
            raise BreakGlassError(ReasonCode.BREAK_GLASS_AUTH_INVALID.value)
        if grant.grant_id in self._revoked or grant.grant_id in self._consumed:
            raise BreakGlassError(ReasonCode.BREAK_GLASS_REPLAY.value)
        if grant.project_id != project_id or grant.target != target:
            raise BreakGlassError(ReasonCode.BREAK_GLASS_AUTH_INVALID.value)
        if now < parse_iso(grant.issued_at_utc) or now >= parse_iso(grant.expires_at_utc):
            raise BreakGlassError(ReasonCode.BREAK_GLASS_EXPIRED.value)
        self._consumed.add(grant.grant_id)
        self.audit.append({'type': 'BREAK_GLASS_CONSUMED', 'grant_id': grant.grant_id, 'at': iso(now)})
        return True

    def revoke(self, grant_id: str, *, reason: str) -> None:
        self._revoked.add(grant_id)
        self.audit.append({'type': 'BREAK_GLASS_REVOKED', 'grant_id': grant_id, 'reason': reason, 'at': iso(utcnow())})
