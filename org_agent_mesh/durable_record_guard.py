from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Any


class DurableRecordGuardError(ValueError):
    pass


@dataclass(frozen=True)
class GuardFinding:
    path: str
    finding_type: str
    marker: str


_SAFE_MARKERS = ("redacted", "removed", "placeholder", "external only", "external_only", "not stored", "not_stored")


def _safe_value(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip().lower()
    if not text:
        return True
    return any(text.startswith(marker) for marker in _SAFE_MARKERS)


def _walk(value: Any, path: str = "$"):
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield child_path, str(key), child
            yield from _walk(child, child_path)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, str(index), child
            yield from _walk(child, child_path)


def _label_contains_live_value(text: str, label: str) -> bool:
    lowered = text.lower()
    marker = label.lower()
    start = 0
    while True:
        position = lowered.find(marker, start)
        if position < 0:
            return False
        suffix = text[position + len(label):].lstrip(" \t:=")
        first_line = suffix.splitlines()[0].strip() if suffix else ""
        if first_line and not _safe_value(first_line):
            return True
        start = position + len(label)


def find_prohibited_values(
    record: Mapping[str, Any],
    *,
    prohibited_fields: Iterable[str],
    prohibited_labels: Iterable[str] = (),
) -> tuple[GuardFinding, ...]:
    prohibited = {str(item).strip().lower() for item in prohibited_fields}
    labels = tuple(str(item).strip() for item in prohibited_labels if str(item).strip())
    findings: list[GuardFinding] = []
    for path, key, value in _walk(record):
        normalized = key.strip().lower()
        if normalized in prohibited and not _safe_value(value):
            findings.append(GuardFinding(path, "field", normalized))
        if isinstance(value, str):
            for label in labels:
                if _label_contains_live_value(value, label):
                    findings.append(GuardFinding(path, "label", label))
    return tuple(findings)


def validate_durable_record(
    record: Mapping[str, Any],
    *,
    prohibited_fields: Iterable[str],
    prohibited_labels: Iterable[str] = (),
    context: str = "durable_record",
) -> None:
    findings = find_prohibited_values(
        record,
        prohibited_fields=prohibited_fields,
        prohibited_labels=prohibited_labels,
    )
    if findings:
        markers = ",".join(sorted({f"{item.finding_type}:{item.marker}" for item in findings}))
        raise DurableRecordGuardError(f"PROHIBITED_DURABLE_VALUE:{context}:{markers}")
