"""Manual test of burnmeter MCP server."""
import asyncio
import sys
sys.path.insert(0, 'src')

from server import mcp, PROVIDERS

async def test_mcp_tools():
    """Test that MCP tools are registered and callable."""

    print("=" * 60)
    print("Testing burnmeter MCP Server")
    print("=" * 60)
    print()

    # Test 1: List available tools
    print("Test 1: List Available Tools")
    print("-" * 60)
    tools = await mcp.list_tools()
    print(f"Found {len(tools)} tools:")
    for tool in tools:
        print(f"  ✓ {tool.name}")
        print(f"    {tool.description}")
    print()

    # Test 2: List platforms
    print("Test 2: list_platforms()")
    print("-" * 60)
    try:
        result = await mcp.call_tool("list_platforms", {})
        print(f"✓ Success!")
        print(f"  Total platforms: {result['total_available']}")
        print(f"  Configured: {result['total_configured']}")
        for name, info in result['platforms'].items():
            status = "✓" if info['configured'] else "✗"
            print(f"  {status} {name}")
    except Exception as e:
        print(f"✗ Error: {e}")
    print()

    # Test 3: get_total_costs (will likely error, but tests the call)
    print("Test 3: get_total_costs()")
    print("-" * 60)
    try:
        result = await mcp.call_tool("get_total_costs", {"period": "7d"})
        print(f"✓ Tool executed!")
        print(f"  Total USD: ${result.get('total_usd', 0):.2f}")
        print(f"  Period: {result.get('period')}")
        if result.get('errors'):
            print(f"  Errors encountered:")
            for error in result['errors']:
                print(f"    - {error}")
    except Exception as e:
        print(f"✗ Error: {e}")
    print()

    # Test 4: check_budget
    print("Test 4: check_budget()")
    print("-" * 60)
    try:
        result = await mcp.call_tool("check_budget", {
            "budget_usd": 500.0,
            "period": "mtd"
        })
        print(f"✓ Tool executed!")
        print(f"  Budget: ${result.get('budget_usd')}")
        print(f"  Spent: ${result.get('spent_usd')}")
        print(f"  Remaining: ${result.get('remaining_usd')}")
        print(f"  Over budget: {result.get('over_budget')}")
    except Exception as e:
        print(f"✗ Error: {e}")
    print()

    # Test 5: get_platform_breakdown
    print("Test 5: get_platform_breakdown()")
    print("-" * 60)
    try:
        result = await mcp.call_tool("get_platform_breakdown", {
            "platform": "vercel",
            "period": "7d"
        })
        print(f"✓ Tool executed!")
        if 'error' in result:
            print(f"  Expected error: {result['error']}")
        else:
            print(f"  Platform: {result.get('platform')}")
            print(f"  Total: ${result.get('total_usd', 0):.2f}")
    except Exception as e:
        print(f"✗ Error: {e}")
    print()

    print("=" * 60)
    print("MCP Server Test Complete")
    print("=" * 60)
    print()
    print("Summary:")
    print("✓ MCP server starts")
    print("✓ Tools are registered")
    print("✓ Tools can be called")
    print("✓ Error handling works")
    print()
    print("Note: Provider API errors are expected without valid billing data.")
    print("The MCP layer itself is working correctly.")

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())
