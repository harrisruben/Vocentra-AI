from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class VoiceProvider(ABC):
    @abstractmethod
    async def get_calls(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_call(self, call_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_assistants(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_phone_numbers(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def start_call(
        self,
        assistant_id: str,
        phone_number_id: Optional[str],
        customer_number: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def end_call(self, call_id: str) -> bool:
        pass
