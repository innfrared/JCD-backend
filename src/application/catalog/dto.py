"""Catalog DTOs."""
from dataclasses import dataclass
from typing import Optional, List, Dict
from decimal import Decimal
from datetime import datetime


@dataclass
class CategoryResponse:
    """Category response DTO."""
    id: int
    name: str
    slug: str
    created_at: datetime


@dataclass
class SubcategoryResponse:
    """Subcategory response DTO."""
    id: int
    category_id: int
    name: str
    slug: str
    created_at: datetime


@dataclass
class VariantProductPreview:
    """Variant product preview DTO."""
    id: int
    name: str
    price: str
    availability: str
    image: Optional[str]
    color_name: Optional[str]
    color_palette: Optional[str]


@dataclass
class SpecificationDetail:
    """Specification detail DTO."""
    key: str
    label: str
    type: str
    value: str  # Will be converted to appropriate type
    display: str
    unit: Optional[str]


@dataclass
class ProductResponse:
    """Product response DTO."""
    id: int
    name: str
    brand: Optional[str]
    price: str  # Decimal as string
    price_new: Optional[str]
    price_old: Optional[str]
    availability: str
    category_id: int
    subcategory_id: Optional[int]
    category: Optional[CategoryResponse]
    subcategory: Optional[SubcategoryResponse]
    currency: str
    variant_group_id: Optional[int]
    variant_color_name: Optional[str]
    variant_color_palette: Optional[str]
    variant_image: Optional[str]
    created_at: datetime
    updated_at: datetime
    variants: List[VariantProductPreview]  # Other products in same variant group
    specifications: Dict[str, str]  # Simple record
    specifications_detailed: List[SpecificationDetail]  # Detailed list


@dataclass
class ListProductsRequest:
    """List products request DTO."""
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    search: Optional[str] = None
    availability: Optional[str] = None
    spec_filters: Optional[Dict[str, str]] = None
    page: int = 1
    page_size: int = 20

