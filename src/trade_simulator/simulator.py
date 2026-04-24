"""
trade_simulator/simulator.py

Concrete paper-trading backend. Implements TradeExecutor.
No real orders are placed — all state is in memory.
"""

import logging

from models.market import Market
from models.signal import Signal, SignalType
from models.trade import Position, SimResult, Trade

from trade_simulator.executor import TradeExecutor
from trade_simulator.portfolio import Portfolio
from trade_simulator.risk import RiskManager

logger = logging.getLogger(__name__)

# Exit level offsets relative to entry price.
TAKE_PROFIT_PCT: float = 0.10   # close at +10%
STOP_LOSS_PCT:   float = 0.05   # close at  -5%


class TradeSimulator(TradeExecutor):
    """
    Paper-trading executor.

    execute()            — opens a position when a signal arrives
    update_market()      — closes positions that hit take-profit or stop-loss
    get_open_positions() — exposes current open trades

    Args:
        position_size:   Fixed USD size per trade (passed to RiskManager).
        max_open_trades: Max simultaneous open positions.
    """

    def __init__(
        self,
        position_size: float = 100.0,
        max_open_trades: int = 5,
    ) -> None:
        self.portfolio = Portfolio()
        self.risk = RiskManager(
            position_size=position_size,
            max_open_trades=max_open_trades,
        )

    def execute(self, signal: Signal, market: Market) -> Trade | None:
        """
        Open a simulated position for the given signal.

        Returns the opened Trade so the caller can inspect entry levels,
        or None if the risk manager rejected it.
        """
        outcome = "YES" if signal.signal_type == SignalType.BUY_YES else "NO"
        entry_price = self._outcome_price(market, outcome)

        if entry_price is None:
            logger.debug("No valid price for %s on %s", outcome, signal.market_id)
            return None

        size = self.risk.approve(signal, entry_price, self.portfolio)
        if size is None:
            return None

        position = Position(
            market_id=signal.market_id,
            outcome=outcome,
            entry_price=entry_price,
            size=size,
        )
        trade = Trade(
            position=position,
            take_profit=round(entry_price * (1 + TAKE_PROFIT_PCT), 6),
            stop_loss=round(entry_price * (1 - STOP_LOSS_PCT), 6),
        )
        self.portfolio.open_position(trade)
        return trade

    def update_market(self, market: Market) -> list[SimResult]:
        """
        Evaluate all open positions against the latest market prices.
        Close any that have reached take-profit or stop-loss.

        Returns a SimResult for each position closed.
        """
        results: list[SimResult] = []

        for trade in self.portfolio.get_open_trades():
            pos = trade.position
            if pos.market_id != market.id:
                continue

            current_price = self._outcome_price(market, pos.outcome)
            if current_price is None:
                continue

            if current_price >= trade.take_profit:
                label = "Take-profit"
            elif current_price <= trade.stop_loss:
                label = "Stop-loss"
            else:
                continue

            logger.info("%s hit: %s %s @ %.4f", label, market.id, pos.outcome, current_price)
            results.append(self.portfolio.close_position(trade, current_price))

        return results

    def get_open_positions(self) -> list[Trade]:
        """Return all currently open trades."""
        return self.portfolio.get_open_trades()
    
    def get_total_pnl(self) -> float:
        return self.portfolio.total_profit_loss()


    @staticmethod
    def _outcome_price(market: Market, outcome_name: str) -> float | None:
        """Return the price of a named outcome, or None if not found."""
        return next(
            (o.price for o in market.outcomes if o.name == outcome_name),
            None,
        )


# ----------------------------------------------------------------------
# Usage example
# ----------------------------------------------------------------------
# if __name__ == "__main__":
#     from src.models.market import Market, Outcome
#     from src.models.signal import Signal, SignalType

#     logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

#     simulator = TradeSimulator(position_size=100.0, max_open_trades=5)

#     # ── 1. Initial market snapshot ────────────────────────────────────
#     market_v1 = Market(
#         id="poly-001",
#         question="Will ETH exceed $5k?",
#         outcomes=[Outcome("YES", 0.40), Outcome("NO", 0.60)],
#         volume=100_000,
#         is_active=True,
#     )

#     # ── 2. Signal arrives → open trade ───────────────────────────────
#     signal = Signal(market_id="poly-001", signal_type=SignalType.BUY_YES, confidence=0.80)
#     trade = simulator.execute(signal, market_v1)

#     print(f"\nTrade opened:")
#     print(f"  Entry price : {trade.position.entry_price:.4f}")
#     print(f"  Take-profit : {trade.take_profit:.4f}")
#     print(f"  Stop-loss   : {trade.stop_loss:.4f}")

#     # ── 3. Duplicate signal on same market is rejected ────────────────
#     rejected = simulator.execute(signal, market_v1)
#     print(f"\nDuplicate signal rejected: {rejected is None}")

#     # ── 4. Price rises → take-profit triggered ────────────────────────
#     market_v2 = Market(
#         id="poly-001",
#         question="Will ETH exceed $5k?",
#         outcomes=[Outcome("YES", 0.45), Outcome("NO", 0.55)],  # +12.5% → above tp
#         volume=105_000,
#         is_active=True,
#     )

#     for r in simulator.update_market(market_v2):
#         print(f"\nTrade closed:")
#         print(f"  Result      : {r.result.value}")
#         print(f"  Entry price : {r.entry_price:.4f}")
#         print(f"  Exit price  : {r.exit_price:.4f}")
#         print(f"  P&L         : ${r.profit_loss:.2f}")

#     print(f"\nTotal P&L   : ${simulator.portfolio.total_profit_loss():.2f}")
#     print(f"Open trades : {len(simulator.get_open_positions())}")

#     # ── 5. New signal → stop-loss scenario ───────────────────────────
#     signal2 = Signal(market_id="poly-001", signal_type=SignalType.BUY_YES, confidence=0.6)
#     simulator.execute(signal2, market_v2)

#     market_v3 = Market(
#         id="poly-001",
#         question="Will ETH exceed $5k?",
#         outcomes=[Outcome("YES", 0.38), Outcome("NO", 0.62)],  # below stop-loss
#         volume=98_000,
#         is_active=True,
#     )
#     for r2 in simulator.update_market(market_v3):
#         print(f"\nStop-loss trade closed:")
#         print(f"  Result      : {r2.result.value}")
#         print(f"  P&L         : ${r2.profit_loss:.2f}")

#     print(f"\nFinal P&L   : ${simulator.portfolio.total_profit_loss():.2f}")