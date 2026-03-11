"""OpenAI cost provider."""

import os
from datetime import datetime

import httpx

from providers.base import BaseProvider, CostBreakdown, NormalizedCost


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI usage API."""

    def __init__(self):
        super().__init__("openai")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"

    def validate_auth(self) -> bool:
        """Check if OpenAI API key is present."""
        return bool(self.api_key)

    async def get_costs(self, start_date: str, end_date: str) -> NormalizedCost:
        """
        Fetch OpenAI costs using usage API.

        API: GET /v1/usage?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
        Returns: Daily breakdown of costs by operation type
        """
        if not self.validate_auth():
            raise ValueError("OPENAI_API_KEY not set")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        params = {"start_date": start_date, "end_date": end_date}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/usage",
                headers=headers,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            # Aggregate costs by operation/model
            breakdown_dict: dict[str, float] = {}
            total = 0.0

            # OpenAI usage API returns daily data
            for daily_usage in data.get("data", []):
                for line_item in daily_usage.get("results", []):
                    operation = line_item.get("operation", "unknown")
                    cost = float(line_item.get("cost", 0))
                    total += cost
                    breakdown_dict[operation] = breakdown_dict.get(operation, 0) + cost

            # Convert to breakdown list
            breakdown = [
                CostBreakdown(service=operation, cost=cost)
                for operation, cost in breakdown_dict.items()
            ]

            return NormalizedCost(
                platform=self.name,
                period=self._get_period_label(start_date, end_date),
                total_usd=total,
                breakdown=breakdown,
                cached_at=datetime.now(),
                start_date=start_date,
                end_date=end_date,
            )
