"""
models/market.py

Market-related data structures.
No business logic — pure data containers.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Outcome:
    """
    A single tradeable outcome within a market.

    Attributes:
        name:  Label for this outcome, e.g. "YES" or "NO".
        price: Implied probability as a decimal in [0.0, 1.0].
    """

    name: str
    price: float


@dataclass
class Market:
    """
    A prediction market snapshot.

    Attributes:
        id:         Unique market identifier from the exchange.
        question:   The binary question being resolved.
        outcomes:   Tradeable outcomes (typically YES / NO).
        volume:     Total traded volume in USD.
        is_active:  False if the market is resolved or suspended.
        fetched_at: When this snapshot was retrieved.
    """

    id: str
    question: str
    outcomes: list[Outcome]
    volume: float
    is_active: bool
    fetched_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


# ----------------------------------------------------------------------
# Usage example
# ----------------------------------------------------------------------
if __name__ == "__main__":
    market = Market(
        id="poly-001",
        question="Will ETH exceed $5000 before July 2025?",
        outcomes=[
            Outcome(name="YES", price=0.34),
            Outcome(name="NO", price=0.66),
        ],
        volume=128_450.75,
        is_active=True,
    )

    print(market)
    print(f"\nOutcomes: {[(o.name, o.price) for o in market.outcomes]}")