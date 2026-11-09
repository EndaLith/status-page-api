INITIAL_STATUS = "investigating"

ALLOWED_TRANSITIONS = {
    "investigating": {"identified", "monitoring", "resolved"},
    "identified": {"investigating", "monitoring", "resolved"},
    "monitoring": {"investigating", "resolved"},
    "resolved": {"investigating"},
}


def can_transition(current: str, new: str) -> bool:
    return new in ALLOWED_TRANSITIONS[current]
