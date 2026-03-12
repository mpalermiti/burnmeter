"""Railway cost provider."""

import os
from datetime import datetime

import httpx

from providers.base import BaseProvider, CostBreakdown, NormalizedCost


class RailwayProvider(BaseProvider):
    """Provider for Railway GraphQL API."""

    def __init__(self):
        super().__init__("railway")
        self.api_key = os.getenv("RAILWAY_API_KEY")
        self.base_url = "https://backboard.railway.com/graphql/v2"

    def validate_auth(self) -> bool:
        """Check if Railway API key is present."""
        return bool(self.api_key)

    async def get_costs(self, start_date: str, end_date: str) -> NormalizedCost:
        """
        Fetch Railway costs using GraphQL API.

        API: POST https://backboard.railway.com/graphql/v2
        Note: This implementation uses common GraphQL patterns.
        May need refinement based on actual Railway schema.

        To find the exact query Railway uses:
        1. Open Railway dashboard → Usage page
        2. Open browser DevTools → Network tab
        3. Look for requests to backboard.railway.com/graphql/v2
        4. Copy the actual query structure
        """
        if not self.validate_auth():
            raise ValueError("RAILWAY_API_KEY not set")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # GraphQL query to fetch usage/billing data
        # This structure is based on common patterns - may need adjustment
        query = """
        query GetProjectUsage {
          me {
            projects {
              edges {
                node {
                  id
                  name
                  usage {
                    currentPeriod {
                      estimatedCost
                      measurementTime
                      services {
                        service
                        cost
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers=headers,
                json={"query": query},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            # Check for GraphQL errors
            if "errors" in data:
                errors = data["errors"]
                error_messages = [e.get("message", str(e)) for e in errors]
                raise ValueError(
                    f"Railway GraphQL error: {', '.join(error_messages)}\n\n"
                    f"Note: This query structure may need adjustment. "
                    f"Check Railway dashboard network tab for actual query structure."
                )

            # Extract cost data from response
            total = 0.0
            breakdown_dict: dict[str, float] = {}

            try:
                projects = data["data"]["me"]["projects"]["edges"]

                for project in projects:
                    node = project["node"]
                    usage = node.get("usage", {})
                    current_period = usage.get("currentPeriod", {})

                    # Add to total
                    estimated_cost = float(current_period.get("estimatedCost", 0))
                    total += estimated_cost

                    # Aggregate service breakdown
                    services = current_period.get("services", [])
                    for service_data in services:
                        service = service_data.get("service", "unknown")
                        cost = float(service_data.get("cost", 0))
                        breakdown_dict[service] = breakdown_dict.get(service, 0) + cost

            except (KeyError, TypeError) as e:
                raise ValueError(
                    f"Failed to parse Railway response: {e}\n"
                    f"Response structure may have changed. Check Railway API docs."
                )

            # Convert to breakdown list
            breakdown = [
                CostBreakdown(service=service, cost=cost)
                for service, cost in breakdown_dict.items()
            ]

            # If no breakdown available, add a single item
            if not breakdown and total > 0:
                breakdown = [CostBreakdown(service="total", cost=total)]

            return NormalizedCost(
                platform=self.name,
                period=self._get_period_label(start_date, end_date),
                total_usd=total,
                breakdown=breakdown,
                cached_at=datetime.now(),
                start_date=start_date,
                end_date=end_date,
            )
