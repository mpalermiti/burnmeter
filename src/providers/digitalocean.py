"""DigitalOcean cost provider."""

import os
from datetime import datetime

import httpx

from providers.base import BaseProvider, CostBreakdown, NormalizedCost


class DigitalOceanProvider(BaseProvider):
    """Provider for DigitalOcean Billing API."""

    def __init__(self):
        super().__init__("digitalocean")
        self.token = os.getenv("DIGITALOCEAN_TOKEN")
        self.base_url = "https://api.digitalocean.com/v2"

    def validate_auth(self) -> bool:
        """Check if DigitalOcean token is present."""
        return bool(self.token)

    async def get_costs(self, start_date: str, end_date: str) -> NormalizedCost:
        """
        Fetch DigitalOcean costs using billing history API.

        API: GET /v2/customers/my/billing_history
        Returns: Invoice and payment history
        """
        if not self.validate_auth():
            raise ValueError("DIGITALOCEAN_TOKEN not set")

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            # Get billing history
            response = await client.get(
                f"{self.base_url}/customers/my/billing_history",
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            # Also get current balance
            balance_response = await client.get(
                f"{self.base_url}/customers/my/balance",
                headers=headers,
                timeout=30.0,
            )
            balance_response.raise_for_status()
            balance_data = balance_response.json()

            # Parse billing history
            breakdown_dict: dict[str, float] = {}
            total = 0.0

            for item in data.get("billing_history", []):
                # Filter by date range
                item_date = item.get("date", "")
                if start_date <= item_date <= end_date:
                    item_type = item.get("type", "unknown")
                    amount = float(item.get("amount", 0))

                    # Only count invoices/charges, not payments/credits
                    if item.get("type") in ["Invoice", "Charge"]:
                        total += amount
                        breakdown_dict[item_type] = (
                            breakdown_dict.get(item_type, 0) + amount
                        )

            # Add current month-to-date usage
            mtd_balance = abs(float(balance_data.get("month_to_date_balance", 0)))
            if mtd_balance > 0:
                breakdown_dict["month_to_date"] = mtd_balance
                total += mtd_balance

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
