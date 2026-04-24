"""
signal_engine/engine.py

SignalEngine runs all registered strategies against a list of markets
and collects every non-None signal they produce.

Usage:
    from signal_engine.engine import SignalEngine
    from signal_engine.strategies.momentum import MomentumStrategy

    engine = SignalEngine(strategies=[MomentumStrategy(threshold=0.05)])
    signals = engine.generate_signals(markets)
"""

import logging

from models.market import Market
from models.signal import Signal
from signal_engine.strategies.base import Strategy

logger = logging.getLogger(__name__)


class SignalEngine:
    """
    Runs a configurable list of strategies over a set of markets.

    Each strategy is evaluated independently against each market.
    Signals are collected in the order they are produced — one strategy
    may emit signals for multiple markets in a single run.

    Args:
        strategies: One or more Strategy instances to run.
    """

    def __init__(self, strategies: list[Strategy]) -> None:
        self.strategies = strategies

    def generate_signals(self, markets: list[Market]) -> list[Signal]:
        """
        Evaluate all strategies on all markets and return every signal produced.

        Args:
            markets: Current market snapshots, typically from MarketScanner.

        Returns:
            List of Signal objects. Empty if no strategy fired.
        """
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

    from models.market import Market, Outcome
    from signal_engine.strategies.momemtum import MomentumStrategy

    engine = SignalEngine(strategies=[MomentumStrategy(threshold=0.05)])

    # Simulate two polling cycles: prices move between cycle 1 and cycle 2.
    cycle_1 = [
        Market(id="poly-001", question="Will ETH exceed $5k?",
               outcomes=[Outcome("YES", 0.40), Outcome("NO", 0.60)],
               volume=100_000, is_active=True),
        Market(id="poly-002", question="Will Fed cut rates?",
               outcomes=[Outcome("YES", 0.55), Outcome("NO", 0.45)],
               volume=50_000, is_active=True),
    ]
    cycle_2 = [
        Market(id="poly-001", question="Will ETH exceed $5k?",
               outcomes=[Outcome("YES", 0.47), Outcome("NO", 0.53)],  # +17.5% → BUY_YES
               volume=102_000, is_active=True),
        Market(id="poly-002", question="Will Fed cut rates?",
               outcomes=[Outcome("YES", 0.48), Outcome("NO", 0.52)],  # -12.7% → BUY_NO
               volume=51_000, is_active=True),
    ]

    print("── Cycle 1 (baseline, no previous prices) ──")
    signals = engine.generate_signals(cycle_1)
    print(f"Signals: {len(signals)}\n")

    print("── Cycle 2 (prices shifted) ──")
    signals = engine.generate_signals(cycle_2)
    for s in signals:
        print(f"  {s.signal_type.value:<10} market={s.market_id}  confidence={s.confidence:.2f}")