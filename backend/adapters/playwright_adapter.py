import asyncio, os
from playwright.async_api import async_playwright
from typing import Dict, Any
from .base import ToolAdapter

class PlaywrightAdapter(ToolAdapter):
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._pw = None
        self._lock = asyncio.Lock()

    async def _ensure_pw(self):
        async with self._lock:
            if self._pw is None:
                self._pw = await async_playwright().__aenter__()

    async def new_session(self, session_id: str, browser: str = 'chromium'):
        await self._ensure_pw()
        browser_obj = await getattr(self._pw, browser).launch(headless=True)
        context = await browser_obj.new_context()
        page = await context.new_page()
        self._sessions[session_id] = {
            'browser': browser_obj,
            'context': context,
            'page': page
        }
        return True

    async def _page(self, session_id: str):
        return self._sessions[session_id]['page']

    async def goto(self, session_id: str, url: str):
        page = await self._page(session_id)
        return await page.goto(url)

    async def click(self, session_id: str, selector: str):
        page = await self._page(session_id)
        await page.click(selector)
        return True

    async def type(self, session_id: str, selector: str, text: str):
        page = await self._page(session_id)
        await page.fill(selector, text)
        return True

    async def screenshot(self, session_id: str, path: str):
        page = await self._page(session_id)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        await page.screenshot(path=path, full_page=True)
        return path

    async def get_dom_snapshot(self, session_id: str) -> str:
        page = await self._page(session_id)
        return await page.content()

    async def get_har(self, session_id: str):
        return {}

    async def close_session(self, session_id: str):
        if session_id in self._sessions:
            await self._sessions[session_id]['context'].close()
            await self._sessions[session_id]['browser'].close()
            del self._sessions[session_id]
