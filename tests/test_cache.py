"""Tests for cache implementation."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from cache import Cache
from providers.base import NormalizedCost, CostBreakdown


class TestCache:
    """Test cache functionality."""

    @pytest.fixture
    def cache(self):
        """Create fresh cache instance."""
        return Cache(ttl_seconds=3600)

    @pytest.fixture
    def mock_cost(self):
        """Create mock cost data."""
        return NormalizedCost(
            platform="vercel",
            period="7d",
            total_usd=95.50,
            breakdown=[CostBreakdown(service="functions", cost=95.50)],
            cached_at=datetime.now(),
            start_date="2026-03-01",
            end_date="2026-03-07"
        )

    def test_cache_set_and_get(self, cache, mock_cost):
        """Test basic cache set/get."""
        cache.set("vercel", "2026-03-01", "2026-03-07", mock_cost)
        result = cache.get("vercel", "2026-03-01", "2026-03-07")

        assert result is not None
        assert result.platform == "vercel"
        assert result.total_usd == 95.50

    def test_cache_miss(self, cache):
        """Test cache miss returns None."""
        result = cache.get("vercel", "2026-03-01", "2026-03-07")
        assert result is None

    def test_cache_expiration(self, cache, mock_cost):
        """Test cache expiration after TTL."""
        # Set cache with 1 second TTL
        short_cache = Cache(ttl_seconds=1)
        short_cache.set("vercel", "2026-03-01", "2026-03-07", mock_cost)

        # Verify it's there
        assert short_cache.get("vercel", "2026-03-01", "2026-03-07") is not None

        # Mock time passage
        future_time = datetime.now() + timedelta(seconds=2)
        with patch('cache.datetime') as mock_datetime:
            mock_datetime.now.return_value = future_time

            result = short_cache.get("vercel", "2026-03-01", "2026-03-07")
            assert result is None  # Should be expired

    def test_cache_different_dates(self, cache, mock_cost):
        """Test cache differentiates by date range."""
        cache.set("vercel", "2026-03-01", "2026-03-07", mock_cost)

        # Different date range should miss
        result = cache.get("vercel", "2026-03-08", "2026-03-14")
        assert result is None

        # Same date range should hit
        result = cache.get("vercel", "2026-03-01", "2026-03-07")
        assert result is not None

    def test_cache_different_platforms(self, cache, mock_cost):
        """Test cache differentiates by platform."""
        cache.set("vercel", "2026-03-01", "2026-03-07", mock_cost)

        # Different platform should miss
        result = cache.get("railway", "2026-03-01", "2026-03-07")
        assert result is None

        # Same platform should hit
        result = cache.get("vercel", "2026-03-01", "2026-03-07")
        assert result is not None

    def test_cache_key_generation(self, cache):
        """Test cache key generation is consistent."""
        key1 = cache._make_key("vercel", "2026-03-01", "2026-03-07")
        key2 = cache._make_key("vercel", "2026-03-01", "2026-03-07")

        assert key1 == key2
        assert "vercel" in key1
        assert "2026-03-01" in key1
        assert "2026-03-07" in key1
