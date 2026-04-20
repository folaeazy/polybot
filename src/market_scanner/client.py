"""
market_scanner/client.py

HTTP client for fetching markets from Polymarket.
Currently returns mocked data — no real API calls are made.

To connect the real API later:
  - Replace _fetch_raw() with an actual httpx/requests call
  - Keep _parse_markets() untouched — it already handles the response shape
"""

from datetime import datetime, timezone

from models.market import Market, Outcome


class PolymarketClient:
    """
    Fetches raw market data and returns parsed Market objects.

    Args:
        api_url: Base URL for the Polymarket API (unused until real calls land).
    """

    def __init__(self, api_url: str = "https://api.polymarket.com") -> None:
        self.api_url = api_url

    def get_markets(self) -> list[Market]:
        """Fetch all available markets and return them as typed dataclasses."""
        raw = self._fetch_raw()
        return self._parse_markets(raw)

    def _fetch_raw(self) -> list[dict]:
        """
        Return raw market data.

        MOCKED — replace with a real HTTP call when ready:
            response = httpx.get(f"{self.api_url}/markets")
            response.raise_for_status()
            return response.json()["markets"]
        """
        return [
            {
                "id": "poly-001",
                "question": "Will ETH exceed $5,000 before July 2025?",
                "outcomes": [
                    {"name": "YES", "price": 0.34},
                    {"name": "NO",  "price": 0.66},
                ],
                "volume": 128_450.75,
                "active": True,
            },
            {
                "id": "poly-002",
                "question": "Will the Fed cut rates in Q3 2025?",
                "outcomes": [
                    {"name": "YES", "price": 0.57},
                    {"name": "NO",  "price": 0.43},
                ],
                "volume": 54_210.00,
                "active": True,
            },
            {
                "id": "poly-003",
                "question": "Will Apple release a foldable iPhone in 2025?",
                "outcomes": [
                    {"name": "YES", "price": 0.12},
                    {"name": "NO",  "price": 0.88},
                ],
                "volume": 8_900.50,
                "active": True,
            },
            {
                "id": "poly-004",
                "question": "Will Bitcoin reach $100k before 2024 ends?",
                "outcomes": [
                    {"name": "YES", "price": 0.91},
                    {"name": "NO",  "price": 0.09},
                ],
                "volume": 310_000.00,
                "active": False,   # resolved — should be filtered out
            },
            {
                "id": "poly-005",
                "question": "Will GPT-5 be released before June 2025?",
                "outcomes": [
                    {"name": "YES", "price": 0.45},
                    {"name": "NO",  "price": 0.55},
                ],
                "volume": 2_100.00,  # low volume — should be filtered out
                "active": True,
            },
        ]

    def _parse_markets(self, raw: list[dict]) -> list[Market]:
        """Convert raw API dicts into typed Market dataclasses."""
        fetched_at = datetime.now(tz=timezone.utc)
        return [
            Market(
                id=item["id"],
                question=item["question"],
                outcomes=[Outcome(name=o["name"], price=o["price"]) for o in item["outcomes"]],
                volume=item["volume"],
                is_active=item["active"],
                fetched_at=fetched_at,
            )
            for item in raw
        ]