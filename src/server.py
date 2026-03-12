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
from providers.railway import RailwayProvider
from providers.turso import TursoProvider
from providers.twilio import TwilioProvider
from providers.upstash import UpstashProvider
from providers.vercel import VercelProvider

# Load environment variables
load_dotenv()

# Initialize MCP server
mcp = FastMCP("burnmeter")

# Initialize providers (12 platforms)
PROVIDERS: dict[str, BaseProvider] = {
    "vercel": VercelProvider(),
    "railway": RailwayProvider(),
    "digitalocean": DigitalOceanProvider(),
    "openrouter": OpenRouterProvider(),
    "openai": OpenAIProvider(),
    "anthropic": AnthropicProvider(),
    "neon": NeonProvider(),
    "planetscale": PlanetScaleProvider(),
    "turso": TursoProvider(),
    "mongodb_atlas": MongoDBAtlasProvider(),
    "upstash": UpstashProvider(),
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


@mcp.tool()
async def forecast_monthly_spend() -> dict:
    """
    Forecast total spending for the current month based on current usage rate.

    Calculates daily burn rate from month-to-date spending and projects
    to end of month. Includes confidence indicator based on days elapsed.

    Returns:
        Forecast with projected total, daily rate, and confidence level
    """
    # Get month-to-date costs
    costs = await get_total_costs(period="mtd")
    total_mtd = costs.get("total_usd", 0)

    # Calculate days elapsed and days in month
    today = datetime.now()
    days_elapsed = today.day
    days_in_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    days_in_month = days_in_month.day
    days_remaining = days_in_month - days_elapsed

    # Calculate daily burn rate and projected total
    daily_rate = total_mtd / days_elapsed if days_elapsed > 0 else 0
    projected_total = total_mtd + (daily_rate * days_remaining)

    # Calculate confidence (more days = higher confidence)
    # Low confidence: < 7 days, Medium: 7-14 days, High: 15+ days
    if days_elapsed < 7:
        confidence = "low"
    elif days_elapsed < 15:
        confidence = "medium"
    else:
        confidence = "high"

    # Calculate per-platform forecasts
    platform_forecasts = []
    for platform_data in costs.get("platforms", []):
        platform_mtd = platform_data.get("total_usd", 0)
        platform_daily = platform_mtd / days_elapsed if days_elapsed > 0 else 0
        platform_projected = platform_mtd + (platform_daily * days_remaining)

        platform_forecasts.append({
            "platform": platform_data.get("platform"),
            "current_mtd": round(platform_mtd, 2),
            "daily_rate": round(platform_daily, 2),
            "projected_total": round(platform_projected, 2),
        })

    return {
        "current_mtd": round(total_mtd, 2),
        "daily_burn_rate": round(daily_rate, 2),
        "projected_monthly_total": round(projected_total, 2),
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
        "days_in_month": days_in_month,
        "confidence": confidence,
        "platform_forecasts": platform_forecasts,
        "note": f"Forecast based on {days_elapsed} days of data. "
                f"Confidence level: {confidence}.",
    }


@mcp.tool()
async def compare_month_over_month() -> dict:
    """
    Compare current month spending to previous month.

    Shows total and per-platform changes with percentage deltas.
    Useful for identifying cost trends and anomalies.

    Returns:
        Comparison with current vs previous month costs and percent changes
    """
    today = datetime.now()

    # Get current month (MTD)
    current_month_costs = await get_total_costs(period="mtd")
    current_total = current_month_costs.get("total_usd", 0)

    # Get previous month (full month)
    # Calculate first and last day of previous month
    first_day_current = today.replace(day=1)
    last_day_previous = first_day_current - timedelta(days=1)
    first_day_previous = last_day_previous.replace(day=1)

    prev_start = first_day_previous.strftime("%Y-%m-%d")
    prev_end = last_day_previous.strftime("%Y-%m-%d")

    # Manually query previous month (not using _parse_period)
    results = []
    prev_total = 0.0
    errors = []

    for platform_name, provider in PROVIDERS.items():
        if not provider.validate_auth():
            continue

        try:
            # Check cache first
            cached = cache.get(platform_name, prev_start, prev_end)
            if cached:
                cost_data = cached
            else:
                cost_data = await provider.get_costs(prev_start, prev_end)
                cache.set(platform_name, prev_start, prev_end, cost_data)

            results.append(cost_data.model_dump())
            prev_total += cost_data.total_usd

        except Exception as e:
            errors.append(f"{platform_name}: {str(e)}")

    # Calculate overall change
    absolute_change = current_total - prev_total
    percent_change = (absolute_change / prev_total * 100) if prev_total > 0 else 0

    # Build per-platform comparison
    platform_comparisons = []
    current_platforms = {p["platform"]: p["total_usd"]
                        for p in current_month_costs.get("platforms", [])}
    prev_platforms = {p["platform"]: p["total_usd"] for p in results}

    all_platforms = set(current_platforms.keys()) | set(prev_platforms.keys())

    for platform in all_platforms:
        current = current_platforms.get(platform, 0)
        previous = prev_platforms.get(platform, 0)
        change = current - previous
        pct_change = (change / previous * 100) if previous > 0 else 0

        platform_comparisons.append({
            "platform": platform,
            "current_month": round(current, 2),
            "previous_month": round(previous, 2),
            "absolute_change": round(change, 2),
            "percent_change": round(pct_change, 1),
        })

    # Sort by absolute change (descending)
    platform_comparisons.sort(key=lambda x: abs(x["absolute_change"]), reverse=True)

    return {
        "current_month": {
            "total": round(current_total, 2),
            "period": current_month_costs.get("period"),
            "start_date": current_month_costs.get("start_date"),
            "end_date": current_month_costs.get("end_date"),
        },
        "previous_month": {
            "total": round(prev_total, 2),
            "start_date": prev_start,
            "end_date": prev_end,
        },
        "comparison": {
            "absolute_change": round(absolute_change, 2),
            "percent_change": round(percent_change, 1),
            "trend": "increasing" if absolute_change > 0 else "decreasing" if absolute_change < 0 else "stable",
        },
        "platform_comparisons": platform_comparisons,
        "errors": errors if errors else None,
    }


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
