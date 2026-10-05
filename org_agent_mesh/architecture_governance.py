from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping, Sequence


class ArchitectureGovernanceError(RuntimeError):
    pass


class MechanismClass(str, Enum):
    INVARIANT = "INVARIANT"
    POLICY = "POLICY"
    PROTOCOL = "PROTOCOL"
    CONTRACT = "CONTRACT"
    IMPLEMENTATION = "IMPLEMENTATION"


FAILURE_TAXONOMY = frozenset({
    "INPUT_INVALID", "CONTRACT_VIOLATION", "DEPENDENCY_UNAVAILABLE", "POLICY_CONFLICT",
    "INVARIANT_VIOLATION", "TIMEOUT", "STATE_CONFLICT", "VALIDATION_FAILURE",
    "PERMISSION_DENIED", "AUTHENTICATION_REQUIRED", "AUTHORITY_NOT_ESTABLISHED",
    "STALE_OWNER", "STALE_POLICY", "UNKNOWN_EFFECT", "QUARANTINED", "UNKNOWN_FAILURE",
})

RECOVERY_DISPOSITIONS = frozenset({
    "RETRY", "FALLBACK", "ROLLBACK", "REPAIR", "DEGRADE", "ESCALATE", "VERIFY_OR_RECOVERY", "HALT",
})

DEPRECATION_STATES = frozenset({"EXPERIMENTAL", "ACTIVE", "DEPRECATED", "READ_ONLY_OR_COMPATIBILITY", "REMOVED"})


@dataclass(frozen=True)
class RegistryEntry:
    entry_id: str
    mechanism_class: MechanismClass
    authority_source: str
    authoritative: bool
    derived: bool
    version: str
    lifecycle: str = "ACTIVE"
    creates_authority: bool = False

    def validate(self) -> None:
        if not self.entry_id or not self.authority_source or not self.version:
            raise ArchitectureGovernanceError("INPUT_INVALID")
        if self.creates_authority:
            raise ArchitectureGovernanceError("AUTHORITY_NOT_ESTABLISHED")
        if self.authoritative and self.derived:
            raise ArchitectureGovernanceError("CONTRACT_VIOLATION:derived_cannot_be_authoritative")
        if self.lifecycle not in DEPRECATION_STATES:
            raise ArchitectureGovernanceError("CONTRACT_VIOLATION:lifecycle")


@dataclass(frozen=True)
class BoundaryContract:
    contract_id: str
    producer: str
    consumer: str
    version: str
    required_inputs: tuple[str, ...]
    required_outputs: tuple[str, ...]
    failure_representation: tuple[str, ...]
    forbidden_behavior: tuple[str, ...]
    idempotency: str
    authority_expectations: tuple[str, ...]

    def validate(self) -> None:
        if not all((self.contract_id, self.producer, self.consumer, self.version, self.idempotency)):
            raise ArchitectureGovernanceError("INPUT_INVALID")
        unknown_failures = set(self.failure_representation) - FAILURE_TAXONOMY
        if unknown_failures:
            raise ArchitectureGovernanceError(f"CONTRACT_VIOLATION:unknown_failure:{sorted(unknown_failures)}")


class DependencyGraph:
    def __init__(self, edges: Mapping[str, Iterable[str]]):
        self.edges = {node: frozenset(deps) for node, deps in edges.items()}
        for deps in tuple(self.edges.values()):
            for dep in deps:
                self.edges.setdefault(dep, frozenset())

    def dependents_of(self, node: str, *, transitive: bool = True) -> tuple[str, ...]:
        direct = {candidate for candidate, deps in self.edges.items() if node in deps}
        if not transitive:
            return tuple(sorted(direct))
        found = set(direct)
        frontier = list(direct)
        while frontier:
            current = frontier.pop()
            for candidate, deps in self.edges.items():
                if current in deps and candidate not in found:
                    found.add(candidate)
                    frontier.append(candidate)
        return tuple(sorted(found))

    def dependency_cycles(self) -> tuple[tuple[str, ...], ...]:
        cycles: set[tuple[str, ...]] = set()
        visiting: list[str] = []
        visited: set[str] = set()

        def walk(node: str) -> None:
            if node in visiting:
                idx = visiting.index(node)
                cycle = tuple(visiting[idx:] + [node])
                cycles.add(cycle)
                return
            if node in visited:
                return
            visiting.append(node)
            for dep in self.edges.get(node, ()): walk(dep)
            visiting.pop()
            visited.add(node)

        for node in sorted(self.edges):
            walk(node)
        return tuple(sorted(cycles))


@dataclass(frozen=True)
class ComplexityDelta:
    components_added: int = 0
    components_removed: int = 0
    dependencies_added: int = 0
    dependencies_removed: int = 0
    policies_added: int = 0
    policies_removed: int = 0
    persistent_state_added: int = 0
    persistent_state_removed: int = 0
    authority_objects_added: int = 0
    sync_paths_added: int = 0
    failure_modes_added: int = 0
    duplicated_logic_eliminated: int = 0
    measurable_gain: int = 0

    @property
    def complexity_cost(self) -> int:
        return (
            3 * self.components_added + 2 * self.dependencies_added + 2 * self.policies_added
            + 3 * self.persistent_state_added + 5 * self.authority_objects_added
            + 2 * self.sync_paths_added + 2 * self.failure_modes_added
            - 2 * self.components_removed - self.dependencies_removed - self.policies_removed
            - 2 * self.persistent_state_removed - 2 * self.duplicated_logic_eliminated
        )

    def earns_cost(self) -> bool:
        return self.measurable_gain > max(0, self.complexity_cost)


def resolve_equal_authority_rules(*, rule_ids: Sequence[str], same_authority: bool, canonical_specificity_resolves: bool) -> str:
    if len(rule_ids) < 2:
        raise ArchitectureGovernanceError("INPUT_INVALID")
    if not same_authority:
        return "USE_AUTHORITY_HIERARCHY"
    if canonical_specificity_resolves:
        return "USE_CANONICAL_SPECIFICITY_RULE"
    raise ArchitectureGovernanceError(f"POLICY_CONFLICT:{','.join(sorted(rule_ids))}")


def validate_recovery_disposition(failure: str, disposition: str) -> None:
    if failure not in FAILURE_TAXONOMY:
        raise ArchitectureGovernanceError("UNKNOWN_FAILURE")
    if disposition not in RECOVERY_DISPOSITIONS:
        raise ArchitectureGovernanceError("CONTRACT_VIOLATION:recovery_disposition")
    if failure == "UNKNOWN_EFFECT" and disposition == "RETRY":
        raise ArchitectureGovernanceError("CONTRACT_VIOLATION:blind_retry_unknown_effect")
