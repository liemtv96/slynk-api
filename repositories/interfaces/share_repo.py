from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

class ShareRepository(ABC):
    @abstractmethod
    def create_share(
        self,
        share_id: str,
        owner_id: str,
        link: str,
        file_ids: List[str],
        expires_at: Optional[datetime],
    ) -> Dict[str, Any]: ...

    @abstractmethod
    def list_shares_for_user(self, owner_id: str) -> List[Dict[str, Any]]: ...

    @abstractmethod
    def delete_share(self, share_id: str, owner_id: str) -> bool: ...

    @abstractmethod
    def get_by_id(self, share_id: str) -> Optional[Dict[str, Any]]: ...
