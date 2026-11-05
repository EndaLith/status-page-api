from app.incident_rules import can_transition


def test_reopen_resolved_incident():
    assert can_transition("resolved", "investigating") is False


def test_resolved_cannot_go_to_monitoring():
    assert can_transition("resolved", "monitoring") is False


def test_false_alarm_can_resolve_directly():
    assert can_transition("investigating", "resolved") is True
