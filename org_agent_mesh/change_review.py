from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class ChangeReviewError(ValueError):
    pass


@dataclass(frozen=True)
class ReviewReceipt:
    receipt_id: str
    path_id: str
    subject_id: str
    case_id: str
    scope: str
    accepted: bool


@dataclass(frozen=True)
class ChangeReview:
    source_project: str
    acting_role: str
    target_class: str
    warning_acknowledged: bool
    first: ReviewReceipt
    second: ReviewReceipt
    backup_ref: str
    expected_pre_state: str
    propagation_record: str

    def validate(self, policy: Mapping[str, Any], *, subject_id: str, case_id: str, base_checks_ok: bool) -> None:
        if not base_checks_ok:
            raise ChangeReviewError("BASE_CHECKS_REQUIRED")
        if self.source_project != policy.get("source_project"):
            raise ChangeReviewError("SOURCE_PROJECT_MISMATCH")
        if self.acting_role.upper() != str(policy.get("required_role", "PRIMARY")).upper():
            raise ChangeReviewError("ROLE_REQUIRED")
        if self.target_class not in set(policy.get("protected_targets", [])):
            raise ChangeReviewError("TARGET_CLASS_INVALID")
        if policy.get("warning_acknowledgement_required") and not self.warning_acknowledged:
            raise ChangeReviewError("WARNING_ACK_REQUIRED")
        for receipt in (self.first, self.second):
            if not receipt.accepted:
                raise ChangeReviewError("RECEIPT_NOT_ACCEPTED")
            if receipt.subject_id != subject_id or receipt.case_id != case_id:
                raise ChangeReviewError("RECEIPT_BINDING_MISMATCH")
            if not receipt.receipt_id or not receipt.path_id or not receipt.scope:
                raise ChangeReviewError("RECEIPT_INCOMPLETE")
        if self.first.receipt_id == self.second.receipt_id:
            raise ChangeReviewError("DISTINCT_RECEIPTS_REQUIRED")
        if self.first.path_id == self.second.path_id:
            raise ChangeReviewError("DISTINCT_PATHS_REQUIRED")
        if not self.backup_ref or not self.expected_pre_state:
            raise ChangeReviewError("PRE_CHANGE_STATE_REQUIRED")
        if not self.propagation_record:
            raise ChangeReviewError("PROPAGATION_RECORD_REQUIRED")
