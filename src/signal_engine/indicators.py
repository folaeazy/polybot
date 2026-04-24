"""
signal_engine/indicators.py

Stateless helper functions for computing price-based indicators.
No dependencies on models or strategies — plain numeric inputs and outputs.
"""


def price_change_pct(old_price: float, new_price: float) -> float:
    """
    Compute the fractional change from old_price to new_price.

    Returns a signed float:
        +0.05 → price rose 5%
        -0.10 → price fell 10%

    Returns 0.0 when old_price is zero to avoid division errors.

    Args:
        old_price: The earlier price observation.
        new_price: The current price observation.
    """
    if old_price == 0:
        return 0.0
    return (new_price - old_price) / old_price