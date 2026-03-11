"""Base provider class for burnmeter cost aggregation."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CostBreakdown(BaseModel):
    """Individual cost item breakdown."""

    service: str
    cost: float
    unit: Optional[str] = None  # e.g., "hours", "GB", "requests"
    quantity: Optional[float] = None


class NormalizedCost(BaseModel):
    """Normalized cost response from any provider."""

    platform: str
    period: str  # e.g., "7d", "30d", "mtd"
    total_usd: float
    currency: str = "USD"
    breakdown: list[CostBreakdown]
    cached_at: datetime
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class BaseProvider(ABC):
    """Abstract base class for cost providers."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def get_costs(
        self, start_date: str, end_date: str
    ) -> NormalizedCost:
        """
        Fetch costs for the given date range.

        Args:
            start_date: ISO format date string (YYYY-MM-DD)
            end_date: ISO format date string (YYYY-MM-DD)

        Returns:
            NormalizedCost object with aggregated costs
        """
        pass

    @abstractmethod
    def validate_auth(self) -> bool:
        """
        Validate that required authentication credentials are present.

        Returns:
            True if credentials are valid, False otherwise
        """
        pass

    def _get_period_label(self, start_date: str, end_date: str) -> str:
        """Generate a period label from date range."""
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        days = (end - start).days

        if days <= 1:
            return "1d"
        elif days <= 7:
            return "7d"
        elif days <= 30:
            return "30d"
        else:
            return f"{days}d"
