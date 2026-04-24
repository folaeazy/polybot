"""
trade_simulator/portfolio.py

Tracks open trades and closed trade history.
All state is in-memory — no persistence.
"""

import logging
from datetime import datetime, timezone

from models.trade import SimResult, Trade, TradeResult, TradeStatus

logger = logging.getLogger(__name__)


class Portfolio:
    """
    In-memory store for open and closed trades.

    Responsibilities:
        - Accept new trades via open_position()
        - Close trades and record SimResult via close_position()
        - Expose current positions and P&L summaries
    """

    def __init__(self) -> None:
        self._open_trades: list[Trade] = []
        self._results: list[SimResult] = []

    def open_position(self, trade: Trade) -> None:
        """Record a newly opened trade."""
        self._open_trades.append(trade)
        logger.info(
            "Position opened: %s %s @ %.4f (tp=%.4f sl=%.4f)",
            trade.position.market_id,
            trade.position.outcome,
            trade.position.entry_price,
            trade.take_profit,
            trade.stop_loss,
        )

    def close_position(self, trade: Trade, exit_price: float) -> SimResult:
        """
        Close an open trade at exit_price and record the result.

        Args:
            trade:      The trade to close (must be in open trades).
            exit_price: Price at which the position is being closed.

        Returns:
            SimResult describing the outcome.
        """
        trade.status = TradeStatus.CLOSED
        self._open_trades.remove(trade)

        pos = trade.position
        profit_loss = (exit_price - pos.entry_price) * pos.size
        duration = (datetime.now(tz=timezone.utc) - pos.opened_at).total_seconds()
        result = TradeResult.WIN if profit_loss > 0 else TradeResult.LOSS

        sim_result = SimResult(
            market_id=pos.market_id,
            outcome=pos.outcome,
            entry_price=pos.entry_price,
            exit_price=exit_price,
            profit_loss=round(profit_loss, 4),
            duration_seconds=round(duration, 2),
            result=result,
        )
        self._results.append(sim_result)

        logger.info(
            "Position closed: %s %s  exit=%.4f  P&L=$%.2f  %s",
            pos.market_id,
            pos.outcome,
            exit_price,
            profit_loss,
            result.value,
        )
        return sim_result

    def get_open_trades(self) -> list[Trade]:
        """All currently open trades."""
        return list(self._open_trades)

    def get_results(self) -> list[SimResult]:
        """All closed trade results."""
        return list(self._results)

    def is_market_open(self, market_id: str) -> bool:
        """True if there is already an open position on this market."""
        return any(t.position.market_id == market_id for t in self._open_trades)

    def total_profit_loss(self) -> float:
        """Sum of P&L across all closed trades."""
        return round(sum(r.profit_loss for r in self._results), 4)