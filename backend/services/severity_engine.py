"""Centralized severity → priority mapping, so priority is calculated consistently everywhere
rather than each analyzer inventing its own scale. Severity itself is judged by each analyzer
from its own evidence (it knows whether a missing security header or a missing alt attribute is
worse); this engine's job is turning that severity into an actionable priority, with two
context adjustments analyzers can opt into rather than every finding defaulting to the same
tier regardless of context."""

from __future__ import annotations

from models.evaluation_models import Priority, Severity

_BASE_PRIORITY: dict[Severity, Priority] = {
    Severity.CRITICAL: Priority.P0,
    Severity.HIGH: Priority.P1,
    Severity.MEDIUM: Priority.P2,
    Severity.LOW: Priority.P3,
    Severity.INFORMATIONAL: Priority.P3,
}

_ESCALATE: dict[Priority, Priority] = {
    Priority.P3: Priority.P2,
    Priority.P2: Priority.P1,
    Priority.P1: Priority.P0,
    Priority.P0: Priority.P0,
}


def derive_priority(severity: Severity, *, high_user_impact: bool = False) -> Priority:
    """`high_user_impact` is for findings whose severity alone would understate how many users
    hit them — e.g. a broken primary CTA versus a broken link in a footer, both "medium"
    severity by consequence, but one blocks every visitor's main path. Escalates by one tier,
    capped at P0. Most analyzers don't set this and just get the severity's base tier — a
    finding is only escalated when an analyzer can point to a concrete reason it's more exposed
    than its severity alone implies, not as a way to inflate priority across the board."""

    base = _BASE_PRIORITY[severity]
    if high_user_impact:
        return _ESCALATE[base]
    return base
