"""
signal_engine/strategies/base.py

Abstract base class for all trading strategies.
Every strategy receives a Market and optionally returns a Signal.
"""

from abc import ABC, abstractmethod

from models.market import Market
from models.signal import Signal


class Strategy(ABC):
    """
    Base class for all signal strategies.

    Each strategy encapsulates one decision rule.
    The engine runs all registered strategies against every market
    and collects the non-None results.
    """

    @abstractmethod
    def generate_signal(self, market: Market) -> Signal | None:
        """
        Analyse a market snapshot and return a trading signal.

        Args:
            market: Current snapshot of a single market.

        Returns:
            A Signal if the strategy has a recommendation, None otherwise.
        """
        ...