from abc import ABC, abstractmethod

class BaseProvider(ABC):

    @abstractmethod
    async def ask(self, message: str) -> str:
        pass
