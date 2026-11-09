INITIAL_STATUS = "investigating"

ALLOWED_TRANSITIONS = {
    "investigating": {"identified", "monitoring", "resolved"},
    "identified": {"investigation", "monitoring", "resolved"},
    "monitoring": {"investigation", "resolved"},
    "resolved": {"investigation"},
}


def can_transition(current: str, new: str) -> bool:
    return new in ALLOWED_TRANSITIONS[current]
