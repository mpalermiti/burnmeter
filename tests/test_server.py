"""Tests for MCP server and tools."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

# Import after conftest adds src to path
from server import _parse_period, get_total_costs, check_budget, list_platforms
from providers.base import NormalizedCost, CostBreakdown


class TestParsePeriod:
    """Test period parsing logic."""

    def test_parse_7d(self):
        """Test 7-day period parsing."""
        start, end = _parse_period("7d")
        assert len(start) == 10  # YYYY-MM-DD format
        assert len(end) == 10

    def test_parse_30d(self):
        """Test 30-day period parsing."""
        start, end = _parse_period("30d")
        assert len(start) == 10
        assert len(end) == 10

    def test_parse_mtd(self):
        """Test month-to-date parsing."""
        start, end = _parse_period("mtd")
        assert start.endswith("-01")  # First day of month

    def test_parse_current_cycle(self):
        """Test current cycle parsing."""
        start, end = _parse_period("current_cycle")
        assert start.endswith("-01")

    def test_parse_invalid(self):
        """Test invalid period raises error."""
        with pytest.raises(ValueError, match="Invalid period"):
            _parse_period("invalid")


class TestGetTotalCosts:
    """Test get_total_costs MCP tool."""

    @pytest.mark.asyncio
    async def test_get_total_costs_success(self):
        """Test successful cost aggregation."""
        mock_cost = NormalizedCost(
            platform="vercel",
            period="7d",
            total_usd=95.50,
            breakdown=[CostBreakdown(service="functions", cost=95.50)],
            cached_at=datetime.now(),
            start_date="2026-03-01",
            end_date="2026-03-07"
        )

        with patch('server.PROVIDERS') as mock_providers:
            mock_provider = MagicMock()
            mock_provider.validate_auth.return_value = True
            mock_provider.get_costs = AsyncMock(return_value=mock_cost)
            mock_providers.get.return_value = mock_provider
            mock_providers.keys.return_value = ["vercel"]

            with patch('server.cache') as mock_cache:
                mock_cache.get.return_value = None

                result = await get_total_costs("7d", ["vercel"])

                assert result["total_usd"] == 95.50
                assert result["period"] == "7d"
                assert len(result["platforms"]) == 1
                assert result["platforms"][0]["platform"] == "vercel"

    @pytest.mark.asyncio
    async def test_get_total_costs_no_auth(self):
        """Test handling of missing auth."""
        with patch('server.PROVIDERS') as mock_providers:
            mock_provider = MagicMock()
            mock_provider.validate_auth.return_value = False
            mock_providers.get.return_value = mock_provider
            mock_providers.keys.return_value = ["vercel"]

            result = await get_total_costs("7d", ["vercel"])

            assert result["total_usd"] == 0.0
            assert "Missing API credentials" in result["errors"][0]

    @pytest.mark.asyncio
    async def test_get_total_costs_api_error(self):
        """Test handling of API errors."""
        with patch('server.PROVIDERS') as mock_providers:
            mock_provider = MagicMock()
            mock_provider.validate_auth.return_value = True
            mock_provider.get_costs = AsyncMock(side_effect=Exception("API Error"))
            mock_providers.get.return_value = mock_provider
            mock_providers.keys.return_value = ["vercel"]

            with patch('server.cache') as mock_cache:
                mock_cache.get.return_value = None

                result = await get_total_costs("7d", ["vercel"])

                assert result["total_usd"] == 0.0
                assert any("API Error" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_get_total_costs_with_cache(self):
        """Test cache hit."""
        mock_cost = NormalizedCost(
            platform="vercel",
            period="7d",
            total_usd=95.50,
            breakdown=[CostBreakdown(service="functions", cost=95.50)],
            cached_at=datetime.now(),
            start_date="2026-03-01",
            end_date="2026-03-07"
        )

        with patch('server.PROVIDERS') as mock_providers:
            mock_provider = MagicMock()
            mock_provider.validate_auth.return_value = True
            mock_provider.get_costs = AsyncMock()  # Should not be called
            mock_providers.get.return_value = mock_provider
            mock_providers.keys.return_value = ["vercel"]

            with patch('server.cache') as mock_cache:
                mock_cache.get.return_value = mock_cost  # Cache hit

                result = await get_total_costs("7d", ["vercel"])

                assert result["total_usd"] == 95.50
                mock_provider.get_costs.assert_not_called()  # Verify cache was used


class TestCheckBudget:
    """Test check_budget MCP tool."""

    @pytest.mark.asyncio
    async def test_check_budget_under(self):
        """Test budget check when under budget."""
        with patch('server.get_total_costs') as mock_get_costs:
            mock_get_costs.return_value = {
                "total_usd": 450.00,
                "platforms": []
            }

            result = await check_budget(500.0, "mtd")

            assert result["budget_usd"] == 500.0
            assert result["spent_usd"] == 450.0
            assert result["remaining_usd"] == 50.0
            assert result["percentage_used"] == 90.0
            assert result["over_budget"] is False

    @pytest.mark.asyncio
    async def test_check_budget_over(self):
        """Test budget check when over budget."""
        with patch('server.get_total_costs') as mock_get_costs:
            mock_get_costs.return_value = {
                "total_usd": 550.00,
                "platforms": []
            }

            result = await check_budget(500.0, "mtd")

            assert result["over_budget"] is True
            assert result["remaining_usd"] == -50.0


class TestListPlatforms:
    """Test list_platforms MCP tool."""

    def test_list_platforms(self):
        """Test platform listing."""
        with patch('server.PROVIDERS') as mock_providers:
            mock_provider = MagicMock()
            mock_provider.validate_auth.return_value = True
            mock_provider.name = "vercel"

            mock_providers.items.return_value = [("vercel", mock_provider)]

            result = list_platforms()

            assert "platforms" in result
            assert "vercel" in result["platforms"]
            assert result["platforms"]["vercel"]["configured"] is True
            assert result["total_configured"] == 1
            assert result["total_available"] == 1
