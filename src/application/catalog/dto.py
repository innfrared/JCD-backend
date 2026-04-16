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
    image: Optional[str]
    created_at: datetime


@dataclass
class SubcategoryResponse:
    """Subcategory response DTO."""
    id: int
    category_id: int
    name: str
    slug: str
    description: Optional[str]
    image: Optional[str]
    created_at: datetime
    slug_aliases: Optional[List[str]] = None


@dataclass
class CategoryWithSubcategoriesResponse:
    """Category response with subcategories."""
    id: int
    name: str
    slug: str
    image: Optional[str]
    created_at: datetime
    subcategories: List[SubcategoryResponse]


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
class VariantSwitchOption:
    """Variant switcher option DTO (product-level variants)."""
    id: int
    image: Optional[str]
    color_name: Optional[str]
    color_palette: Optional[str]
    is_current: bool


@dataclass
class ProductVariantDetailResponse:
    """Detailed product variant payload (detail endpoint only)."""
    id: int
    folder: Optional[str]
    color: Optional[str]
    material: Optional[str]
    cord_diameter: Optional[str]
    cord_type: Optional[str]
    description: Optional[str]
    care: Optional[str]
    handles: Optional[str]
    image_url: Optional[str]
    sort_order: int


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
    description: Optional[str]
    brand: Optional[str]
    price: str  # Decimal as string
    price_new: Optional[str]
    price_old: Optional[str]
    availability: str
    category_id: int
    subcategory_ids: List[int]
    category: Optional[CategoryResponse]
    subcategories: List[SubcategoryResponse]
    currency: str
    variant_group_id: Optional[int]
    variant_color_name: Optional[str]
    variant_color_palette: Optional[str]
    variant_image: Optional[str]
    variant_ids: List[int]
    variant_options: List[VariantSwitchOption]
    created_at: datetime
    updated_at: datetime
    variants: List[VariantProductPreview]  # Other products in same variant group
    variants_detailed: List[ProductVariantDetailResponse]  # Current product variants
    specifications: Dict[str, str]  # Simple record
    specifications_detailed: List[SpecificationDetail]  # Detailed list


@dataclass
class ProductCardResponse:
    """Product card response DTO for listing endpoint."""
    id: int
    name: str
    brand: Optional[str]
    price: str
    price_new: Optional[str]
    price_old: Optional[str]
    availability: str
    currency: str
    image_url: Optional[str]
    category_id: int
    subcategory_ids: List[int]
    created_at: datetime
    updated_at: datetime
    specifications: Optional[Dict[str, str]] = None
    specifications_detailed: Optional[List[SpecificationDetail]] = None


@dataclass
class ListProductsRequest:
    """List products request DTO."""
    category_id: Optional[int] = None
    subcategory_ids: Optional[List[int]] = None
    subcategory_slugs: Optional[List[str]] = None
    search: Optional[str] = None
    availability: Optional[str] = None
    spec_filters: Optional[Dict[str, str]] = None
    page: int = 1
    page_size: int = 20
    include_detailed_specs: bool = False

