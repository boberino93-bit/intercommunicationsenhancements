from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Any


class DurableRecordGuardError(ValueError):
    pass


@dataclass(frozen=True)
class GuardFinding:
    field_name: str


_SAFE_MARKERS = ("redacted", "removed", "placeholder", "external only", "external_only", "not stored", "not_stored")


def _safe_value(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip().lower()
    if not text:
        return True
    return any(text.startswith(marker) for marker in _SAFE_MARKERS)


def find_prohibited_values(record: Mapping[str, Any], *, prohibited_fields: Iterable[str]) -> tuple[GuardFinding, ...]:
    prohibited = {str(item).strip().lower() for item in prohibited_fields}
    findings: list[GuardFinding] = []
    for key, value in record.items():
        normalized = str(key).strip().lower()
        if normalized in prohibited and not _safe_value(value):
            findings.append(GuardFinding(normalized))
    return tuple(findings)


def validate_durable_record(record: Mapping[str, Any], *, prohibited_fields: Iterable[str], context: str = "durable_record") -> None:
    findings = find_prohibited_values(record, prohibited_fields=prohibited_fields)
    if findings:
        names = ",".join(sorted({item.field_name for item in findings}))
        raise DurableRecordGuardError(f"PROHIBITED_DURABLE_VALUE:{context}:{names}")
