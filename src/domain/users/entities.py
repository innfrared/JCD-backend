"""User domain entities."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from src.domain.shared.exceptions import ValidationError


@dataclass
class User:
    """User entity."""
    id: Optional[int]
    email: str
    password_hash: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    is_active: bool
    is_staff: bool
    created_at: datetime
    
    def __post_init__(self):
        if not self.email:
            raise ValidationError("Email is required")
        if '@' not in self.email:
            raise ValidationError("Invalid email format")
        if not self.password_hash:
            raise ValidationError("Password hash is required")


@dataclass
class Address:
    """Address entity."""
    id: Optional[int]
    user_id: int
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
    
    def __post_init__(self):
        if not self.label:
            raise ValidationError("Label is required")
        if not self.full_name:
            raise ValidationError("Full name is required")
        if not self.country:
            raise ValidationError("Country is required")
        if not self.city:
            raise ValidationError("City is required")
        if not self.street:
            raise ValidationError("Street is required")
        if not self.postal_code:
            raise ValidationError("Postal code is required")

