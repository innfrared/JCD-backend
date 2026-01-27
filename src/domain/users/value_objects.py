"""User value objects."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Email:
    """Email value object."""
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Email cannot be empty")
        if '@' not in self.value:
            raise ValueError("Invalid email format")


@dataclass(frozen=True)
class PhoneNumber:
    """Phone number value object."""
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Phone number cannot be empty")

