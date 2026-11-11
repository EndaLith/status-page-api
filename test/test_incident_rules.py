import pytest

from app.incident_rules import can_transition


@pytest.mark.parametrize(
    "current, new, expected",
    [
        ("investigating", "identified", True),
        ("investigating", "monitoring", True),
        ("investigating", "resolved", True),
        ("identified", "investigating", True),
        ("identified", "monitoring", True),
        ("identified", "resolved", True),
        ("monitoring", "investigating", True),
        ("monitoring", "identified", False),
        ("monitoring", "resolved", True),
        ("resolved", "investigating", True),
        ("resolved", "identified", False),
        ("resolved", "monitoring", False),
    ],
)
def test_transition_table(current, new, expected):
    assert can_transition(current, new) is expected


def test_reopen_resolved_incident():
    assert can_transition("resolved", "investigating") is True


def test_resolved_cannot_go_to_monitoring():
    assert can_transition("resolved", "monitoring") is False


def test_false_alarm_can_resolve_directly():
    assert can_transition("investigating", "resolved") is True
