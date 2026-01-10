from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAgent(ABC):
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """
        Execute the agent's main logic.
        """
        pass
