# tools.py

import asyncio
from typing import Optional
from langchain.tools import tool
from mcp_client import MCPClient, run_sync

# 全局 MCP 客户端实例（简单起见）
# 注意：你启动 MCP server 的地址／端口需要在这里填写
MCP_WS_URL = "ws://localhost:9222"  # 根据实际情况修改
mcp_client = MCPClient(MCP_WS_URL)
run_sync(mcp_client.connect())

@tool
def navigate(url: str) -> str:
    """Navigate browser to the given URL."""
    try:
        result = run_sync(mcp_client.goto(url))
        return f"Navigated to {url}"
    except Exception as e:
        return f"ERROR navigating to {url}: {e}"

@tool
def click_selector(selector: str) -> str:
    """Click the DOM element matching the CSS selector."""
    try:
        result = run_sync(mcp_client.click(selector))
        return f"Clicked selector {selector}"
    except Exception as e:
        return f"ERROR clicking selector {selector}: {e}"

@tool
def type_text(selector: str, text: str) -> str:
    """Type the given text into the element matching the selector."""
    try:
        result = run_sync(mcp_client.type(selector, text))
        return f"Typed text into {selector}"
    except Exception as e:
        return f"ERROR typing into {selector}: {e}"

@tool
def wait_for(selector: str, timeout_ms: int = 30000) -> str:
    """Wait for the given selector to appear on the page within timeout (milliseconds)."""
    try:
        result = run_sync(mcp_client.wait_for_selector(selector, timeout_ms))
        return f"Selector {selector} appeared"
    except Exception as e:
        return f"ERROR waiting for selector {selector}: {e}"

@tool
def assert_text(selector: str, expected: str, timeout_ms: int = 30000) -> str:
    """Assert that the element matching selector contains the expected text."""
    try:
        ok = run_sync(mcp_client.assert_element_text(selector, expected, timeout_ms))
        if ok:
            return f"Assertion passed: selector {selector} contains text '{expected}'"
        else:
            return f"Assertion failed: selector {selector} does NOT contain text '{expected}'"
    except Exception as e:
        return f"ERROR asserting text for {selector}: {e}"
