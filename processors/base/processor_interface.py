from abc import ABC, abstractmethod
from typing import Any

class ProcessorInterface(ABC):
    @abstractmethod
    async def process(self, payload: dict) -> Any:
        pass