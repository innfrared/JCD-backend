"""Homepage use cases."""
from typing import List
from src.domain.homepage.entities import HomeSection, HomeSectionItem
from src.domain.homepage.rules import get_items_to_render, filter_unavailable_products
from src.application.homepage.ports import HomeSectionRepository, ProductCardRepository
from src.application.homepage.dto import (
    HomePageResponse, HomeCarouselSection, ProductCard
)
from src.domain.catalog.entities import Product


class GetHomePageSectionsUseCase:
    """Get homepage sections use case."""
    
    def __init__(
        self,
        home_section_repo: HomeSectionRepository,
        product_card_repo: ProductCardRepository
    ):
        self.home_section_repo = home_section_repo
        self.product_card_repo = product_card_repo
    
    def execute(self) -> HomePageResponse:
        """Execute get homepage sections."""
        # Load active sections ordered by sort_order
        sections = self.home_section_repo.list_active_ordered()
        
        if not sections:
            return HomePageResponse(sections=[])
        
        section_ids = [section.id for section in sections]
        
        # Fetch all section items in one query
        section_items_map = self.home_section_repo.get_section_items(section_ids)
        
        # Collect all product IDs in order
        all_product_ids = []
        section_product_ids_map = {}
        
        for section in sections:
            items = section_items_map.get(section.id, [])
            # Sort items by sort_order
            sorted_items = sorted(items, key=lambda x: x.sort_order)
            product_ids = [item.product_id for item in sorted_items]
            section_product_ids_map[section.id] = product_ids
            all_product_ids.extend(product_ids)
        
        # Fetch all products in one query
        products = self.product_card_repo.get_product_cards(all_product_ids)
        
        # Create product lookup map
        product_map = {product.id: product for product in products}
        
        # Build response sections
        response_sections = []
        
        for section in sections:
            product_ids = section_product_ids_map.get(section.id, [])
            
            # Get products in order, preserving curated order
            section_products = [
                product_map[pid] for pid in product_ids
                if pid in product_map
            ]
            
            # Apply domain rule: filter unavailable (we keep them but mark as out of stock)
            available_products = filter_unavailable_products(
                section_products,
                include_unavailable=True
            )
            
            # Apply domain rule: limit by product_count
            products_to_render = get_items_to_render(
                section.product_count,
                available_products
            )
            
            # Convert to ProductCard DTOs
            product_cards = [
                self._to_product_card(product)
                for product in products_to_render
            ]
            
            response_sections.append(HomeCarouselSection(
                id=section.id,
                key=section.key,
                title=section.title,
                description=section.description,
                main_image=section.main_image,
                category_name=section.category_name,
                product_count=section.product_count,
                sort_order=section.sort_order,
                is_active=section.is_active,
                items=product_cards
            ))
        
        return HomePageResponse(sections=response_sections)
    
    def _to_product_card(self, product: Product) -> ProductCard:
        """Convert Product entity to ProductCard DTO."""
        # Get image URL from repository (attached as temporary attribute)
        image_url = getattr(product, '_image_url', None)
        
        return ProductCard(
            id=product.id,
            name=product.name,
            brand=product.brand,
            price=str(product.price),
            price_new=str(product.price_new) if product.price_new else None,
            price_old=str(product.price_old) if product.price_old else None,
            availability=product.availability.value,
            currency=product.currency.value,
            image_url=image_url,
            category_id=product.category_id,
            subcategory_ids=product.subcategory_ids
        )

