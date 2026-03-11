"""Test script for burnmeter providers."""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, 'src')

from providers.vercel import VercelProvider
from providers.anthropic import AnthropicProvider

async def test_providers():
    # Load environment
    load_dotenv()

    # Date range: last 7 days
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    print(f"Testing date range: {start_date} to {end_date}\n")

    # Test Vercel
    print("=" * 50)
    print("Testing Vercel Provider")
    print("=" * 50)
    vercel = VercelProvider()
    if vercel.validate_auth():
        print("✓ Vercel auth valid")
        try:
            result = await vercel.get_costs(start_date, end_date)
            print(f"✓ Success! Total: ${result.total_usd:.2f}")
            print(f"  Period: {result.period}")
            print(f"  Breakdown:")
            for item in result.breakdown[:5]:  # Show first 5
                print(f"    - {item.service}: ${item.cost:.2f}")
        except Exception as e:
            print(f"✗ Error: {e}")
    else:
        print("✗ Vercel token missing or invalid")

    print()

    # Test Anthropic
    print("=" * 50)
    print("Testing Anthropic Provider")
    print("=" * 50)
    anthropic = AnthropicProvider()
    if anthropic.validate_auth():
        key = os.getenv('ANTHROPIC_API_KEY', '')
        print(f"✓ Anthropic auth valid")
        print(f"  Key type: {'Admin' if key.startswith('sk-ant-admin-') else 'Regular'}")
        try:
            result = await anthropic.get_costs(start_date, end_date)
            print(f"✓ Success! Total: ${result.total_usd:.2f}")
            print(f"  Period: {result.period}")
            print(f"  Breakdown:")
            for item in result.breakdown[:5]:
                print(f"    - {item.service}: ${item.cost:.2f}")
        except Exception as e:
            print(f"✗ Error: {type(e).__name__}: {e}")
            if not key.startswith('sk-ant-admin-'):
                print("\n  ⚠️  Regular API keys don't support cost reporting.")
                print("  Need Admin API key (sk-ant-admin-...) from Organization account.")
    else:
        print("✗ Anthropic API key missing")

if __name__ == "__main__":
    asyncio.run(test_providers())
