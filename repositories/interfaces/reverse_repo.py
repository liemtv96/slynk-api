from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

class ReverseShareRepository(ABC):
    @abstractmethod
    def create_reverse(
        self,
        rid: str,
        owner_id: str,
        name: str,
        link: str,
        max_files: int,
        expires_at: Optional[datetime],
    ) -> Dict[str, Any]: ...

    @abstractmethod
    def list_reverse_for_user(self, owner_id: str) -> List[Dict[str, Any]]: ...

    @abstractmethod
    def increment_received_files(self, reverse_id: str, count: int = 1) -> None: ...

    @abstractmethod
    def get_by_id(self, reverse_id: str) -> Optional[Dict[str, Any]]: ...
