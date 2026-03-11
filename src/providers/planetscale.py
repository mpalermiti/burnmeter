"""PlanetScale cost provider."""

import os
from datetime import datetime

import httpx

from providers.base import BaseProvider, CostBreakdown, NormalizedCost


class PlanetScaleProvider(BaseProvider):
    """Provider for PlanetScale billing API."""

    def __init__(self):
        super().__init__("planetscale")
        self.service_token = os.getenv("PLANETSCALE_SERVICE_TOKEN")
        self.org_name = os.getenv("PLANETSCALE_ORG_NAME")
        self.base_url = "https://api.planetscale.com/v1"

    def validate_auth(self) -> bool:
        """Check if PlanetScale service token and org name are present."""
        return bool(self.service_token and self.org_name)

    async def get_costs(self, start_date: str, end_date: str) -> NormalizedCost:
        """
        Fetch PlanetScale costs using invoices API.

        API: GET /v1/organizations/{org}/invoices
        Returns: Invoice data with line items
        """
        if not self.validate_auth():
            raise ValueError("PLANETSCALE_SERVICE_TOKEN or PLANETSCALE_ORG_NAME not set")

        headers = {
            "Authorization": self.service_token,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            # Get invoices for the organization
            response = await client.get(
                f"{self.base_url}/organizations/{self.org_name}/invoices",
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            breakdown_dict: dict[str, float] = {}
            total = 0.0

            # Process each invoice
            for invoice in data.get("data", []):
                invoice_id = invoice.get("id")

                # Get line items for this invoice
                items_response = await client.get(
                    f"{self.base_url}/organizations/{self.org_name}/invoices/{invoice_id}/line-items",
                    headers=headers,
                    timeout=30.0,
                )
                items_response.raise_for_status()
                items_data = items_response.json()

                # Aggregate line items
                for item in items_data.get("data", []):
                    description = item.get("description", "unknown")
                    amount = float(item.get("amount", 0)) / 100  # Convert cents to dollars

                    breakdown_dict[description] = (
                        breakdown_dict.get(description, 0) + amount
                    )
                    total += amount

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
