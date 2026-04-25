"""
signal_engine/engine.py

SignalEngine runs all registered strategies against a list of markets
and collects every non-None signal they produce.

Usage:
    engine = SignalEngine(strategies=[MomentumStrategy(threshold=0.05)])
    signals = engine.generate_signals(markets)

    # With events (include EventStrategy in strategies list):
    signals = engine.generate_signals(markets, events=events)
"""

import logging

from models.event import Event
from models.market import Market
from models.signal import Signal
from signal_engine.strategies.base import Strategy
from signal_engine.strategies.event_strategy import EventStrategy

logger = logging.getLogger(__name__)


class SignalEngine:
    """
    Runs a configurable list of strategies over a set of markets.

    Each strategy is evaluated independently against each market.
    When events are supplied, any EventStrategy in the list is refreshed
    with the current event set before the run. Strategies that do not
    use events are unaffected.

    Args:
        strategies: One or more Strategy instances to run.
    """

    def __init__(self, strategies: list[Strategy]) -> None:
        self.strategies = strategies

    def generate_signals(
        self,
        markets: list[Market],
        events: list[Event] | None = None,
    ) -> list[Signal]:
        """
        Evaluate all strategies on all markets and return every signal produced.

        Args:
            markets: Current market snapshots, typically from MarketScanner.
            events:  Optional events from EventCollector. When provided,
                     EventStrategy instances are refreshed with this list
                     before running. Passing None (default) leaves existing
                     strategies unchanged — full backward compatibility.

        Returns:
            List of Signal objects. Empty if no strategy fired.
        """
        if events is not None:
            self._update_event_strategies(events)

        signals: list[Signal] = []

        for market in markets:
            for strategy in self.strategies:
                signal = self._run(strategy, market)
                if signal is not None:
                    signals.append(signal)
                    logger.info(
                        "Signal: %s on %s (confidence=%.2f)",
                        signal.signal_type.value,
                        signal.market_id,
                        signal.confidence,
                    )

        if signals:
            logger.debug(
                "%d signal(s) from %d market(s) across %d strategies",
                len(signals), len(markets), len(self.strategies),
            )
        return signals

    def _update_event_strategies(self, events: list[Event]) -> None:
        """Inject the current event list into all EventStrategy instances."""
        for strategy in self.strategies:
            if isinstance(strategy, EventStrategy):
                strategy.events = events

    def _run(self, strategy: Strategy, market: Market) -> Signal | None:
        """
        Run a single strategy against a single market.
        Isolates exceptions so one bad strategy cannot break the engine.
        """
        try:
            return strategy.generate_signal(market)
        except Exception as exc:
            logger.exception(
                "Strategy %s failed on market %s: %s",
                type(strategy).__name__,
                market.id,
                exc,
            )
            return None


# ----------------------------------------------------------------------
# Usage example
# ----------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")

    from models.event import Event
    from models.market import Market, Outcome
    from signal_engine.strategies.event_strategy import EventStrategy
    from signal_engine.strategies.momemtum import MomentumStrategy

    engine = SignalEngine(strategies=[
        MomentumStrategy(threshold=0.05),
        EventStrategy(events=[]),
    ])

    markets = [
        Market(id="poly-001", question="Will ETH exceed $5k?",
               outcomes=[Outcome("YES", 0.40), Outcome("NO", 0.60)],
               volume=100_000, is_active=True),
        Market(id="poly-002", question="Will Fed cut rates?",
               outcomes=[Outcome("YES", 0.55), Outcome("NO", 0.45)],
               volume=50_000, is_active=True),
    ]
    events = [
        Event(type="macro",     strength=0.80, related_keywords=["fed", "rates"]),
        Event(type="sentiment", strength=0.65, related_keywords=["eth", "ethereum"]),
    ]

    print("── No events (momentum only, cycle 1 baseline) ──")
    signals = engine.generate_signals(markets)
    print(f"Signals: {len(signals)}\n")

    print("── With events ──")
    signals = engine.generate_signals(markets, events=events)
    for s in signals:
        print(f"  {s.signal_type.value:<10} market={s.market_id}  confidence={s.confidence:.2f}")