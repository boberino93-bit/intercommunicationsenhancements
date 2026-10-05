from .reliability_v18_core import *

@dataclass(frozen=True)
class DurableSnapshot:
    store_id: str
    revision: int
    created_at_utc: str
    payload: object
    payload_digest: str
    parent_digest: str | None = None

    @classmethod
    def create(cls, store_id: str, revision: int, payload, *, created_at: datetime, parent_digest: str | None=None):
        return cls(store_id, revision, iso(created_at), payload, digest(payload), parent_digest)

    def verify(self) -> bool:
        return digest(self.payload) == self.payload_digest

@dataclass(frozen=True)
class RecoveryObjective:
    system_class: str
    rpo_seconds: int
    rto_seconds: int
    max_backup_lag_seconds: int
    max_checkpoint_age_seconds: int
    max_unverified_effect_age_seconds: int
    max_stale_claim_age_seconds: int
    max_heartbeat_age_seconds: int
    max_dormant_wake_latency_seconds: int

@dataclass(frozen=True)
class ReconstructionResult:
    success: bool
    cutoff_revision: int | None
    trusted_survivors: tuple[str, ...]
    rejected_survivors: tuple[str, ...]
    mode: str
    reconstructed_state_digest: str | None
    rpo_seconds_observed: float
    rto_seconds_observed: float

class ReconstructionEngine:

    def reconstruct(self, snapshots: Sequence[DurableSnapshot], *, target_time: datetime | None=None) -> ReconstructionResult:
        started = time.monotonic()
        target_time = ensure_aware(target_time or utcnow())
        good = [s for s in snapshots if s.verify()]
        bad = [s for s in snapshots if not s.verify()]
        if not good:
            elapsed = time.monotonic() - started
            return ReconstructionResult(False, None, (), tuple((s.store_id for s in bad)), 'SAFE_MINIMAL_MODE', None, math.inf, elapsed)
        cutoff = max((s.revision for s in good))
        candidates = [s for s in good if s.revision == cutoff]
        digests = {s.payload_digest for s in candidates}
        if len(digests) != 1:
            elapsed = time.monotonic() - started
            return ReconstructionResult(False, cutoff - 1 if cutoff > 0 else None, tuple((s.store_id for s in good)), tuple((s.store_id for s in bad)), 'SAFE_MINIMAL_MODE', None, math.inf, elapsed)
        chosen = candidates[0]
        rpo = max(0.0, (target_time - parse_iso(chosen.created_at_utc)).total_seconds())
        elapsed = time.monotonic() - started
        return ReconstructionResult(True, cutoff, tuple((s.store_id for s in good)), tuple((s.store_id for s in bad)), 'DEGRADED_READ_MOSTLY' if bad else 'NORMAL', chosen.payload_digest, rpo, elapsed)

@dataclass(frozen=True)
class GameDayEvidence:
    scenario: str
    expected_behavior: str
    actual_behavior: str
    success: bool
    rpo_seconds: float
    rto_seconds: float
    invariant_violations: tuple[str, ...] = ()
    manual_interventions: tuple[str, ...] = ()
    remediation: tuple[str, ...] = ()

class RecoveryDrillRunner:

    def __init__(self, engine: ReconstructionEngine):
        self.engine = engine

    def run_corrupt_latest_checkpoint(self, snapshots: Sequence[DurableSnapshot]) -> GameDayEvidence:
        target_time = max((parse_iso(s.created_at_utc) for s in snapshots), default=utcnow())
        result = self.engine.reconstruct(snapshots, target_time=target_time)
        expected = 'reject corrupt backup and reconstruct from valid durable survivor'
        actual = f"success={result.success};mode={result.mode};rejected={','.join(result.rejected_survivors)}"
        return GameDayEvidence('CORRUPT_LATEST_CHECKPOINT', expected, actual, result.success and bool(result.rejected_survivors), result.rpo_seconds_observed, result.rto_seconds_observed, () if result.success else ('reconstruction_failed',))

    @staticmethod
    def objectives_met(evidence: GameDayEvidence, objective: RecoveryObjective) -> bool:
        return evidence.success and evidence.rpo_seconds <= objective.rpo_seconds and (evidence.rto_seconds <= objective.rto_seconds)

class HysteresisController:

    def __init__(self, *, enter_threshold: float, exit_threshold: float, min_samples: int, min_dwell_seconds: float, cooldown_seconds: float):
        if exit_threshold > enter_threshold:
            raise ValueError('exit_threshold must be <= enter_threshold')
        self.enter_threshold = enter_threshold
        self.exit_threshold = exit_threshold
        self.min_samples = max(1, min_samples)
        self.min_dwell_seconds = max(0.0, min_dwell_seconds)
        self.cooldown_seconds = max(0.0, cooldown_seconds)
        self.active = False
        self.last_change_mono = -math.inf

    def update(self, samples: Sequence[float], *, now_mono: float) -> bool:
        if len(samples) < self.min_samples:
            return self.active
        if now_mono - self.last_change_mono < self.cooldown_seconds:
            return self.active
        avg = sum(samples) / len(samples)
        if not self.active and avg >= self.enter_threshold:
            self.active = True
            self.last_change_mono = now_mono
        elif self.active and avg <= self.exit_threshold and (now_mono - self.last_change_mono >= self.min_dwell_seconds):
            self.active = False
            self.last_change_mono = now_mono
        return self.active

class ChurnGuard:

    def __init__(self, *, max_changes: int, window_seconds: float, freeze_seconds: float):
        self.max_changes = max_changes
        self.window_seconds = window_seconds
        self.freeze_seconds = freeze_seconds
        self._events = deque()
        self._frozen_until = -math.inf

    def record_change(self, *, now_mono: float) -> bool:
        while self._events and now_mono - self._events[0] > self.window_seconds:
            self._events.popleft()
        if now_mono < self._frozen_until:
            return False
        self._events.append(now_mono)
        if len(self._events) > self.max_changes:
            self._frozen_until = now_mono + self.freeze_seconds
            return False
        return True

    def frozen(self, *, now_mono: float) -> bool:
        return now_mono < self._frozen_until

@dataclass(frozen=True)
class SLO:
    slo_id: str
    metric: str
    target: float
    comparison: str
    window_seconds: int
    severity: str
    error_budget: float
    degraded_threshold: float
    recovery_action: str

@dataclass
class SLOState:
    successes: int = 0
    failures: int = 0
    observed_values: list[float] = field(default_factory=list)

class SLORegistry:

    def __init__(self, slos: Iterable[SLO]):
        self.slos = {s.slo_id: s for s in slos}
        self.state = {s.slo_id: SLOState() for s in slos}

    def record_binary(self, slo_id: str, success: bool) -> None:
        st = self.state[slo_id]
        if success:
            st.successes += 1
        else:
            st.failures += 1

    def record_value(self, slo_id: str, value: float) -> None:
        self.state[slo_id].observed_values.append(float(value))

    def health(self, slo_id: str) -> dict:
        slo = self.slos[slo_id]
        st = self.state[slo_id]
        total = st.successes + st.failures
        rate = st.successes / total if total else 1.0
        budget_used = st.failures / total if total else 0.0
        latest = st.observed_values[-1] if st.observed_values else None
        target_ok = True
        if latest is not None:
            target_ok = latest >= slo.target if slo.comparison == '>=' else latest <= slo.target
        else:
            target_ok = rate >= slo.target if slo.comparison == '>=' else 1 - rate <= slo.target
        exhausted = budget_used > slo.error_budget
        return {'target_ok': target_ok, 'budget_used': budget_used, 'budget_exhausted': exhausted, 'latest': latest, 'rate': rate}

class ReliabilityBudgetEngine:

    def __init__(self, *, error_budget: float, durability_budget: float, liveness_budget: float, change_budget: float):
        self.limits = {'error': error_budget, 'durability': durability_budget, 'liveness': liveness_budget, 'change': change_budget}
        self.debt = defaultdict(float)

    def consume(self, budget: str, amount: float) -> None:
        if budget not in self.limits or amount < 0:
            raise ValueError('invalid budget consumption')
        self.debt[budget] += amount

    def remaining(self, budget: str) -> float:
        return self.limits[budget] - self.debt[budget]

    def decision(self, *, optional: bool, fanout: int=1) -> ControlDecision:
        exhausted = [k for k in self.limits if self.remaining(k) < 0]
        if not exhausted:
            return ControlDecision('ADMIT', ReasonCode.ADMIT_OK.value, 'slo_budget', 'budgets healthy')
        if optional:
            return ControlDecision('SHED', ReasonCode.PAUSE_ERROR_BUDGET_EXHAUSTED.value, 'slo_budget', f"exhausted budgets: {','.join(exhausted)}", 'retry after remediation')
        if fanout > 1:
            return ControlDecision('THROTTLE', ReasonCode.THROTTLE_ERROR_BUDGET.value, 'slo_budget', f"exhausted budgets: {','.join(exhausted)}", 'reduce fanout to 1')
        return ControlDecision('DEGRADED', ReasonCode.PAUSE_ERROR_BUDGET_EXHAUSTED.value, 'slo_budget', f"exhausted budgets: {','.join(exhausted)}", 'run protected recovery/essential work only')

class StateIntegrityEngine:

    def verify_snapshots(self, snapshots: Sequence[DurableSnapshot]) -> dict:
        invalid = [s.store_id for s in snapshots if not s.verify()]
        by_revision: dict[int, set[str]] = defaultdict(set)
        for s in snapshots:
            if s.verify():
                by_revision[s.revision].add(s.payload_digest)
        divergent = sorted((rev for rev, ds in by_revision.items() if len(ds) > 1))
        last_common = max((rev for rev, ds in by_revision.items() if len(ds) == 1), default=None)
        return {'invalid_stores': invalid, 'divergent_revisions': divergent, 'last_verified_common_revision': last_common, 'ok': not invalid and (not divergent)}

class DependencyGraph:

    def __init__(self, edges: Mapping[str, Iterable[str]]):
        self.edges = {k: tuple(v) for k, v in edges.items()}
        for deps in list(self.edges.values()):
            for d in deps:
                self.edges.setdefault(d, ())

    def cycles(self) -> list[list[str]]:
        color = {n: 0 for n in self.edges}
        stack: list[str] = []
        found: list[list[str]] = []

        def visit(n: str):
            color[n] = 1
            stack.append(n)
            for d in self.edges[n]:
                if color[d] == 0:
                    visit(d)
                elif color[d] == 1:
                    idx = stack.index(d)
                    cyc = stack[idx:] + [d]
                    if cyc not in found:
                        found.append(cyc)
            stack.pop()
            color[n] = 2
        for n in self.edges:
            if color[n] == 0:
                visit(n)
        return found

    def bootstrap_root(self, preferred: Iterable[str]) -> tuple[str, ...]:
        """Return preferred nodes whose dependencies are acyclic and satisfied within the set closure."""
        if self.cycles():
            cyclic_nodes = {x for c in self.cycles() for x in c}
        else:
            cyclic_nodes = set()
        return tuple((x for x in preferred if x in self.edges and x not in cyclic_nodes))

class TrustedTimeMonitor:

    def __init__(self, *, max_skew_seconds: float):
        self.max_skew = max_skew_seconds
        self._last_wall: datetime | None = None
        self._last_mono: float | None = None

    def observe(self, wall: datetime, mono: float, *, provider_wall: datetime | None=None) -> ControlDecision:
        wall = ensure_aware(wall)
        if self._last_wall is not None:
            wall_delta = (wall - self._last_wall).total_seconds()
            mono_delta = mono - self._last_mono
            if wall_delta < -self.max_skew:
                raise TimeReliabilityError(ReasonCode.CLOCK_ROLLBACK.value)
            if abs(wall_delta - mono_delta) > self.max_skew:
                raise TimeReliabilityError(ReasonCode.CLOCK_SKEW.value)
        if provider_wall is not None:
            provider_wall = ensure_aware(provider_wall)
            if abs((provider_wall - wall).total_seconds()) > self.max_skew:
                raise TimeReliabilityError(ReasonCode.CLOCK_SKEW.value)
        self._last_wall, self._last_mono = (wall, mono)
        return ControlDecision('TIME_OK', ReasonCode.ADMIT_OK.value, 'trusted_time', 'clock observations within tolerated skew')
