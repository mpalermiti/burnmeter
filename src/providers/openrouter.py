"""OpenRouter cost provider."""

import os
from datetime import datetime

import httpx

from providers.base import BaseProvider, CostBreakdown, NormalizedCost


class OpenRouterProvider(BaseProvider):
    """Provider for OpenRouter billing API."""

    def __init__(self):
        super().__init__("openrouter")
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"

    def validate_auth(self) -> bool:
        """Check if OpenRouter API key is present."""
        return bool(self.api_key)

    async def get_costs(self, start_date: str, end_date: str) -> NormalizedCost:
        """
        Fetch OpenRouter costs using credits API.

        API: GET /api/v1/credits - returns total purchased and used
        Note: OpenRouter tracks credits, not historical spending by date range.
        We return the current usage snapshot.
        """
        if not self.validate_auth():
            raise ValueError("OPENROUTER_API_KEY not set")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            # Get current credits
            response = await client.get(
                f"{self.base_url}/credits", headers=headers, timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

            # Credits response: { "data": { "total": 100, "used": 25 } }
            credits_data = data.get("data", {})
            total_credits = float(credits_data.get("total", 0))
            used_credits = float(credits_data.get("used", 0))

            # OpenRouter credits are 1:1 with USD
            total_usd = used_credits

            breakdown = [
                CostBreakdown(
                    service="api_usage",
                    cost=used_credits,
                    unit="credits",
                    quantity=used_credits,
                ),
                CostBreakdown(
                    service="remaining_balance",
                    cost=total_credits - used_credits,
                    unit="credits",
                    quantity=total_credits - used_credits,
                ),
            ]

            return NormalizedCost(
                platform=self.name,
                period=self._get_period_label(start_date, end_date),
                total_usd=total_usd,
                breakdown=breakdown,
                cached_at=datetime.now(),
                start_date=start_date,
                end_date=end_date,
            )
