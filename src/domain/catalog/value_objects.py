"""Catalog value objects."""
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from src.domain.shared.types import Currency


@dataclass(frozen=True)
class Slug:
    """Slug value object."""
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Slug cannot be empty")
        # Basic slug validation
        if not all(c.isalnum() or c in '-_' for c in self.value):
            raise ValueError("Invalid slug format")


@dataclass(frozen=True)
class Price:
    """Price value object."""
    amount: Decimal
    currency: Currency
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Price cannot be negative")

