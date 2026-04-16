"""Catalog repository ports (interfaces)."""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Tuple
from src.domain.catalog.entities import Category, Subcategory, Product, ProductVariant


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
    def get_by_ids(self, category_ids: List[int]) -> Dict[int, Category]:
        """Get categories indexed by ID."""
        pass
    
    @abstractmethod
    def get_subcategory_by_id(self, subcategory_id: int) -> Optional[Subcategory]:
        """Get subcategory by ID."""
        pass

    @abstractmethod
    def get_subcategories_by_category(self, category_id: int) -> List[Subcategory]:
        """Get subcategories by category ID."""
        pass

    @abstractmethod
    def get_subcategories_by_ids(
        self, subcategory_ids: List[int]
    ) -> Dict[int, Subcategory]:
        """Get subcategories indexed by ID."""
        pass

    @abstractmethod
    def get_subcategories_by_category_ids(
        self, category_ids: List[int]
    ) -> Dict[int, List[Subcategory]]:
        """Get subcategories grouped by category ID."""
        pass

    @abstractmethod
    def get_subcategories_by_slugs(
        self,
        slugs: List[str],
        category_id: Optional[int] = None,
    ) -> List[Subcategory]:
        """Get subcategories matching slugs, optionally scoped by category."""
        pass


class ProductRepository(ABC):
    """Product repository interface."""
    
    @abstractmethod
    def get_all(
        self,
        category_id: Optional[int] = None,
        subcategory_ids: Optional[List[int]] = None,
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
    def get_product_variants(self, product_id: int) -> List[ProductVariant]:
        """Get all variants for a specific product."""
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

    @abstractmethod
    def get_specifications_batch(
        self,
        product_ids: List[int],
        include_detailed: bool = False,
    ) -> Dict[int, Tuple[Dict[str, str], List[Dict]]]:
        """Get product specifications in batch indexed by product ID."""
        pass

