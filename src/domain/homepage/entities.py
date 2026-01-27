"""Homepage domain entities."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from src.domain.shared.exceptions import ValidationError


@dataclass
class HomeSection:
    """Home section entity."""
    id: Optional[int]
    key: str
    title: str
    description: Optional[str]
    main_image: Optional[str]
    category_name: Optional[str]
    product_count: int
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self):
        if not self.key:
            raise ValidationError("Section key is required")
        if not self.title:
            raise ValidationError("Section title is required")
        if self.product_count < 0:
            raise ValidationError("Product count cannot be negative")
        if self.sort_order < 0:
            raise ValidationError("Sort order cannot be negative")


@dataclass
class HomeSectionItem:
    """Home section item entity (curated product reference)."""
    id: Optional[int]
    section_id: int
    product_id: int
    sort_order: int
    
    def __post_init__(self):
        if self.sort_order < 0:
            raise ValidationError("Sort order cannot be negative")

