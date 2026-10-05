from .reliability_v18_core import *
from .reliability_v18_governance import DegradedModeManager
from .reliability_v18_evolution import RINGS
from .reliability_v18_recovery import ReliabilityBudgetEngine, DurableSnapshot, RecoveryObjective, RecoveryDrillRunner, ReconstructionEngine

@dataclass(frozen=True)
class SupplyChainAttestation:
    artifact_id: str
    source_repository: str
    source_revision: str
    builder_id: str
    toolchain_id: str
    dependency_inventory_digest: str
    build_environment_digest: str
    artifact_digest: str
    vulnerability_status: str
    trust_decision: str
    promotion_ring: str
    signature: str

    def unsigned(self):
        d = asdict(self)
        d.pop('signature')
        return d

class SupplyChainVerifier:

    def __init__(self, trusted_builder_keys: Mapping[str, bytes]):
        self.keys = {k: bytes(v) for k, v in trusted_builder_keys.items()}

    def verify(self, att: SupplyChainAttestation, *, actual_artifact_digest: str, required_ring: str | None=None) -> bool:
        key = self.keys.get(att.builder_id)
        if key is None or not verify_signature(att.unsigned(), att.signature, key):
            raise IntegrityError(ReasonCode.SUPPLY_CHAIN_MISMATCH.value)
        if att.artifact_digest != actual_artifact_digest:
            raise IntegrityError(ReasonCode.SUPPLY_CHAIN_MISMATCH.value)
        if required_ring is not None and RINGS.index(att.promotion_ring) < RINGS.index(required_ring):
            raise IntegrityError('artifact not eligible for required ring')
        if att.vulnerability_status not in {'CLEAR', 'ACCEPTED_RISK'} or att.trust_decision != 'TRUSTED':
            raise IntegrityError('supply-chain trust not established')
        return True

@dataclass
class CredentialLease:
    credential_id: str
    project_id: str
    environment: str
    capabilities: tuple[str, ...]
    issued_at_utc: str
    expires_at_utc: str
    provenance: str
    _secret: bytearray = field(repr=False)
    revoked: bool = False

    def use(self, *, now: datetime, project_id: str, environment: str, capability: str) -> bytes:
        now = ensure_aware(now)
        if self.revoked:
            raise CredentialError(ReasonCode.CREDENTIAL_REVOKED.value)
        if now >= parse_iso(self.expires_at_utc):
            raise CredentialError(ReasonCode.CREDENTIAL_EXPIRED.value)
        if self.project_id != project_id or self.environment != environment or capability not in self.capabilities:
            raise CredentialError(ReasonCode.CREDENTIAL_SCOPE_MISMATCH.value)
        return bytes(self._secret)

    def zeroize(self) -> None:
        for i in range(len(self._secret)):
            self._secret[i] = 0
        self.revoked = True

class CredentialBroker:

    def __init__(self):
        self._leases: dict[str, CredentialLease] = {}

    def issue(self, *, project_id: str, environment: str, capabilities: Iterable[str], secret_value: bytes, ttl_seconds: int, provenance: str, now: datetime) -> CredentialLease:
        if ttl_seconds <= 0:
            raise CredentialError('TTL must be positive')
        now = ensure_aware(now)
        lease = CredentialLease(credential_id=f'cred-{secrets.token_hex(8)}', project_id=project_id, environment=environment, capabilities=tuple(sorted(set(capabilities))), issued_at_utc=iso(now), expires_at_utc=iso(now + timedelta(seconds=ttl_seconds)), provenance=provenance, _secret=bytearray(secret_value))
        self._leases[lease.credential_id] = lease
        return lease

    def revoke(self, credential_id: str) -> None:
        self._leases[credential_id].zeroize()

    def teardown_project(self, project_id: str) -> None:
        for lease in self._leases.values():
            if lease.project_id == project_id:
                lease.zeroize()

@dataclass(frozen=True)
class AssuranceCase:
    case_id: str
    objective: str
    project_id: str
    exact_artifact_digest: str
    policy_certificate_id: str
    ownership_ref: str
    test_evidence: tuple[str, ...]
    independent_validation: tuple[str, ...]
    known_risks: tuple[str, ...]
    unresolved_limitations: tuple[str, ...]
    slo_health: Mapping[str, object]
    rollback_plan: str
    blast_radius_ring: str
    supply_chain_attestation_id: str
    backup_state_ref: str
    monitoring_plan: str
    acceptance_criteria: tuple[str, ...]
    human_authorization_id: str | None = None

class AssuranceCaseBuilder:
    REQUIRED = ('objective', 'project_id', 'exact_artifact_digest', 'policy_certificate_id', 'ownership_ref', 'test_evidence', 'independent_validation', 'rollback_plan', 'blast_radius_ring', 'supply_chain_attestation_id', 'backup_state_ref', 'monitoring_plan', 'acceptance_criteria')

    def build(self, **kwargs) -> AssuranceCase:
        missing = [k for k in self.REQUIRED if not kwargs.get(k)]
        if missing:
            raise AssuranceError(f"{ReasonCode.ASSURANCE_CASE_INCOMPLETE.value}:{','.join(missing)}")
        kwargs.setdefault('known_risks', ())
        kwargs.setdefault('unresolved_limitations', ())
        kwargs.setdefault('slo_health', {})
        kwargs.setdefault('human_authorization_id', None)
        kwargs.setdefault('case_id', f'ac-{digest(kwargs)[:20]}')
        return AssuranceCase(**kwargs)

class ProtectedTransitionPreflight:
    """Composes independent controls without becoming a second authority source."""

    def __init__(self, *, degraded_modes: DegradedModeManager, budget_engine: ReliabilityBudgetEngine, supply_chain_verifier: SupplyChainVerifier | None=None):
        self.degraded_modes = degraded_modes
        self.budget_engine = budget_engine
        self.supply_chain_verifier = supply_chain_verifier

    def check(self, *, effect: str, optional: bool, fanout: int, attestation: SupplyChainAttestation | None=None, actual_artifact_digest: str | None=None, required_ring: str | None=None) -> ControlDecision:
        self.degraded_modes.authorize_effect(effect, optional=optional)
        budget_decision = self.budget_engine.decision(optional=optional, fanout=fanout)
        if budget_decision.decision != 'ADMIT':
            return budget_decision
        if attestation is not None:
            if self.supply_chain_verifier is None or actual_artifact_digest is None:
                raise IntegrityError('supply-chain verifier/digest required')
            self.supply_chain_verifier.verify(attestation, actual_artifact_digest=actual_artifact_digest, required_ring=required_ring)
        return ControlDecision('ADMIT', ReasonCode.ADMIT_OK.value, 'preflight', 'protected-transition preflight passed')

def run_reference_game_day(now: datetime | None=None) -> dict:
    now = ensure_aware(now or utcnow())
    valid = DurableSnapshot.create('github', 7, {'state': 'ok', 'owner': 'primary'}, created_at=now - timedelta(seconds=3))
    bad = DurableSnapshot('artifactory', 8, iso(now - timedelta(seconds=1)), {'state': 'tampered'}, '0' * 64, valid.payload_digest)
    objective = RecoveryObjective('reference-control-plane', 30, 5, 30, 30, 30, 30, 30, 30)
    evidence = RecoveryDrillRunner(ReconstructionEngine()).run_corrupt_latest_checkpoint([valid, bad])
    return {'scenario': asdict(evidence), 'objective': asdict(objective), 'objectives_met': RecoveryDrillRunner.objectives_met(evidence, objective), 'generated_at_utc': iso(now), 'evidence_digest': digest({'scenario': asdict(evidence), 'objective': asdict(objective)})}
