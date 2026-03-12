"""Convex backend platform cost provider."""

import os
from datetime import datetime
import httpx
from providers.base import BaseProvider, CostBreakdown, NormalizedCost


class ConvexProvider(BaseProvider):
    """Fetches billing data from Convex's API.

    Convex is a backend-as-a-service platform with database,
    functions, file storage, and real-time sync.

    Pricing based on compute, storage, and bandwidth.

    API: https://docs.convex.dev/api (billing endpoints TBD)
    """

    def __init__(self):
        super().__init__("convex")
        self.api_key = os.getenv("CONVEX_DEPLOY_KEY")
        self.base_url = "https://api.convex.dev/v1"

    def validate_auth(self) -> bool:
        """Check if Convex deploy key is present."""
        return bool(self.api_key)

    async def get_costs(self, start_date: str, end_date: str) -> NormalizedCost:
        """
        Fetch Convex billing data.

        Note: Convex's billing API may be in their dashboard or admin API.
        This implementation attempts to fetch usage/billing data.
        If this returns 404, check Convex dashboard for actual billing endpoint.
        """
        if not self.validate_auth():
            raise ValueError("CONVEX_DEPLOY_KEY not set")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            # Try to fetch team/project billing data
            # Note: Actual endpoint may need adjustment based on Convex's API
            response = await client.get(
                f"{self.base_url}/billing/usage",
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
                    "Convex billing endpoint not found. "
                    "Convex may not expose billing data via API yet. "
                    "Check https://dashboard.convex.dev for billing info, "
                    "or contact Convex support to confirm the billing API endpoint."
                )

            response.raise_for_status()
            data = response.json()

            # Parse response (adjust based on actual API structure)
            # Expected structure (to be confirmed):
            # {
            #   "total_cost": 25.00,
            #   "usage": {
            #     "compute_hours": 100,
            #     "storage_gb": 5.5,
            #     "bandwidth_gb": 50,
            #     "function_calls": 1000000
            #   },
            #   "costs": {
            #     "compute": 15.00,
            #     "storage": 5.00,
            #     "bandwidth": 5.00
            #   }
            # }

            total = data.get("total_cost", 0)
            costs = data.get("costs", {})

            breakdown = []
            for service, cost in costs.items():
                if cost > 0:
                    breakdown.append(CostBreakdown(service=service, cost=cost))

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
