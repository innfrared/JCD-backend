"""User DTOs."""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class RegisterRequest:
    """Register request DTO."""
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


@dataclass
class LoginRequest:
    """Login request DTO."""
    email: str
    password: str


@dataclass
class UserResponse:
    """User response DTO."""
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    is_active: bool
    created_at: datetime


@dataclass
class UpdateProfileRequest:
    """Update profile request DTO."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


@dataclass
class AddressRequest:
    """Address request DTO."""
    label: str
    full_name: str
    phone: str
    country: str
    city: str
    street: str
    postal_code: str
    apartment: Optional[str] = None
    is_default: bool = False


@dataclass
class AddressResponse:
    """Address response DTO."""
    id: int
    label: str
    full_name: str
    phone: str
    country: str
    city: str
    street: str
    apartment: Optional[str]
    postal_code: str
    is_default: bool
    created_at: datetime

