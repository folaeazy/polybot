"""
market_scanner/filters.py

Pure filter functions for Market objects.
Each filter takes a list of markets and returns a filtered list.
Stateless and side-effect free — easy to test and compose.
"""

from models.market import Market


def filter_active(markets: list[Market]) -> list[Market]:
    """Keep only markets that are currently open and tradeable."""
    return [m for m in markets if m.is_active]


def filter_by_min_volume(markets: list[Market], min_volume: float) -> list[Market]:
    """
    Keep only markets with total traded volume at or above the threshold.

    Args:
        markets:    Markets to filter.
        min_volume: Minimum USD volume required (inclusive).
    """
    return [m for m in markets if m.volume >= min_volume]


def apply_all(markets: list[Market], min_volume: float) -> list[Market]:
    """
    Apply all filters in order and return the surviving markets.

    Args:
        markets:    Raw market list from the client.
        min_volume: Passed through to filter_by_min_volume.
    """
    markets = filter_active(markets)
    markets = filter_by_min_volume(markets, min_volume=min_volume)
    return markets