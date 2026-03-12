"""Anthropic cost provider."""

import os
from datetime import datetime

import httpx

from providers.base import BaseProvider, CostBreakdown, NormalizedCost


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic Admin API."""

    def __init__(self):
        super().__init__("anthropic")
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.base_url = "https://api.anthropic.com/v1"

    def validate_auth(self) -> bool:
        """Check if Anthropic API key is present and is an admin key."""
        # Admin API keys start with sk-ant-admin-
        return bool(self.api_key and self.api_key.startswith("sk-ant-admin-"))

    async def get_costs(self, start_date: str, end_date: str) -> NormalizedCost:
        """
        Fetch Anthropic costs using Admin API cost report.

        API: GET /v1/organizations/cost_report
        Requires: Admin API key (sk-ant-admin-...)
        Returns: Service-level cost breakdowns in USD
        """
        if not self.validate_auth():
            raise ValueError("ANTHROPIC_API_KEY not set or not an admin key")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        params = {"start_date": start_date, "end_date": end_date}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/organizations/cost_report",
                headers=headers,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            # Aggregate costs by service type
            breakdown_dict: dict[str, float] = {}
            total = 0.0

            # Anthropic returns costs in cents, convert to dollars
            for item in data.get("costs", []):
                service = item.get("type", "unknown")
                cost_cents = float(item.get("amount", 0))
                cost_usd = cost_cents / 100
                total += cost_usd
                breakdown_dict[service] = breakdown_dict.get(service, 0) + cost_usd

            # Convert to breakdown list
            breakdown = [
                CostBreakdown(service=service, cost=cost)
                for service, cost in breakdown_dict.items()
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
