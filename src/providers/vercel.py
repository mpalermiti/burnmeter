"""Vercel cost provider."""

import os
from datetime import datetime

import httpx

from providers.base import BaseProvider, CostBreakdown, NormalizedCost


class VercelProvider(BaseProvider):
    """Provider for Vercel billing API."""

    def __init__(self):
        super().__init__("vercel")
        self.token = os.getenv("VERCEL_TOKEN")
        self.base_url = "https://api.vercel.com"

    def validate_auth(self) -> bool:
        """Check if Vercel token is present."""
        return bool(self.token)

    async def get_costs(self, start_date: str, end_date: str) -> NormalizedCost:
        """
        Fetch Vercel costs using the billing charges API.

        API: GET /v1/billing/charges?from=YYYY-MM-DD&to=YYYY-MM-DD
        Returns: JSONL stream with daily charges
        """
        if not self.validate_auth():
            raise ValueError("VERCEL_TOKEN not set")

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        params = {"from": start_date, "to": end_date}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v1/billing/charges",
                headers=headers,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()

            # Parse JSONL response
            lines = response.text.strip().split("\n")
            charges = [eval(line) for line in lines if line]

            # Aggregate by service type
            breakdown_dict: dict[str, float] = {}
            total = 0.0

            for charge in charges:
                # Vercel charges have: date, total, breakdown by service
                if "total" in charge:
                    total += float(charge["total"])

                # Aggregate breakdown items
                if "items" in charge:
                    for item in charge["items"]:
                        service = item.get("name", "unknown")
                        cost = float(item.get("amount", 0))
                        breakdown_dict[service] = breakdown_dict.get(service, 0) + cost

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
