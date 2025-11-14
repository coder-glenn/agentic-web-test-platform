# mcp_client.py

import asyncio
import websockets
import json
import uuid
import logging
from typing import Any, Optional, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPClient:
    def __init__(self, websocket_url: str):
        """
        初始化 MCP 客户端，连接到 Playwright MCP 服务器。
        websocket_url: WebSocket URL，例如 "ws://localhost:XXXXX"
        """
        self.websocket_url = websocket_url
        self._ws: Optional[websockets.WebSocketClientProtocol] = None

    async def connect(self):
        logger.info(f"Connecting to MCP server at {self.websocket_url}")
        self._ws = await websockets.connect(self.websocket_url)
        logger.info("Connected to MCP server")

    async def close(self):
        if self._ws:
            await self._ws.close()
            logger.info("WebSocket connection closed")

    async def _send(self, method: str, params: Dict[str, Any]) -> Any:
        if not self._ws:
            raise RuntimeError("WebSocket connection is not established")
        req_id = str(uuid.uuid4())
        payload = {
            "id": req_id,
            "method": method,
            "params": params
        }
        await self._ws.send(json.dumps(payload))
        logger.debug(f"Sent: {payload}")
        # wait for response
        while True:
            message = await self._ws.recv()
            resp = json.loads(message)
            logger.debug(f"Received: {resp}")
            if resp.get("id") == req_id:
                if "error" in resp:
                    raise RuntimeError(f"MCP error: {resp['error']}")
                return resp.get("result")

    # 常用操作封装
    async def goto(self, url: str) -> Any:
        return await self._send("browser_navigate", {"url": url})

    async def click(self, selector: str) -> Any:
        return await self._send("browser_click", {"selector": selector})

    async def type(self, selector: str, text: str) -> Any:
        return await self._send("browser_type", {"selector": selector, "text": text})

    async def wait_for_selector(self, selector: str, timeout_ms: int = 30000) -> Any:
        return await self._send("browser_wait_for", {"selector": selector, "timeout": timeout_ms})

    async def assert_element_text(self, selector: str, expected_text: str, timeout_ms: int = 30000) -> bool:
        # 简单实现：等待 selector 出现，然后获取其 textContent 并比对
        await self.wait_for_selector(selector, timeout_ms)
        result = await self._send("browser_evaluate", {
            "script": f"document.querySelector({json.dumps(selector)}).textContent"
        })
        actual = result.get("value") if isinstance(result, dict) else result
        return actual and expected_text in actual

    # 工具：截图
    async def screenshot(self, path: str) -> Any:
        return await self._send("browser_take_screenshot", {"path": path})

# 简单同步包装
def run_sync(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

if __name__ == "__main__":
    # 测试脚本
    client = MCPClient("ws://localhost:9222")  # 根据你 MCP 服务实际端口修改
    try:
        run_sync(client.connect())
        run_sync(client.goto("https://www.nvidia.cn/"))
        run_sync(client.wait_for_selector("body", 10000))
        logger.info("Loaded NVIDIA.cn")
    finally:
        run_sync(client.close())
