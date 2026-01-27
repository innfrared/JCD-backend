"""Catalog domain entities."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from src.domain.shared.types import Currency, Availability, AttributeDataType, ScopeType
from src.domain.shared.exceptions import ValidationError


@dataclass
class Category:
    """Category entity."""
    id: Optional[int]
    name: str
    slug: str
    created_at: datetime
    
    def __post_init__(self):
        if not self.name:
            raise ValidationError("Category name is required")
        if not self.slug:
            raise ValidationError("Category slug is required")


@dataclass
class Subcategory:
    """Subcategory entity."""
    id: Optional[int]
    category_id: int
    name: str
    slug: str
    created_at: datetime
    
    def __post_init__(self):
        if not self.name:
            raise ValidationError("Subcategory name is required")
        if not self.slug:
            raise ValidationError("Subcategory slug is required")


@dataclass
class VariantGroup:
    """Variant group entity (groups products that are variants of each other)."""
    id: Optional[int]
    name: Optional[str]
    slug: Optional[str]
    default_product_id: Optional[int]
    created_at: datetime
    
    def __post_init__(self):
        # All fields are optional, no validation needed
        pass


@dataclass
class Product:
    """Product entity."""
    id: Optional[int]
    name: str
    brand: Optional[str]
    price: Decimal
    price_new: Optional[Decimal]
    price_old: Optional[Decimal]
    availability: Availability
    category_id: int
    subcategory_id: Optional[int]
    currency: Currency
    variant_group_id: Optional[int]
    variant_color_name: Optional[str]
    variant_color_palette: Optional[str]
    variant_image: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self):
        if not self.name:
            raise ValidationError("Product name is required")
        if self.price < 0:
            raise ValidationError("Price cannot be negative")
        if self.price_new and self.price_new < 0:
            raise ValidationError("Price new cannot be negative")
        if self.price_old and self.price_old < 0:
            raise ValidationError("Price old cannot be negative")


@dataclass
class ProductVariant:
    """Product variant entity."""
    id: Optional[int]
    product_id: int
    name: str
    value: str
    image_url: Optional[str]
    color_palette: Optional[str]
    sort_order: int
    sizes: List[str]
    
    def __post_init__(self):
        if not self.name:
            raise ValidationError("Variant name is required")
        if not self.value:
            raise ValidationError("Variant value is required")
        if self.sort_order < 0:
            raise ValidationError("Sort order cannot be negative")


@dataclass
class Attribute:
    """Attribute definition entity."""
    id: Optional[int]
    scope_type: ScopeType
    scope_id: int
    key: str
    label: str
    data_type: AttributeDataType
    unit: Optional[str]
    is_filterable: bool
    is_required: bool
    sort_order: int
    
    def __post_init__(self):
        if not self.key:
            raise ValidationError("Attribute key is required")
        if not self.label:
            raise ValidationError("Attribute label is required")
        if self.sort_order < 0:
            raise ValidationError("Sort order cannot be negative")


@dataclass
class AttributeOption:
    """Attribute option entity."""
    id: Optional[int]
    attribute_id: int
    value: str
    label: str
    sort_order: int
    
    def __post_init__(self):
        if not self.value:
            raise ValidationError("Option value is required")
        if not self.label:
            raise ValidationError("Option label is required")
        if self.sort_order < 0:
            raise ValidationError("Sort order cannot be negative")


@dataclass
class ProductAttributeValue:
    """Product attribute value entity."""
    id: Optional[int]
    product_id: int
    attribute_id: int
    value_text: Optional[str]
    value_number: Optional[Decimal]
    value_bool: Optional[bool]
    option_ids: List[int]  # For SINGLE_SELECT and MULTI_SELECT
    
    def __post_init__(self):
        # At least one value must be set
        if not any([self.value_text, self.value_number is not None, self.value_bool is not None, self.option_ids]):
            raise ValidationError("At least one value must be provided")

