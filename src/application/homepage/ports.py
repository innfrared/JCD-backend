"""Homepage repository ports (interfaces)."""
from abc import ABC, abstractmethod
from typing import List, Dict
from src.domain.homepage.entities import HomeSection, HomeSectionItem
from src.domain.catalog.entities import Product


class HomeSectionRepository(ABC):
    """Home section repository interface."""
    
    @abstractmethod
    def list_active_ordered(self) -> List[HomeSection]:
        """List all active sections ordered by sort_order."""
        pass
    
    @abstractmethod
    def get_section_items(
        self,
        section_ids: List[int]
    ) -> Dict[int, List[HomeSectionItem]]:
        """
        Get all section items for given sections.
        
        Returns:
            Dict mapping section_id to list of items ordered by sort_order
        """
        pass


class ProductCardRepository(ABC):
    """Product card repository interface (lightweight product info)."""
    
    @abstractmethod
    def get_product_cards(
        self,
        product_ids: List[int]
    ) -> List[Product]:
        """
        Get products by IDs in the same order as provided.
        
        Returns:
            List of Product entities (may be shorter if some IDs don't exist)
        """
        pass

