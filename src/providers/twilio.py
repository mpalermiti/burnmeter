"""Twilio cost provider."""

import os
from datetime import datetime

import httpx

from providers.base import BaseProvider, CostBreakdown, NormalizedCost


class TwilioProvider(BaseProvider):
    """Provider for Twilio Usage API."""

    def __init__(self):
        super().__init__("twilio")
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.base_url = "https://api.twilio.com/2010-04-01"

    def validate_auth(self) -> bool:
        """Check if Twilio credentials are present."""
        return bool(self.account_sid and self.auth_token)

    async def get_costs(self, start_date: str, end_date: str) -> NormalizedCost:
        """
        Fetch Twilio costs using Usage Records API.

        API: GET /2010-04-01/Accounts/{AccountSid}/Usage/Records
        Returns: Usage records with prices per category
        """
        if not self.validate_auth():
            raise ValueError("TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN not set")

        auth = httpx.BasicAuth(self.account_sid, self.auth_token)

        async with httpx.AsyncClient() as client:
            # Get usage records for date range
            params = {
                "StartDate": start_date,
                "EndDate": end_date,
            }

            response = await client.get(
                f"{self.base_url}/Accounts/{self.account_sid}/Usage/Records",
                auth=auth,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            # Aggregate costs by category
            breakdown_dict: dict[str, float] = {}
            total = 0.0

            for record in data.get("usage_records", []):
                category = record.get("category", "unknown")
                price = float(record.get("price", 0))

                # Twilio returns negative prices (costs)
                cost = abs(price)

                breakdown_dict[category] = breakdown_dict.get(category, 0) + cost
                total += cost

            # Convert to breakdown list
            breakdown = [
                CostBreakdown(service=category, cost=cost)
                for category, cost in breakdown_dict.items()
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
