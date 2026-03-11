"""Neon cost provider."""

import os
from datetime import datetime

import httpx

from providers.base import BaseProvider, CostBreakdown, NormalizedCost


class NeonProvider(BaseProvider):
    """Provider for Neon consumption API."""

    def __init__(self):
        super().__init__("neon")
        self.api_key = os.getenv("NEON_API_KEY")
        self.base_url = "https://console.neon.tech/api/v2"

    def validate_auth(self) -> bool:
        """Check if Neon API key is present."""
        return bool(self.api_key)

    async def get_costs(self, start_date: str, end_date: str) -> NormalizedCost:
        """
        Fetch Neon costs using consumption metrics API.

        API: GET /consumption/projects
        Returns: Compute time, storage, and data transfer metrics
        Note: Neon returns usage metrics, not dollar costs directly
        """
        if not self.validate_auth():
            raise ValueError("NEON_API_KEY not set")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        params = {"from": start_date, "to": end_date}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/consumption/projects",
                headers=headers,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            # Neon pricing (approximate):
            # - Compute: $0.16/hour for 1 CU
            # - Storage: $0.000164/GB-hour
            # - Written data: $0.096/GB

            breakdown = []
            total = 0.0

            for project in data.get("projects", []):
                compute_seconds = float(project.get("compute_time_seconds", 0))
                compute_hours = compute_seconds / 3600
                compute_cost = compute_hours * 0.16

                storage_bytes = float(project.get("synthetic_storage_size_bytes", 0))
                storage_gb_hours = (storage_bytes / (1024**3)) * (compute_hours)
                storage_cost = storage_gb_hours * 0.000164

                written_bytes = float(project.get("written_data_bytes", 0))
                written_gb = written_bytes / (1024**3)
                written_cost = written_gb * 0.096

                breakdown.append(
                    CostBreakdown(
                        service="compute",
                        cost=compute_cost,
                        unit="hours",
                        quantity=compute_hours,
                    )
                )
                breakdown.append(
                    CostBreakdown(
                        service="storage",
                        cost=storage_cost,
                        unit="GB-hours",
                        quantity=storage_gb_hours,
                    )
                )
                breakdown.append(
                    CostBreakdown(
                        service="written_data",
                        cost=written_cost,
                        unit="GB",
                        quantity=written_gb,
                    )
                )

                total += compute_cost + storage_cost + written_cost

            return NormalizedCost(
                platform=self.name,
                period=self._get_period_label(start_date, end_date),
                total_usd=total,
                breakdown=breakdown,
                cached_at=datetime.now(),
                start_date=start_date,
                end_date=end_date,
            )
