"""
models/signal.py

Signal-related data structures.
Emitted by signal_engine, consumed by trade_simulator and notifier.
No business logic — pure data containers.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class SignalType(Enum):
    """
    Trading action recommended by the signal engine.

    BUY_YES — open a position on the YES outcome.
    BUY_NO  — open a position on the NO outcome.
    """

    BUY_YES = "BUY_YES"
    BUY_NO = "BUY_NO"


@dataclass
class Signal:
    """
    A trading recommendation produced by the signal engine.

    Attributes:
        market_id:   ID of the market this signal relates to.
        signal_type: The recommended action.
        confidence:  Strength of the signal in [0.0, 1.0].
        created_at:  When the signal was generated.
    """

    market_id: str
    signal_type: SignalType
    confidence: float
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


# ----------------------------------------------------------------------
# Usage example
# ----------------------------------------------------------------------
if __name__ == "__main__":
    signal = Signal(
        market_id="poly-001",
        signal_type=SignalType.BUY_YES,
        confidence=0.78,
    )

    print(signal)
    print(f"\nType       : {signal.signal_type.value}")
    print(f"Confidence : {signal.confidence:.0%}")