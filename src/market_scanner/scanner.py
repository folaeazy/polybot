"""
market_scanner/scanner.py

MarketScanner orchestrates the fetch → filter pipeline.

Both dependencies are injected, keeping this class fully testable
without network calls or hardcoded filter thresholds.

Usage:
    from market_scanner.client import PolymarketClient
    from market_scanner.scanner import MarketScanner

    scanner = MarketScanner(min_volume=10_000)
    markets = scanner.get_active_markets()
"""

import logging
from typing import Protocol

from models.market import Market
from market_scanner import filters

logger = logging.getLogger(__name__)


class MarketSource(Protocol):
    """Any object that can supply a list of markets."""

    def get_markets(self) -> list[Market]: ...


class MarketScanner:
    """
    Fetches markets from a source, applies filters, and returns
    the markets that are ready for signal analysis.

    Args:
        client:     Data source. Defaults to PolymarketClient().
                    Pass any object with get_markets() in tests.
        min_volume: Minimum USD volume a market must have to be returned.
    """

    def __init__(
        self,
        client: MarketSource | None = None,
        min_volume: float = 10_000.0,
    ) -> None:
        from market_scanner.client import PolymarketClient
        self.client: MarketSource = client or PolymarketClient()
        self.min_volume = min_volume

    def get_active_markets(self) -> list[Market]:
        """
        Fetch all markets and return those that pass all filters.

        Returns:
            Filtered list of Market objects, ready for the signal engine.
        """
        markets = self.client.get_markets()
        logger.debug("Fetched %d markets from client", len(markets))

        markets = filters.apply_all(markets, min_volume=self.min_volume)
        logger.debug("%d markets passed filters (min_volume=%.0f)", len(markets), self.min_volume)

        return markets


# ----------------------------------------------------------------------
# Usage example
# ----------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")

    scanner = MarketScanner(min_volume=10_000)
    markets = scanner.get_active_markets()

    print(f"\n{'─' * 52}")
    print(f"  {len(markets)} markets passed filters")
    print(f"{'─' * 52}")

    for m in markets:
        yes_price = next((o.price for o in m.outcomes if o.name == "YES"), None)
        print(
            f"  [{m.id}]  vol=${m.volume:>10,.0f}  "
            f"YES={yes_price:.2f}  {m.question[:45]}"
        )

    print(f"{'─' * 52}\n")