from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any, Dict, Optional


class CognitiveTopology(ABC):
    @abstractmethod
    async def run(
        self,
        prompt: str,
        left: Any,
        right: Any,
        cc: Any,
        memory: Optional[Any] = None,
        ui_settings: Optional[Dict] = None
    ) -> AsyncGenerator[str, None]:
        yield ""
    
    @property
    @abstractmethod
    def name(self) -> str:
        return ""
    
    @property
    @abstractmethod
    def description(self) -> str:
        return ""
