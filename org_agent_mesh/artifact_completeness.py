from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Mapping, Sequence


class ArtifactCompletenessError(ValueError):
    pass


class Readiness(str, Enum):
    DRAFT = "DRAFT"
    TEMPLATE = "TEMPLATE"
    PARTIALLY_POPULATED = "PARTIALLY_POPULATED"
    REQUIRES_HUMAN_INPUT = "REQUIRES_HUMAN_INPUT"
    READY_TO_USE = "READY_TO_USE"
    READY_TO_SUBMIT = "READY_TO_SUBMIT"
    READY_TO_EXECUTE = "READY_TO_EXECUTE"


_PLACEHOLDER_PATTERNS = (
    re.compile(r"\bTODO\b", re.I),
    re.compile(r"\bTBD\b", re.I),
    re.compile(r"\bREPLACE_ME\b", re.I),
    re.compile(r"\[(?:PASTE|INSERT)[^\]]*\]", re.I),
    re.compile(r"\$\{[^}]+\}"),
    re.compile(r"<(?:TOKEN|VALUE|INSERT|PASTE)[^>]*>", re.I),
)


@dataclass(frozen=True)
class ArtifactReadinessCheck:
    rendered_text: str
    mandatory_fields: Mapping[str, str | None]
    identifiers_current: bool
    final_render_validated: bool
    human_input_outstanding: Sequence[str] = ()

    def unresolved_placeholders(self) -> tuple[str, ...]:
        found: list[str] = []
        for pattern in _PLACEHOLDER_PATTERNS:
            found.extend(match.group(0) for match in pattern.finditer(self.rendered_text))
        return tuple(found)

    def validate_ready(self, readiness: Readiness) -> None:
        if readiness not in {Readiness.READY_TO_USE, Readiness.READY_TO_SUBMIT, Readiness.READY_TO_EXECUTE}:
            return
        missing = [name for name, value in self.mandatory_fields.items() if value is None or not str(value).strip()]
        if missing:
            raise ArtifactCompletenessError("MANDATORY_FIELDS_MISSING:" + ",".join(sorted(missing)))
        placeholders = self.unresolved_placeholders()
        if placeholders:
            raise ArtifactCompletenessError("UNRESOLVED_PLACEHOLDERS")
        if self.human_input_outstanding:
            raise ArtifactCompletenessError("HUMAN_INPUT_STILL_REQUIRED")
        if not self.identifiers_current:
            raise ArtifactCompletenessError("STALE_OR_UNVERIFIED_IDENTIFIERS")
        if not self.final_render_validated:
            raise ArtifactCompletenessError("FINAL_RENDER_NOT_VALIDATED")
