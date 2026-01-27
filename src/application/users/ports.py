"""User repository ports (interfaces)."""
from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.users.entities import User, Address


class UserRepository(ABC):
    """User repository interface."""
    
    @abstractmethod
    def create(self, user: User) -> User:
        """Create a new user."""
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass
    
    @abstractmethod
    def update(self, user: User) -> User:
        """Update user."""
        pass


class AddressRepository(ABC):
    """Address repository interface."""
    
    @abstractmethod
    def create(self, address: Address) -> Address:
        """Create a new address."""
        pass
    
    @abstractmethod
    def get_by_id(self, address_id: int) -> Optional[Address]:
        """Get address by ID."""
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: int) -> List[Address]:
        """Get all addresses for a user."""
        pass
    
    @abstractmethod
    def update(self, address: Address) -> Address:
        """Update address."""
        pass
    
    @abstractmethod
    def delete(self, address_id: int) -> None:
        """Delete address."""
        pass
    
    @abstractmethod
    def set_default(self, user_id: int, address_id: int) -> None:
        """Set default address for user."""
        pass

