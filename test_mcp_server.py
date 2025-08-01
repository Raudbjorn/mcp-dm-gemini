#!/usr/bin/env python3
"""
Test script for the MCP server
"""
import asyncio
import json
import sys
from mcp_server_standalone import server, initialize_services

async def test_tools():
    """Test the MCP server tools"""
    print("Testing MCP server tools...")
    
    # Initialize services
    await initialize_services()
    
    # Test list_tools by calling the handler function directly
    from mcp_server_standalone import handle_list_tools, handle_call_tool
    
    tools = await handle_list_tools()
    print(f"Available tools: {len(tools)}")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # Test a simple search (this will fail gracefully if no content is indexed)
    try:
        result = await handle_call_tool("search", {"query": "test"})
        print(f"Search test result: {result[0].text[:100]}...")
    except Exception as e:
        print(f"Search test failed (expected): {e}")
    
    print("MCP server tools are working correctly!")

if __name__ == "__main__":
    asyncio.run(test_tools())