"""
trade_simulator/risk.py

Stateless risk rules applied before any trade is opened.
Returns position size if approved, None if any rule rejects the trade.
No side effects, no state — easy to test and extend.
"""

import logging

from models.signal import Signal
from trade_simulator.portfolio import Portfolio

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Evaluates whether a new trade is permissible.

    Rules (all must pass):
        1. No existing open position on the same market.
        2. Total open trades below max_open_trades.
        3. Entry price is positive.
    """

    def __init__(
        self,
        position_size: float = 100.0,
        max_open_trades: int = 5,
    ) -> None:
        self.position_size = position_size
        self.max_open_trades = max_open_trades

    def approve(
        self,
        signal: Signal,
        entry_price: float,
        portfolio: Portfolio,
    ) -> float | None:
        """
        Check all risk rules and return position size if approved, else None.

        Args:
            signal:      Incoming signal to evaluate.
            entry_price: Proposed fill price for the position.
            portfolio:   Current portfolio state.
        """
        if portfolio.is_market_open(signal.market_id):
            logger.debug("Rejected: already have open position on %s", signal.market_id)
            return None

        if len(portfolio.get_open_trades()) >= self.max_open_trades:
            logger.debug("Rejected: max open trades (%d) reached", self.max_open_trades)
            return None

        if entry_price <= 0:
            logger.debug("Rejected: invalid entry price %.4f on %s", entry_price, signal.market_id)
            return None

        return self.position_size