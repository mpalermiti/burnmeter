"""Tests for provider implementations with mocked HTTP responses."""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from providers.vercel import VercelProvider
from providers.railway import RailwayProvider
from providers.openai import OpenAIProvider
from providers.anthropic import AnthropicProvider


class TestVercelProvider:
    """Test Vercel provider with mocked HTTP."""

    @pytest.fixture
    def provider(self):
        with patch.dict('os.environ', {'VERCEL_TOKEN': 'test-token'}):
            return VercelProvider()

    def test_validate_auth(self, provider):
        """Test auth validation."""
        assert provider.validate_auth() is True

    def test_validate_auth_missing(self):
        """Test auth validation fails without token."""
        with patch.dict('os.environ', {}, clear=True):
            provider = VercelProvider()
            assert provider.validate_auth() is False

    @pytest.mark.asyncio
    async def test_get_costs_success(self, provider):
        """Test successful cost retrieval."""
        mock_response = MagicMock()
        mock_response.text = '''{"total": 95.50, "items": [{"name": "functions", "amount": 45.20}, {"name": "bandwidth", "amount": 50.30}]}
{"total": 10.00, "items": [{"name": "functions", "amount": 10.00}]}'''
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await provider.get_costs("2026-03-01", "2026-03-07")

            assert result.platform == "vercel"
            assert result.total_usd == 105.50
            assert len(result.breakdown) == 2
            assert result.breakdown[0].service == "functions"
            assert result.breakdown[0].cost == 55.20

    @pytest.mark.asyncio
    async def test_get_costs_no_auth(self):
        """Test get_costs fails without auth."""
        with patch.dict('os.environ', {}, clear=True):
            provider = VercelProvider()
            with pytest.raises(ValueError, match="VERCEL_TOKEN not set"):
                await provider.get_costs("2026-03-01", "2026-03-07")


class TestRailwayProvider:
    """Test Railway provider with mocked GraphQL."""

    @pytest.fixture
    def provider(self):
        with patch.dict('os.environ', {'RAILWAY_API_KEY': 'test-key'}):
            return RailwayProvider()

    def test_validate_auth(self, provider):
        """Test auth validation."""
        assert provider.validate_auth() is True

    @pytest.mark.asyncio
    async def test_get_costs_success(self, provider):
        """Test successful GraphQL cost retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "me": {
                    "projects": {
                        "edges": [
                            {
                                "node": {
                                    "id": "proj1",
                                    "name": "test-project",
                                    "usage": {
                                        "currentPeriod": {
                                            "estimatedCost": 25.50,
                                            "services": [
                                                {"service": "compute", "cost": 15.00},
                                                {"service": "storage", "cost": 10.50}
                                            ]
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await provider.get_costs("2026-03-01", "2026-03-07")

            assert result.platform == "railway"
            assert result.total_usd == 25.50
            assert len(result.breakdown) == 2

    @pytest.mark.asyncio
    async def test_get_costs_graphql_error(self, provider):
        """Test GraphQL error handling."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "errors": [
                {"message": "Authentication failed"}
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            with pytest.raises(ValueError, match="Railway GraphQL error"):
                await provider.get_costs("2026-03-01", "2026-03-07")


class TestOpenAIProvider:
    """Test OpenAI provider."""

    @pytest.fixture
    def provider(self):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            return OpenAIProvider()

    def test_validate_auth(self, provider):
        """Test auth validation."""
        assert provider.validate_auth() is True

    @pytest.mark.asyncio
    async def test_get_costs_success(self, provider):
        """Test successful cost retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "aggregation_timestamp": 1709251200,
                    "n_requests": 100,
                    "operation": "completion",
                    "snapshot_id": "gpt-4",
                    "n_context_tokens_total": 50000,
                    "n_generated_tokens_total": 10000
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await provider.get_costs("2026-03-01", "2026-03-07")

            assert result.platform == "openai"
            assert result.total_usd >= 0
            assert isinstance(result.breakdown, list)


class TestAnthropicProvider:
    """Test Anthropic provider."""

    @pytest.fixture
    def provider(self):
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-admin-test'}):
            return AnthropicProvider()

    def test_validate_auth_admin_key(self, provider):
        """Test auth validation with admin key."""
        assert provider.validate_auth() is True

    def test_validate_auth_regular_key(self):
        """Test auth validation fails with regular key."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-regular'}):
            provider = AnthropicProvider()
            assert provider.validate_auth() is False

    @pytest.mark.asyncio
    async def test_get_costs_success(self, provider):
        """Test successful cost retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "costs": [
                {
                    "date": "2026-03-01",
                    "amount": 25.50
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await provider.get_costs("2026-03-01", "2026-03-07")

            assert result.platform == "anthropic"
            assert result.total_usd >= 0
