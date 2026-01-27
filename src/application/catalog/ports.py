"""Catalog repository ports (interfaces)."""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Tuple
from src.domain.catalog.entities import (
    Category, Subcategory, Product, VariantGroup, Attribute,
    AttributeOption, ProductAttributeValue
)


class CategoryRepository(ABC):
    """Category repository interface."""
    
    @abstractmethod
    def get_all(self) -> List[Category]:
        """Get all categories."""
        pass
    
    @abstractmethod
    def get_by_id(self, category_id: int) -> Optional[Category]:
        """Get category by ID."""
        pass
    
    @abstractmethod
    def get_subcategory_by_id(self, subcategory_id: int) -> Optional[Subcategory]:
        """Get subcategory by ID."""
        pass


class ProductRepository(ABC):
    """Product repository interface."""
    
    @abstractmethod
    def get_all(
        self,
        category_id: Optional[int] = None,
        subcategory_id: Optional[int] = None,
        search: Optional[str] = None,
        availability: Optional[str] = None,
        spec_filters: Optional[Dict[str, str]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Product], int]:
        """Get all products with filters and pagination."""
        pass
    
    @abstractmethod
    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        pass
    
    @abstractmethod
    def get_variant_group_products(
        self,
        variant_group_id: int,
        exclude_product_id: Optional[int] = None
    ) -> List[Product]:
        """Get all products in a variant group, excluding specified product."""
        pass
    
    @abstractmethod
    def get_specifications(
        self,
        product_id: int
    ) -> Tuple[Dict[str, str], List[Dict]]:
        """Get product specifications.
        
        Returns:
            Tuple of (simple_record, detailed_list)
        """
        pass


class AttributeRepository(ABC):
    """Attribute repository interface."""
    
    @abstractmethod
    def get_by_scope(
        self,
        scope_type: str,
        scope_id: int
    ) -> List[Attribute]:
        """Get attributes by scope."""
        pass
    
    @abstractmethod
    def get_options(self, attribute_id: int) -> List[AttributeOption]:
        """Get options for an attribute."""
        pass

