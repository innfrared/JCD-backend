"""Authentication utilities."""
from typing import Optional
from dataclasses import dataclass


@dataclass
class TokenPair:
    """JWT token pair."""
    access: str
    refresh: str


@dataclass
class AuthenticatedUser:
    """Authenticated user info."""
    user_id: int
    email: str
    is_staff: bool

