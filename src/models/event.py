"""
models/event.py

Event data structure.
Events represent external signals (news, macro data, sentiment shifts)
that the signal engine can use alongside market prices.
No business logic — pure data container.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Event:
    """
    An external event that may be relevant to one or more markets.

    Attributes:
        type:             Category of the event, e.g. "macro", "news", "sentiment".
        strength:         Implied probability that the event resolves YES, in [0.0, 1.0].
                          Acts as the event's view of the market: 0.8 means the event
                          strongly suggests YES is likely.
        related_keywords: Words used to match this event to market questions.
        created_at:       When the event was collected.
    """

    type: str
    strength: float
    related_keywords: list[str]
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))