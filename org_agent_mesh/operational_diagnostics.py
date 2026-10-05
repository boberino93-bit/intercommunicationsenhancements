from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

from .reliability_v18_core import digest


class AssuranceLevel(str, Enum):
    PROVEN = "PROVEN"
    PARTIAL = "PARTIAL"
    UNPROVEN = "UNPROVEN"


@dataclass(frozen=True)
class SchedulerAdmissionEvidence:
    pre_invocation_hook_available: bool
    admission_called_before_provider: bool
    provider_rejection_observable: bool
    source_ref: str

    def assessment(self) -> dict:
        preventive = self.pre_invocation_hook_available and self.admission_called_before_provider
        payload = {
            "assurance": AssuranceLevel.PROVEN.value if preventive else AssuranceLevel.PARTIAL.value,
            "mode": "PREVENTIVE" if preventive else "MITIGATION_ONLY",
            "provider_rejection_observable": self.provider_rejection_observable,
            "source_ref": self.source_ref,
            "authority": False,
        }
        return {**payload, "digest": digest(payload)}


@dataclass(frozen=True)
class DistributedBackendEvidence:
    durable: bool
    atomic_cas: bool
    lease_expiry_recovery: bool
    stale_owner_rejection: bool
    fence_validated_at_privileged_sink: bool
    partition_tested: bool
    restore_generation_tested: bool
    multi_node_tested: bool
    source_ref: str

    def assessment(self) -> dict:
        required = (
            self.durable,
            self.atomic_cas,
            self.lease_expiry_recovery,
            self.stale_owner_rejection,
            self.partition_tested,
            self.restore_generation_tested,
            self.multi_node_tested,
        )
        proven = all(required)
        partial = any(required)
        payload = {
            "assurance": AssuranceLevel.PROVEN.value if proven else AssuranceLevel.PARTIAL.value if partial else AssuranceLevel.UNPROVEN.value,
            "fence_validated_at_privileged_sink": self.fence_validated_at_privileged_sink,
            "missing": [
                name for name, ok in {
                    "durable": self.durable,
                    "atomic_cas": self.atomic_cas,
                    "lease_expiry_recovery": self.lease_expiry_recovery,
                    "stale_owner_rejection": self.stale_owner_rejection,
                    "partition_tested": self.partition_tested,
                    "restore_generation_tested": self.restore_generation_tested,
                    "multi_node_tested": self.multi_node_tested,
                }.items() if not ok
            ],
            "source_ref": self.source_ref,
            "authority": False,
        }
        return {**payload, "digest": digest(payload)}


@dataclass(frozen=True)
class RepositoryGovernanceEvidence:
    branch_protected: bool
    required_status_checks: bool
    force_push_disabled: bool
    deletion_disabled: bool
    pr_required: bool
    source_ref: str

    def assessment(self) -> dict:
        controls = (
            self.branch_protected,
            self.required_status_checks,
            self.force_push_disabled,
            self.deletion_disabled,
            self.pr_required,
        )
        payload = {
            "assurance": AssuranceLevel.PROVEN.value if all(controls) else AssuranceLevel.PARTIAL.value if any(controls) else AssuranceLevel.UNPROVEN.value,
            "missing": [
                name for name, ok in {
                    "branch_protected": self.branch_protected,
                    "required_status_checks": self.required_status_checks,
                    "force_push_disabled": self.force_push_disabled,
                    "deletion_disabled": self.deletion_disabled,
                    "pr_required": self.pr_required,
                }.items() if not ok
            ],
            "source_ref": self.source_ref,
            "authority": False,
        }
        return {**payload, "digest": digest(payload)}


class RuntimeReadinessDiagnostic:
    """Combines environment evidence without upgrading it into authority."""

    def evaluate(
        self,
        *,
        scheduler: SchedulerAdmissionEvidence,
        backend: DistributedBackendEvidence,
        repository: RepositoryGovernanceEvidence,
    ) -> dict:
        parts = {
            "scheduler_admission": scheduler.assessment(),
            "distributed_backend": backend.assessment(),
            "repository_governance": repository.assessment(),
        }
        assurances = [part["assurance"] for part in parts.values()]
        overall = (
            AssuranceLevel.PROVEN.value
            if all(x == AssuranceLevel.PROVEN.value for x in assurances)
            else AssuranceLevel.UNPROVEN.value
            if all(x == AssuranceLevel.UNPROVEN.value for x in assurances)
            else AssuranceLevel.PARTIAL.value
        )
        payload = {
            "overall_assurance": overall,
            "components": parts,
            "authority": False,
            "may_authorize_deployment": False,
        }
        return {**payload, "digest": digest(payload)}
