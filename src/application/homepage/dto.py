"""Homepage DTOs."""
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ProductCard:
    """Product card DTO (lightweight product info for carousel)."""
    id: int
    name: str
    brand: Optional[str]
    price: str  # Decimal as string
    price_new: Optional[str]
    price_old: Optional[str]
    availability: str
    currency: str
    image_url: Optional[str]  # Primary image from first variant or product
    category_id: int
    subcategory_ids: List[int]


@dataclass
class HomeCarouselSection:
    """Home carousel section DTO."""
    id: int
    key: str
    title: str
    description: Optional[str]
    main_image: Optional[str]
    category_name: Optional[str]
    product_count: int
    sort_order: int
    is_active: bool
    items: List[ProductCard]


@dataclass
class HomePageResponse:
    """Homepage response DTO."""
    sections: List[HomeCarouselSection]

