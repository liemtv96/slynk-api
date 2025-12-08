from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class FileRepository(ABC):
    @abstractmethod
    def create_file(
        self,
        file_id: str,
        owner_id: str,
        filename: str,
        content_type: Optional[str],
        size: int,
        storage_engine: str,
        storage_key: str,
        share_id: Optional[str] = None,
        reverse_share_id: Optional[str] = None,
    ) -> Dict[str, Any]: ...

    @abstractmethod
    def get_by_id(self, file_id: str) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    def list_files_for_share(self, share_id: str) -> List[Dict[str, Any]]: ...
