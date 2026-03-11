"""Simple in-memory cache for API responses."""

import os
from datetime import datetime, timedelta
from typing import Optional

from providers.base import NormalizedCost


class CostCache:
    """In-memory cache with TTL for cost data."""

    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize cache.

        Args:
            ttl_seconds: Time-to-live for cached entries (default 1 hour)
        """
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[NormalizedCost, datetime]] = {}

    def _make_key(self, platform: str, start_date: str, end_date: str) -> str:
        """Generate cache key from parameters."""
        return f"{platform}:{start_date}:{end_date}"

    def get(
        self, platform: str, start_date: str, end_date: str
    ) -> Optional[NormalizedCost]:
        """
        Retrieve cached cost data if available and not expired.

        Returns:
            NormalizedCost if cached and fresh, None otherwise
        """
        key = self._make_key(platform, start_date, end_date)
        if key not in self._cache:
            return None

        cost_data, cached_at = self._cache[key]
        age = datetime.now() - cached_at

        if age.total_seconds() > self.ttl_seconds:
            # Expired, remove from cache
            del self._cache[key]
            return None

        return cost_data

    def set(
        self, platform: str, start_date: str, end_date: str, cost_data: NormalizedCost
    ) -> None:
        """Store cost data in cache with current timestamp."""
        key = self._make_key(platform, start_date, end_date)
        self._cache[key] = (cost_data, datetime.now())

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()


# Global cache instance
_cache_ttl = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
cache = CostCache(ttl_seconds=_cache_ttl)
