"""Shared domain types."""
from typing import Optional
from decimal import Decimal
from enum import Enum


class Currency(str, Enum):
    """Currency enum."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


class Availability(str, Enum):
    """Product availability enum."""
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    PRE_ORDER = "pre_order"


class AttributeDataType(str, Enum):
    """Attribute data type enum."""
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    SINGLE_SELECT = "SINGLE_SELECT"
    MULTI_SELECT = "MULTI_SELECT"


class ScopeType(str, Enum):
    """Attribute scope type enum."""
    CATEGORY = "category"
    SUBCATEGORY = "subcategory"


class Money:
    """Money value object."""
    
    def __init__(self, amount: Decimal, currency: Currency):
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        self.amount = amount
        self.currency = currency
    
    def __eq__(self, other):
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount and self.currency == other.currency
    
    def __repr__(self):
        return f"Money({self.amount}, {self.currency.value})"

