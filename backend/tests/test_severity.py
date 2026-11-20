from __future__ import annotations

from models.evaluation_models import Priority, Severity
from services.severity_engine import derive_priority


def test_base_priority_mapping():
    assert derive_priority(Severity.CRITICAL) == Priority.P0
    assert derive_priority(Severity.HIGH) == Priority.P1
    assert derive_priority(Severity.MEDIUM) == Priority.P2
    assert derive_priority(Severity.LOW) == Priority.P3
    assert derive_priority(Severity.INFORMATIONAL) == Priority.P3


def test_not_everything_is_high_priority():
    # A spec requirement in its own right: low/medium severity findings must not all collapse
    # into the same top priority tier.
    priorities = {derive_priority(s) for s in Severity}
    assert len(priorities) > 1


def test_high_user_impact_escalates_by_one_tier_capped_at_p0():
    assert derive_priority(Severity.LOW, high_user_impact=True) == Priority.P2
    assert derive_priority(Severity.MEDIUM, high_user_impact=True) == Priority.P1
    assert derive_priority(Severity.HIGH, high_user_impact=True) == Priority.P0
    assert derive_priority(Severity.CRITICAL, high_user_impact=True) == Priority.P0
