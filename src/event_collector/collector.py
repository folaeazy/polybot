"""
event_collector/collector.py

Generates mock events for development and simulation.
In production, replace _fetch_raw() with a real data source
(news API, sentiment feed, webhook) — nothing else changes.
"""

import logging
from datetime import datetime, timezone

from models.event import Event

logger = logging.getLogger(__name__)


class EventCollector:
    """
    Fetches events and returns them as typed Event objects.

    Currently mocked — returns a fixed set of events on every call.
    The event set is intentionally varied so different markets will
    match on different cycles depending on their questions.

    To connect a real source:
        Replace _fetch_raw() with an HTTP call or queue consumer.
        Keep _parse_events() untouched.
    """

    def get_events(self) -> list[Event]:
        """Fetch all current events and return them as Event objects."""
        raw = self._fetch_raw()
        events = self._parse_events(raw)
        logger.debug("Collected %d events", len(events))
        return events

    def _fetch_raw(self) -> list[dict]:
        """
        Return raw event data.

        MOCKED — replace with a real source when ready:
            response = httpx.get("https://api.newsfeed.com/events")
            return response.json()["events"]
        """
        return [
            {
                "type": "macro",
                "strength": 0.72,
                "keywords": ["fed", "rates", "federal reserve", "interest"],
            },
            {
                "type": "sentiment",
                "strength": 0.65,
                "keywords": ["eth", "ethereum", "crypto"],
            },
            {
                "type": "news",
                "strength": 0.30,
                "keywords": ["apple", "iphone", "foldable"],
            },
            {
                "type": "sentiment",
                "strength": 0.85,
                "keywords": ["gpt", "openai", "ai model"],
            },
        ]

    def _parse_events(self, raw: list[dict]) -> list[Event]:
        """Convert raw dicts into typed Event dataclasses."""
        created_at = datetime.now(tz=timezone.utc)
        return [
            Event(
                type=item["type"],
                strength=item["strength"],
                related_keywords=item["keywords"],
                created_at=created_at,
            )
            for item in raw
        ]