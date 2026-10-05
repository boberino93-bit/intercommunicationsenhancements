from .reliability_v18_core import *

class Compatibility(str, Enum):
    BACKWARD_COMPATIBLE = 'BACKWARD_COMPATIBLE'
    FORWARD_COMPATIBLE = 'FORWARD_COMPATIBLE'
    BIDIRECTIONAL = 'BIDIRECTIONAL'
    BREAKING = 'BREAKING'

@dataclass(frozen=True)
class SchemaRecord:
    schema_id: str
    version: int
    status: str
    owner: str
    compatibility: Compatibility
    minimum_reader: int
    minimum_writer: int
    maximum_reader: int | None = None
    required_migration: str | None = None
    rollback_compatible: bool = True
    dependencies: tuple[str, ...] = ()

class SchemaEvolutionRegistry:

    def __init__(self):
        self._records: dict[tuple[str, int], SchemaRecord] = {}
        self._active: dict[str, int] = {}

    def register(self, record: SchemaRecord, *, activate: bool=False) -> None:
        key = (record.schema_id, record.version)
        if key in self._records:
            raise SchemaError('schema version already registered')
        self._records[key] = record
        if activate:
            self._active[record.schema_id] = record.version

    def active(self, schema_id: str) -> SchemaRecord:
        v = self._active.get(schema_id)
        if v is None:
            raise SchemaError('schema has no active version')
        return self._records[schema_id, v]

    def check_writer(self, schema_id: str, writer_version: int, *, reader_versions: Iterable[int]) -> bool:
        active = self.active(schema_id)
        if writer_version < active.minimum_writer:
            raise SchemaError(ReasonCode.BLOCK_SCHEMA_INCOMPATIBLE.value)
        for reader in reader_versions:
            if reader < active.minimum_reader:
                raise SchemaError(ReasonCode.BLOCK_SCHEMA_INCOMPATIBLE.value)
            if active.maximum_reader is not None and reader > active.maximum_reader:
                raise SchemaError(ReasonCode.BLOCK_SCHEMA_INCOMPATIBLE.value)
        if active.compatibility == Compatibility.BREAKING and writer_version != active.version:
            raise SchemaError(ReasonCode.BLOCK_SCHEMA_INCOMPATIBLE.value)
        return True

class MigrationState(str, Enum):
    PLANNED = 'PLANNED'
    CANARY = 'CANARY'
    IN_PROGRESS = 'IN_PROGRESS'
    PAUSED = 'PAUSED'
    ROLLBACK_PENDING = 'ROLLBACK_PENDING'
    ROLLED_BACK = 'ROLLED_BACK'
    VERIFIED = 'VERIFIED'
    COMPLETE = 'COMPLETE'
    FAILED = 'FAILED'

@dataclass(frozen=True)
class MigrationRecord:
    migration_id: str
    schema_id: str
    from_version: int
    to_version: int
    state: MigrationState
    epoch: int
    checkpoint_digest: str
    applied_batches: tuple[str, ...] = ()
    verified_batches: tuple[str, ...] = ()
    rollback_reason: str | None = None

class TransactionalMigrationCoordinator:

    def __init__(self):
        self._records: dict[str, MigrationRecord] = {}

    def plan(self, migration_id: str, schema_id: str, from_version: int, to_version: int, checkpoint) -> MigrationRecord:
        if migration_id in self._records:
            raise MigrationError('migration already exists')
        rec = MigrationRecord(migration_id, schema_id, from_version, to_version, MigrationState.PLANNED, 0, digest(checkpoint))
        self._records[migration_id] = rec
        return rec

    def enter_canary(self, migration_id: str) -> MigrationRecord:
        rec = self._records[migration_id]
        if rec.state != MigrationState.PLANNED:
            raise MigrationError('canary requires PLANNED')
        return self._save(replace(rec, state=MigrationState.CANARY))

    def start(self, migration_id: str) -> MigrationRecord:
        rec = self._records[migration_id]
        if rec.state not in {MigrationState.CANARY, MigrationState.PAUSED}:
            raise MigrationError('migration start/resume requires CANARY or PAUSED')
        return self._save(replace(rec, state=MigrationState.IN_PROGRESS))

    def apply_batch(self, migration_id: str, batch_id: str) -> MigrationRecord:
        rec = self._records[migration_id]
        if rec.state != MigrationState.IN_PROGRESS:
            raise MigrationError('batch apply requires IN_PROGRESS')
        if batch_id in rec.applied_batches:
            return rec
        return self._save(replace(rec, applied_batches=rec.applied_batches + (batch_id,)))

    def verify_batch(self, migration_id: str, batch_id: str) -> MigrationRecord:
        rec = self._records[migration_id]
        if batch_id not in rec.applied_batches:
            raise MigrationError('cannot verify unapplied batch')
        if batch_id in rec.verified_batches:
            return rec
        return self._save(replace(rec, verified_batches=rec.verified_batches + (batch_id,)))

    def pause(self, migration_id: str) -> MigrationRecord:
        rec = self._records[migration_id]
        if rec.state != MigrationState.IN_PROGRESS:
            raise MigrationError('pause requires IN_PROGRESS')
        return self._save(replace(rec, state=MigrationState.PAUSED))

    def verify(self, migration_id: str) -> MigrationRecord:
        rec = self._records[migration_id]
        if rec.state != MigrationState.IN_PROGRESS or set(rec.applied_batches) != set(rec.verified_batches):
            raise MigrationError('all applied batches must verify')
        return self._save(replace(rec, state=MigrationState.VERIFIED))

    def complete(self, migration_id: str) -> MigrationRecord:
        rec = self._records[migration_id]
        if rec.state != MigrationState.VERIFIED:
            raise MigrationError('complete requires VERIFIED')
        return self._save(replace(rec, state=MigrationState.COMPLETE, epoch=rec.epoch + 1))

    def request_rollback(self, migration_id: str, *, reason: str) -> MigrationRecord:
        rec = self._records[migration_id]
        if rec.state in {MigrationState.COMPLETE, MigrationState.ROLLED_BACK}:
            raise MigrationError('cannot rollback terminal migration')
        return self._save(replace(rec, state=MigrationState.ROLLBACK_PENDING, rollback_reason=reason))

    def rollback(self, migration_id: str, *, checkpoint) -> MigrationRecord:
        rec = self._records[migration_id]
        if rec.state != MigrationState.ROLLBACK_PENDING:
            raise MigrationError('rollback requires ROLLBACK_PENDING')
        if digest(checkpoint) != rec.checkpoint_digest:
            raise MigrationError('checkpoint integrity mismatch')
        return self._save(replace(rec, state=MigrationState.ROLLED_BACK))

    def _save(self, rec: MigrationRecord) -> MigrationRecord:
        self._records[rec.migration_id] = rec
        return rec

@dataclass(frozen=True)
class CapabilityEvidence:
    evidence_id: str
    subject: str
    capability: str
    evaluator: str
    dataset_id: str
    sample_count: int
    score: float
    confidence: float
    contaminated: bool
    issued_at_utc: str
    expires_at_utc: str
    provenance_digest: str
    signature: str

    def unsigned(self) -> dict:
        d = asdict(self)
        d.pop('signature')
        return d

class CapabilityEvidenceRegistry:

    def __init__(self, verification_keys: Mapping[str, bytes], *, max_score_jump: float=0.35):
        self.keys = {k: bytes(v) for k, v in verification_keys.items()}
        self.max_score_jump = max_score_jump
        self._history: dict[tuple[str, str], list[CapabilityEvidence]] = defaultdict(list)
        self._revoked: set[str] = set()

    def ingest(self, evidence: CapabilityEvidence, *, now: datetime) -> None:
        key = self.keys.get(evidence.evaluator)
        if key is None or not verify_signature(evidence.unsigned(), evidence.signature, key):
            raise EvidenceError(ReasonCode.CAPABILITY_EVIDENCE_UNTRUSTED.value)
        now = ensure_aware(now)
        if now >= parse_iso(evidence.expires_at_utc):
            raise EvidenceError('expired evidence')
        if evidence.sample_count <= 0 or not 0 <= evidence.score <= 1 or (not 0 <= evidence.confidence <= 1):
            raise EvidenceError('invalid evidence metrics')
        hist = self._history[evidence.subject, evidence.capability]
        if hist:
            prev = hist[-1]
            if abs(evidence.score - prev.score) > self.max_score_jump and evidence.sample_count < max(10, prev.sample_count // 2):
                raise EvidenceError(ReasonCode.CAPABILITY_EVIDENCE_ANOMALOUS.value)
        hist.append(evidence)

    def effective(self, subject: str, capability: str, *, now: datetime) -> CapabilityEvidence | None:
        now = ensure_aware(now)
        valid = [e for e in self._history.get((subject, capability), []) if e.evidence_id not in self._revoked and now < parse_iso(e.expires_at_utc) and (not e.contaminated)]
        return valid[-1] if valid else None

    def revoke(self, evidence_id: str) -> None:
        self._revoked.add(evidence_id)

    def history(self, subject: str, capability: str) -> tuple[CapabilityEvidence, ...]:
        return tuple(self._history.get((subject, capability), ()))

@dataclass(frozen=True)
class EvaluationProvenance:
    evaluation_id: str
    benchmark_id: str
    benchmark_version: str
    candidate_id: str
    evaluator_id: str
    held_out: bool
    hidden_canary: bool
    exposed_to_prompt: bool
    exposed_to_expected_answer: bool
    exposed_to_scoring_rubric: bool
    exposed_to_prior_feedback: bool

    @property
    def contaminated(self) -> bool:
        return any((self.exposed_to_prompt, self.exposed_to_expected_answer, self.exposed_to_scoring_rubric, self.exposed_to_prior_feedback))

    @property
    def independent_weight(self) -> float:
        if self.contaminated:
            return 0.0
        if self.held_out and self.hidden_canary:
            return 1.0
        if self.held_out:
            return 0.8
        return 0.35

class ContaminationLedger:

    def __init__(self):
        self.records: dict[str, EvaluationProvenance] = {}

    def record(self, p: EvaluationProvenance) -> None:
        self.records[p.evaluation_id] = p

    def pristine(self, evaluation_id: str) -> bool:
        return not self.records[evaluation_id].contaminated

RINGS = ('RING_0_LOCAL', 'RING_1_ISOLATED', 'RING_2_PROJECT_CANARY', 'RING_3_SMALL_COHORT', 'RING_4_BROADER_SWARM', 'RING_5_DEFAULT')

@dataclass(frozen=True)
class RingPolicy:
    ring: str
    min_evidence: int
    max_error_rate: float
    max_slo_burn: float
    require_human_review: bool = False

@dataclass(frozen=True)
class RolloutState:
    rollout_id: str
    artifact_digest: str
    source_revision: str
    ring_index: int
    status: str = 'ACTIVE'
    version: int = 1
    last_good_ring_index: int = 0
    quarantine_reason: str | None = None

class RolloutManager:

    def __init__(self, policies: Sequence[RingPolicy]):
        self.policies = {p.ring: p for p in policies}
        if set(self.policies) != set(RINGS):
            raise RolloutError('all rollout rings require policy')
        self._states: dict[str, RolloutState] = {}

    def start(self, rollout_id: str, artifact_digest: str, source_revision: str) -> RolloutState:
        if rollout_id in self._states:
            raise RolloutError('rollout already exists')
        state = RolloutState(rollout_id, artifact_digest, source_revision, 0)
        self._states[rollout_id] = state
        return state

    def promote(self, rollout_id: str, *, target_ring: str, evidence_count: int, error_rate: float, slo_burn: float, human_reviewed: bool=False) -> RolloutState:
        state = self._states[rollout_id]
        if state.status != 'ACTIVE':
            raise RolloutError('rollout is not active')
        target_idx = RINGS.index(target_ring)
        if target_idx != state.ring_index + 1:
            raise RolloutError(ReasonCode.BLOCK_ROLLOUT_RING_SKIP.value)
        policy = self.policies[target_ring]
        if evidence_count < policy.min_evidence or error_rate > policy.max_error_rate or slo_burn > policy.max_slo_burn:
            raise RolloutError(ReasonCode.HOLD_ROLLOUT_REGRESSION.value)
        if policy.require_human_review and (not human_reviewed):
            raise RolloutError('human review required for ring')
        updated = replace(state, ring_index=target_idx, last_good_ring_index=target_idx, version=state.version + 1)
        self._states[rollout_id] = updated
        return updated

    def monitor(self, rollout_id: str, *, expected_version: int, error_rate: float, slo_burn: float, security_violation: bool=False, backup_failure: bool=False) -> ControlDecision:
        state = self._states[rollout_id]
        if state.version != expected_version:
            raise RolloutError('stale rollout control version')
        ring = RINGS[state.ring_index]
        policy = self.policies[ring]
        if security_violation or backup_failure or error_rate > policy.max_error_rate or (slo_burn > policy.max_slo_burn):
            reason = 'security/backup failure' if security_violation or backup_failure else 'regression threshold exceeded'
            self._states[rollout_id] = replace(state, status='QUARANTINED', quarantine_reason=reason, version=state.version + 1)
            return ControlDecision('QUARANTINE', ReasonCode.HOLD_ROLLOUT_REGRESSION.value, 'rollout', reason, 'execute fenced rollback')
        return ControlDecision('CONTINUE', ReasonCode.ADMIT_OK.value, 'rollout', 'ring health within thresholds')

    def automatic_rollback(self, rollout_id: str, *, expected_version: int, expected_artifact_digest: str) -> RolloutState:
        state = self._states[rollout_id]
        if state.version != expected_version or state.artifact_digest != expected_artifact_digest:
            raise RolloutError('rollback fence mismatch')
        if state.status != 'QUARANTINED':
            raise RolloutError('automatic rollback requires quarantined rollout')
        rollback_idx = max(0, state.last_good_ring_index - 1)
        updated = replace(state, ring_index=rollback_idx, status='ROLLED_BACK', version=state.version + 1)
        self._states[rollout_id] = updated
        return updated

    def state(self, rollout_id: str) -> RolloutState:
        return self._states[rollout_id]
