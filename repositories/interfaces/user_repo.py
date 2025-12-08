from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class UserRepository(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    def create_user(self, user_id: str, email: str, username: str, password_hash: str) -> Dict[str, Any]: ...

    @abstractmethod
    def delete_user(self, user_id: str) -> None: ...

    @abstractmethod
    def get_settings(self, user_id: str) -> Dict[str, Any]: ...

    @abstractmethod
    def update_settings(self, user_id: str, changes: Dict[str, Any]) -> Dict[str, Any]: ...
