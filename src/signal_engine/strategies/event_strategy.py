"""
signal_engine/strategies/event_strategy.py

EventStrategy: generates a signal when an event's keywords match a market
question and the event's implied strength diverges from the market price.

Decision logic:
    - Match: any event keyword appears in the market question (case-insensitive)
    - Direction: strength > YES price → market underpricing YES → BUY_YES
                 strength < YES price → market overpricing YES  → BUY_NO
    - Confidence: how far strength diverges from yes_price, scaled to [0, 1]
    - Gate: only act when the divergence exceeds `min_divergence`

This strategy is stateless — it does not remember previous observations.
"""

import logging

from models.event import Event
from models.market import Market
from models.signal import Signal, SignalType
from signal_engine.strategies.base import Strategy

logger = logging.getLogger(__name__)


class EventStrategy(Strategy):
    """
    Matches events to markets and signals when the event implies
    a different probability than the current market price.

    Args:
        events:          Events collected this cycle (injected per call).
        min_divergence:  Minimum gap between event strength and YES price
                         required to emit a signal. Default 0.10 (10 points).
    """

    def __init__(self, events: list[Event], min_divergence: float = 0.10) -> None:
        self.events = events
        self.min_divergence = min_divergence

    def generate_signal(self, market: Market) -> Signal | None:
        """
        Find the strongest matching event and signal if divergence is large enough.

        Returns the signal for the best-matching event, or None if no event
        matches or no divergence clears the threshold.
        """
        yes_price = next((o.price for o in market.outcomes if o.name == "YES"), None)
        if yes_price is None:
            return None

        best = self._best_matching_event(market)
        if best is None:
            return None

        divergence = best.strength - yes_price

        if abs(divergence) < self.min_divergence:
            logger.debug(
                "Event matched %s but divergence %.2f below threshold %.2f",
                market.id, abs(divergence), self.min_divergence,
            )
            return None

        signal_type = SignalType.BUY_YES if divergence > 0 else SignalType.BUY_NO
        confidence = min(abs(divergence) / (1 - self.min_divergence), 1.0)

        logger.debug(
            "Event signal: %s on %s  strength=%.2f  yes_price=%.2f  divergence=%+.2f",
            signal_type.value, market.id, best.strength, yes_price, divergence,
        )
        return Signal(market_id=market.id, signal_type=signal_type, confidence=confidence)

    def _best_matching_event(self, market: Market) -> Event | None:
        """
        Return the event whose keywords best match the market question.

        'Best' is defined as the highest keyword hit count. Ties are broken
        by event strength (stronger event wins). Returns None if no event
        has any keyword match.
        """
        question = market.question.lower()
        best: Event | None = None
        best_hits = 0

        for event in self.events:
            hits = sum(1 for kw in event.related_keywords if kw in question)
            if hits > best_hits or (hits == best_hits and best is not None and event.strength > best.strength):
                best = event
                best_hits = hits

        return best if best_hits > 0 else None