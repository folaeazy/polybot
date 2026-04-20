"""
models/trade.py

Trade-related data structures.
Consumed by trade_simulator, portfolio, and notifier.
No business logic — pure data containers.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class TradeStatus(str, Enum):
    """Lifecycle state of a trade."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"


class TradeResult(str, Enum):
    """Outcome of a closed trade."""

    WIN = "WIN"
    LOSS = "LOSS"


@dataclass
class Position:
    """
    An open stake in a single market outcome.

    Attributes:
        market_id:   ID of the market being traded.
        outcome:     Which side was bought, e.g. "YES" or "NO".
        entry_price: Price paid per share at entry in [0.0, 1.0].
        size:        Dollar amount staked.
        opened_at:   When the position was opened.
    """

    market_id: str
    outcome: str
    entry_price: float
    size: float
    opened_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


@dataclass
class Trade:
    """
    A position with defined exit parameters.

    Attributes:
        position:    The underlying open position.
        take_profit: Price at which to close for a profit.
        stop_loss:   Price at which to close to limit losses.
        status:      OPEN while active, CLOSED once exited.
    """

    position: Position
    take_profit: float
    stop_loss: float
    status: TradeStatus = TradeStatus.OPEN


@dataclass
class SimResult:
    """
    The outcome of a completed simulated trade.

    Attributes:
        market_id:        Market the trade was on.
        outcome:          Which side was traded, e.g. "YES" or "NO".
        entry_price:      Price at open.
        exit_price:       Price at close.
        profit_loss:      Absolute P&L in USD.
        duration_seconds: How long the position was held.
        result:           WIN or LOSS.
    """

    market_id: str
    outcome: str
    entry_price: float
    exit_price: float
    profit_loss: float
    duration_seconds: float
    result: TradeResult


# ----------------------------------------------------------------------
# Usage example
# ----------------------------------------------------------------------
if __name__ == "__main__":
    position = Position(
        market_id="poly-001",
        outcome="YES",
        entry_price=0.34,
        size=100.0,
    )

    trade = Trade(
        position=position,
        take_profit=0.60,
        stop_loss=0.20,
    )

    print(trade)
    print(f"\nMarket : {trade.position.market_id}")
    print(f"Status : {trade.status.value}")

    result = SimResult(
        market_id="poly-001",
        outcome="YES",
        entry_price=0.34,
        exit_price=0.61,
        profit_loss=27.0,
        duration_seconds=3_600.0,
        result=TradeResult.WIN,
    )

    print(f"\nResult : {result.result.value}")
    print(f"P&L    : ${result.profit_loss:.2f}")