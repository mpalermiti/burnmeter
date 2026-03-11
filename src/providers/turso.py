"""Turso cost provider."""

import os
from datetime import datetime

import httpx

from providers.base import BaseProvider, CostBreakdown, NormalizedCost


class TursoProvider(BaseProvider):
    """Provider for Turso Platform API."""

    def __init__(self):
        super().__init__("turso")
        self.api_token = os.getenv("TURSO_API_TOKEN")
        self.org_name = os.getenv("TURSO_ORG_NAME")
        self.base_url = "https://api.turso.tech/v1"

    def validate_auth(self) -> bool:
        """Check if Turso API token and org name are present."""
        return bool(self.api_token and self.org_name)

    async def get_costs(self, start_date: str, end_date: str) -> NormalizedCost:
        """
        Fetch Turso costs using organization usage API.

        API: GET /v1/organizations/{org}/usage
        Returns: Current billing cycle usage (rows read/written, storage)
        Note: Returns usage for current cycle, not historical date ranges
        """
        if not self.validate_auth():
            raise ValueError("TURSO_API_TOKEN or TURSO_ORG_NAME not set")

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/organizations/{self.org_name}/usage",
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            # Turso pricing (overages):
            # - $1.00 per extra billion rows read
            # - $1.00 per extra million rows written
            # - $0.75 per extra GB storage

            usage = data.get("usage", {})
            rows_read = float(usage.get("rows_read", 0))
            rows_written = float(usage.get("rows_written", 0))
            storage_bytes = float(usage.get("storage_bytes", 0))

            # Calculate costs (assuming all usage is overage for simplicity)
            read_cost = (rows_read / 1_000_000_000) * 1.00
            write_cost = (rows_written / 1_000_000) * 1.00
            storage_gb = storage_bytes / (1024**3)
            storage_cost = storage_gb * 0.75

            breakdown = [
                CostBreakdown(
                    service="rows_read",
                    cost=read_cost,
                    unit="billion_rows",
                    quantity=rows_read / 1_000_000_000,
                ),
                CostBreakdown(
                    service="rows_written",
                    cost=write_cost,
                    unit="million_rows",
                    quantity=rows_written / 1_000_000,
                ),
                CostBreakdown(
                    service="storage",
                    cost=storage_cost,
                    unit="GB",
                    quantity=storage_gb,
                ),
            ]

            total = read_cost + write_cost + storage_cost

            return NormalizedCost(
                platform=self.name,
                period=self._get_period_label(start_date, end_date),
                total_usd=total,
                breakdown=breakdown,
                cached_at=datetime.now(),
                start_date=start_date,
                end_date=end_date,
            )
