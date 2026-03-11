"""MongoDB Atlas cost provider."""

import asyncio
import os
from datetime import datetime

import httpx

from providers.base import BaseProvider, CostBreakdown, NormalizedCost


class MongoDBAtlasProvider(BaseProvider):
    """Provider for MongoDB Atlas Admin API."""

    def __init__(self):
        super().__init__("mongodb_atlas")
        self.public_key = os.getenv("MONGODB_ATLAS_PUBLIC_KEY")
        self.private_key = os.getenv("MONGODB_ATLAS_PRIVATE_KEY")
        self.org_id = os.getenv("MONGODB_ATLAS_ORG_ID")
        self.base_url = "https://cloud.mongodb.com/api/atlas/v2"

    def validate_auth(self) -> bool:
        """Check if MongoDB Atlas credentials are present."""
        return bool(self.public_key and self.private_key and self.org_id)

    async def get_costs(self, start_date: str, end_date: str) -> NormalizedCost:
        """
        Fetch MongoDB Atlas costs using Cost Explorer API.

        API: POST /v2/orgs/{orgId}/billing/costExplorer/usage
        Returns: Token for polling, then cost data
        Note: This is an asynchronous API that requires polling
        """
        if not self.validate_auth():
            raise ValueError(
                "MONGODB_ATLAS_PUBLIC_KEY, MONGODB_ATLAS_PRIVATE_KEY, "
                "or MONGODB_ATLAS_ORG_ID not set"
            )

        auth = httpx.DigestAuth(self.public_key, self.private_key)
        headers = {"Content-Type": "application/json"}

        # Create Cost Explorer query
        query_body = {
            "startDate": start_date,
            "endDate": end_date,
            "groupBy": "services",
        }

        async with httpx.AsyncClient() as client:
            # Initiate the Cost Explorer query
            response = await client.post(
                f"{self.base_url}/orgs/{self.org_id}/billing/costExplorer/usage",
                auth=auth,
                headers=headers,
                json=query_body,
                timeout=30.0,
            )
            response.raise_for_status()
            query_data = response.json()

            # Get the token for polling
            token = query_data.get("token")
            if not token:
                raise ValueError("No token returned from Cost Explorer API")

            # Poll for results (max 10 attempts, 2 seconds apart)
            for _ in range(10):
                await asyncio.sleep(2)

                poll_response = await client.get(
                    f"{self.base_url}/orgs/{self.org_id}/billing/costExplorer/usage/{token}",
                    auth=auth,
                    headers=headers,
                    timeout=30.0,
                )
                poll_response.raise_for_status()
                result = poll_response.json()

                # Check if query is complete
                if result.get("status") == "COMPLETED":
                    breakdown_dict: dict[str, float] = {}
                    total = 0.0

                    # Parse results
                    for item in result.get("results", []):
                        service = item.get("groupBy", {}).get("service", "unknown")
                        cost = float(item.get("cost", 0))
                        breakdown_dict[service] = breakdown_dict.get(service, 0) + cost
                        total += cost

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

                elif result.get("status") == "FAILED":
                    raise ValueError("Cost Explorer query failed")

            # Timeout after 10 attempts
            raise TimeoutError("Cost Explorer query timed out after 20 seconds")
