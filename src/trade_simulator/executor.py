"""
trade_simulator/executor.py

Abstract interface all execution backends must implement.
Decouples the rest of the system from whether trades are simulated or live.

To add a live backend later:
    class RealTradeExecutor(TradeExecutor): ...

Nothing outside trade_simulator needs to change.
"""

from abc import ABC, abstractmethod

from models.market import Market
from models.signal import Signal
from models.trade import SimResult, Trade


class TradeExecutor(ABC):
    """
    Contract for all trade execution backends.

    The engine calls execute() when a signal arrives.
    The orchestrator calls update_market() on each polling cycle
    so the executor can close positions that hit their exit levels.
    """

    @abstractmethod
    def execute(self, signal: Signal, market: Market) -> Trade | None:
        """
        Act on a signal. Open a position if risk rules allow.

        Args:
            signal: Recommendation from the signal engine.
            market: Current snapshot of the relevant market.

        Returns:
            The opened Trade if successful, None if rejected.
        """
        ...

    @abstractmethod
    def update_market(self, market: Market) -> list[SimResult]:
        """
        Check open positions against the latest market price.
        Close any that have hit take-profit or stop-loss.

        Args:
            market: Fresh snapshot for any market we may hold.

        Returns:
            List of SimResult for every position closed this update.
        """
        ...

    @abstractmethod
    def get_open_positions(self) -> list[Trade]:
        """Return all currently open trades."""
        ...
        
    @abstractmethod
    def get_total_pnl(self) -> float:
        pass    