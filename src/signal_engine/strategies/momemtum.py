"""
signal_engine/strategies/momentum.py

MomentumStrategy: generates a signal when the YES outcome price moves
beyond a configurable threshold since the last observation.

Price history is kept in memory — one entry per market id.
On the first observation of a market there is no previous price,
so no signal is returned.
"""

from models.market import Market
from models.signal import Signal, SignalType
from signal_engine.indicators import price_change_pct
from signal_engine.strategies.base import Strategy


class MomentumStrategy(Strategy):
    """
    Compares the current YES price against the last seen YES price.

    Signal rules:
        change >= +threshold  → BUY_YES  (price rising, YES gaining)
        change <= -threshold  → BUY_NO   (price falling, NO gaining)
        otherwise             → None     (no actionable momentum)

    Confidence is the magnitude of the change relative to the threshold,
    capped at 1.0. A move twice the threshold → confidence 1.0.

    Args:
        threshold: Minimum fractional price change required to emit a signal.
                   Default 0.05 means a 5% move triggers a signal.
    """

    def __init__(self, threshold: float = 0.05) -> None:
        self.threshold = threshold
        self._previous_yes_prices: dict[str, float] = {}

    def generate_signal(self, market: Market) -> Signal | None:
        yes_price = next((o.price for o in market.outcomes if o.name == "YES"), None)
        if yes_price is None:
            return None

        previous_price = self._previous_yes_prices.get(market.id)
        self._previous_yes_prices[market.id] = yes_price

        # First observation — no previous price to compare against yet
        if previous_price is None:
            return None

        change = price_change_pct(old_price=previous_price, new_price=yes_price)
        confidence = min(abs(change) / self.threshold, 1.0)

        if change >= self.threshold:
            return Signal(market_id=market.id, signal_type=SignalType.BUY_YES, confidence=confidence)

        if change <= -self.threshold:
            return Signal(market_id=market.id, signal_type=SignalType.BUY_NO, confidence=confidence)

        return None