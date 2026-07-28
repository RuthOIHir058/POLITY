"""Structured explainability record for one simulated or derived variable."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AuditEntry:
    year: int
    variable: str
    value: float
    delta: float
    causes: list[tuple[str, float]] = field(default_factory=list)
    severity: str = "none"
    note: str = ""
