"""Result contract for a single annual simulation step."""

from dataclasses import dataclass, field

from engine.core.audit_entry import AuditEntry
from engine.core.country_state import CountryState


@dataclass
class StepResult:
    state: CountryState
    derived: dict[str, float] = field(default_factory=dict)
    reference: dict[str, float] = field(default_factory=dict)
    audit_log: list[AuditEntry] = field(default_factory=list)
