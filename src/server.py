"""Burnmeter MCP Server - Multi-cloud cost aggregation."""

import os
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from cache import cache
from providers.anthropic import AnthropicProvider
from providers.base import BaseProvider
from providers.digitalocean import DigitalOceanProvider
from providers.mongodb_atlas import MongoDBAtlasProvider
from providers.neon import NeonProvider
from providers.openai import OpenAIProvider
from providers.openrouter import OpenRouterProvider
from providers.planetscale import PlanetScaleProvider
from providers.turso import TursoProvider
from providers.twilio import TwilioProvider
from providers.upstash import UpstashProvider
from providers.vercel import VercelProvider

# Load environment variables
load_dotenv()

# Initialize MCP server
mcp = FastMCP("burnmeter")

# Initialize providers (all 11 platforms)
PROVIDERS: dict[str, BaseProvider] = {
    "vercel": VercelProvider(),
    "openrouter": OpenRouterProvider(),
    "openai": OpenAIProvider(),
    "anthropic": AnthropicProvider(),
    "neon": NeonProvider(),
    "planetscale": PlanetScaleProvider(),
    "digitalocean": DigitalOceanProvider(),
    "turso": TursoProvider(),
    "upstash": UpstashProvider(),
    "mongodb_atlas": MongoDBAtlasProvider(),
    "twilio": TwilioProvider(),
}


def _parse_period(period: str) -> tuple[str, str]:
    """
    Convert period string to start_date and end_date.

    Args:
        period: One of "7d", "30d", "mtd", "current_cycle"

    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    today = datetime.now()
    end_date = today.strftime("%Y-%m-%d")

    if period == "7d":
        start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    elif period == "30d":
        start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    elif period == "mtd":
        # Month-to-date: first day of current month
        start_date = today.replace(day=1).strftime("%Y-%m-%d")
    elif period == "current_cycle":
        # Assume cycle starts on 1st of month
        start_date = today.replace(day=1).strftime("%Y-%m-%d")
    else:
        raise ValueError(f"Invalid period: {period}")

    return start_date, end_date


@mcp.tool()
async def get_total_costs(
    period: str = "7d", platforms: Optional[list[str]] = None
) -> dict:
    """
    Get total infrastructure costs across all configured platforms.

    Args:
        period: Time period - "7d", "30d", "mtd", or "current_cycle" (default: "7d")
        platforms: List of platforms to include (default: all configured)

    Returns:
        Dictionary with total costs and per-platform breakdown
    """
    start_date, end_date = _parse_period(period)

    # Determine which platforms to query
    if platforms is None:
        platforms = list(PROVIDERS.keys())

    results = []
    total = 0.0
    errors = []

    for platform_name in platforms:
        provider = PROVIDERS.get(platform_name)
        if not provider:
            errors.append(f"Unknown platform: {platform_name}")
            continue

        if not provider.validate_auth():
            errors.append(f"{platform_name}: Missing API credentials")
            continue

        try:
            # Check cache first
            cached = cache.get(platform_name, start_date, end_date)
            if cached:
                cost_data = cached
            else:
                # Fetch from API
                cost_data = await provider.get_costs(start_date, end_date)
                cache.set(platform_name, start_date, end_date, cost_data)

            results.append(cost_data.model_dump())
            total += cost_data.total_usd

        except Exception as e:
            errors.append(f"{platform_name}: {str(e)}")

    return {
        "total_usd": round(total, 2),
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "platforms": results,
        "errors": errors if errors else None,
    }


@mcp.tool()
async def get_platform_breakdown(platform: str, period: str = "30d") -> dict:
    """
    Get detailed cost breakdown for a single platform.

    Args:
        platform: Platform name (vercel, openrouter, openai, etc.)
        period: Time period - "7d", "30d", "mtd", or "current_cycle" (default: "30d")

    Returns:
        Detailed cost breakdown with service-level data
    """
    provider = PROVIDERS.get(platform)
    if not provider:
        return {"error": f"Unknown platform: {platform}"}

    if not provider.validate_auth():
        return {"error": f"Missing API credentials for {platform}"}

    start_date, end_date = _parse_period(period)

    try:
        # Check cache first
        cached = cache.get(platform, start_date, end_date)
        if cached:
            cost_data = cached
        else:
            cost_data = await provider.get_costs(start_date, end_date)
            cache.set(platform, start_date, end_date, cost_data)

        return cost_data.model_dump()

    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def check_budget(budget_usd: float, period: str = "mtd") -> dict:
    """
    Check if current spending exceeds the specified budget.

    Args:
        budget_usd: Monthly budget in USD
        period: Time period to check (default: "mtd" - month-to-date)

    Returns:
        Budget status with spending details
    """
    costs = await get_total_costs(period=period)
    total = costs.get("total_usd", 0)
    remaining = budget_usd - total
    percentage = (total / budget_usd * 100) if budget_usd > 0 else 0

    return {
        "budget_usd": budget_usd,
        "spent_usd": total,
        "remaining_usd": round(remaining, 2),
        "percentage_used": round(percentage, 1),
        "over_budget": total > budget_usd,
        "period": period,
        "platforms": costs.get("platforms", []),
    }


@mcp.tool()
def list_platforms() -> dict:
    """
    List all available platforms and their configuration status.

    Returns:
        Dictionary of platforms with auth status
    """
    platforms = {}
    for name, provider in PROVIDERS.items():
        platforms[name] = {
            "configured": provider.validate_auth(),
            "name": provider.name,
        }

    return {
        "platforms": platforms,
        "total_configured": sum(1 for p in platforms.values() if p["configured"]),
        "total_available": len(platforms),
    }


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
