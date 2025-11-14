from abc import ABC, abstractmethod
from typing import Dict, Any

class ToolAdapter(ABC):
    @abstractmethod
    async def new_session(self, session_id: str, browser: str = 'chromium'):
        pass

    @abstractmethod
    async def goto(self, session_id: str, url: str):
        pass

    @abstractmethod
    async def click(self, session_id: str, selector: str):
        pass

    @abstractmethod
    async def type(self, session_id: str, selector: str, text: str):
        pass

    @abstractmethod
    async def screenshot(self, session_id: str, path: str):
        pass

    @abstractmethod
    async def get_dom_snapshot(self, session_id: str) -> str:
        pass

    @abstractmethod
    async def get_har(self, session_id: str) -> Dict[str, Any]:
        pass
