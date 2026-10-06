from __future__ import annotations

from dataclasses import dataclass, field

OBSERVED = "OBSERVED"
SUPPORTED = "SUPPORTED"
INFERRED = "INFERRED"
HYPOTHESIS = "HYPOTHESIS"
DISPUTED = "DISPUTED"
BLOCKED = "BLOCKED"
RETRACTED = "RETRACTED"
TAINTED = "TAINTED_REVALIDATION_REQUIRED"
HUMAN_DECISION_REQUIRED = "HUMAN_DECISION_REQUIRED"

ALLOWED = {OBSERVED, SUPPORTED, INFERRED, HYPOTHESIS, DISPUTED, BLOCKED, RETRACTED, TAINTED}
CONTAMINATING = {DISPUTED, BLOCKED, RETRACTED, TAINTED}

class EpistemicError(ValueError):
    pass

@dataclass
class Claim:
    claim_id: str
    state: str
    summary: str
    dependencies: tuple[str, ...] = ()
    consequential: bool = False
    provenance_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.claim_id or not self.summary:
            raise EpistemicError("claim_id and summary are required")
        if self.state not in ALLOWED:
            raise EpistemicError("unsupported evidence state")
        if self.claim_id in self.dependencies:
            raise EpistemicError("claim cannot depend on itself")

@dataclass
class ClaimGraph:
    claims: dict[str, Claim] = field(default_factory=dict)

    def add(self, claim: Claim) -> None:
        if claim.claim_id in self.claims:
            raise EpistemicError("duplicate claim_id")
        missing = [dep for dep in claim.dependencies if dep not in self.claims]
        if missing:
            raise EpistemicError(f"unknown dependencies:{','.join(missing)}")
        self.claims[claim.claim_id] = claim
        self._assert_acyclic()
        self._propagate()

    def set_state(self, claim_id: str, state: str) -> None:
        if state not in ALLOWED:
            raise EpistemicError("unsupported evidence state")
        self.claims[claim_id].state = state
        self._propagate()

    def _assert_acyclic(self) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()
        def visit(node: str) -> None:
            if node in visiting:
                raise EpistemicError("claim dependency cycle")
            if node in visited:
                return
            visiting.add(node)
            for dep in self.claims[node].dependencies:
                visit(dep)
            visiting.remove(node)
            visited.add(node)
        for node in self.claims:
            visit(node)

    def _propagate(self) -> None:
        changed = True
        while changed:
            changed = False
            for claim in self.claims.values():
                if claim.state in {DISPUTED, BLOCKED, RETRACTED}:
                    continue
                if any(self.claims[d].state in CONTAMINATING for d in claim.dependencies):
                    if claim.state != TAINTED:
                        claim.state = TAINTED
                        changed = True

    def disposition(self, claim_id: str) -> str:
        claim = self.claims[claim_id]
        if claim.consequential and claim.state not in {OBSERVED, SUPPORTED}:
            return HUMAN_DECISION_REQUIRED
        return claim.state

    def require_safe_premise(self, claim_id: str) -> bool:
        disposition = self.disposition(claim_id)
        if disposition == HUMAN_DECISION_REQUIRED or disposition in CONTAMINATING:
            raise EpistemicError(f"UNRESOLVED_CONSEQUENTIAL_CLAIM:{claim_id}:{disposition}")
        return True
