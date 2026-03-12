"""Clerk authentication platform cost provider."""

import os
from datetime import datetime
import httpx
from providers.base import BaseProvider, CostBreakdown, NormalizedCost


class ClerkProvider(BaseProvider):
    """Fetches billing data from Clerk's API.

    Clerk provides user authentication and management.
    Pricing based on MAUs (Monthly Active Users).

    API: https://clerk.com/docs/reference/backend-api
    """

    def __init__(self):
        super().__init__("clerk")
        self.api_key = os.getenv("CLERK_SECRET_KEY")
        self.base_url = "https://api.clerk.com/v1"

    def validate_auth(self) -> bool:
        """Check if Clerk secret key is present."""
        return bool(self.api_key)

    async def get_costs(self, start_date: str, end_date: str) -> NormalizedCost:
        """
        Fetch Clerk billing data.

        Note: Clerk's billing API may be in their dashboard API.
        This implementation uses organization billing endpoint.
        If this returns 404, check Clerk dashboard for actual billing endpoint.
        """
        if not self.validate_auth():
            raise ValueError("CLERK_SECRET_KEY not set")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            # Try to fetch organization billing data
            # Note: Actual endpoint may need adjustment based on Clerk's API
            response = await client.get(
                f"{self.base_url}/organization/billing",
                headers=headers,
                params={
                    "start_date": start_date,
                    "end_date": end_date,
                },
                timeout=30.0,
            )

            # If 404, provide helpful error message
            if response.status_code == 404:
                raise ValueError(
                    "Clerk billing endpoint not found. "
                    "Clerk may not expose billing data via API yet. "
                    "Check https://dashboard.clerk.com for billing info, "
                    "or contact Clerk support to confirm the billing API endpoint."
                )

            response.raise_for_status()
            data = response.json()

            # Parse response (adjust based on actual API structure)
            # Expected structure (to be confirmed):
            # {
            #   "total": 49.00,
            #   "breakdown": {
            #     "maus": 1000,
            #     "cost_per_mau": 0.049,
            #     "base_plan": 25.00
            #   }
            # }

            total = data.get("total", 0)
            breakdown_data = data.get("breakdown", {})

            breakdown = []
            if "base_plan" in breakdown_data:
                breakdown.append(
                    CostBreakdown(service="base_plan", cost=breakdown_data["base_plan"])
                )
            if "maus" in breakdown_data and "cost_per_mau" in breakdown_data:
                mau_cost = breakdown_data["maus"] * breakdown_data["cost_per_mau"]
                breakdown.append(
                    CostBreakdown(service="active_users", cost=mau_cost)
                )

            # If no breakdown, just use total
            if not breakdown and total > 0:
                breakdown.append(CostBreakdown(service="total", cost=total))

            return NormalizedCost(
                platform=self.name,
                period=self._get_period_label(start_date, end_date),
                total_usd=total,
                breakdown=breakdown,
                cached_at=datetime.now(),
                start_date=start_date,
                end_date=end_date,
            )
