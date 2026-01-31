"""Homepage repository implementation."""
from typing import List, Dict
from django.db.models import Prefetch
from src.domain.homepage.entities import HomeSection, HomeSectionItem
from src.domain.catalog.entities import Product
from src.domain.shared.types import Currency, Availability
from src.application.homepage.ports import HomeSectionRepository, ProductCardRepository
from src.infrastructure.db.models.homepage import (
    HomeSection as HomeSectionModel,
    HomeSectionItem as HomeSectionItemModel
)
from src.infrastructure.db.models.catalog import Product as ProductModel


class DjangoHomeSectionRepository(HomeSectionRepository):
    """Django home section repository implementation."""
    
    def list_active_ordered(self) -> List[HomeSection]:
        """List all active sections ordered by sort_order."""
        section_models = HomeSectionModel.objects.filter(
            is_active=True
        ).order_by('sort_order', 'id')
        
        return [self._to_domain(section) for section in section_models]
    
    def get_section_items(
        self,
        section_ids: List[int]
    ) -> Dict[int, List[HomeSectionItem]]:
        """Get all section items for given sections."""
        if not section_ids:
            return {}
        
        items = HomeSectionItemModel.objects.filter(
            section_id__in=section_ids
        ).order_by('section_id', 'sort_order', 'id')
        
        # Group by section_id
        result = {}
        for item in items:
            section_id = item.section_id
            if section_id not in result:
                result[section_id] = []
            result[section_id].append(self._to_domain_item(item))
        
        return result
    
    def _to_domain(self, section_model: HomeSectionModel) -> HomeSection:
        """Convert Django model to domain entity."""
        return HomeSection(
            id=section_model.id,
            key=section_model.key,
            title=section_model.title,
            description=section_model.description,
            main_image=section_model.main_image,
            category_name=section_model.category_name,
            product_count=section_model.product_count,
            sort_order=section_model.sort_order,
            is_active=section_model.is_active,
            created_at=section_model.created_at,
            updated_at=section_model.updated_at
        )
    
    def _to_domain_item(self, item_model: HomeSectionItemModel) -> HomeSectionItem:
        """Convert Django model to domain entity."""
        return HomeSectionItem(
            id=item_model.id,
            section_id=item_model.section_id,
            product_id=item_model.product_id,
            sort_order=item_model.sort_order
        )


class DjangoProductCardRepository(ProductCardRepository):
    """Django product card repository implementation."""
    
    def get_product_cards(
        self,
        product_ids: List[int]
    ) -> List[Product]:
        """Get products by IDs in the same order as provided."""
        if not product_ids:
            return []
        
        # Fetch products
        product_models = ProductModel.objects.filter(
            id__in=product_ids
        ).select_related('category').prefetch_related('subcategories')
        
        # Fetch first variant image URLs for each product
        from src.infrastructure.db.models.catalog import ProductVariant as ProductVariantModel
        
        # Get first variant (by sort_order) with image for each product
        # Fetch all variants with images, then pick first per product
        all_variants = ProductVariantModel.objects.filter(
            product_id__in=product_ids,
            image_url__isnull=False
        ).order_by('product_id', 'sort_order', 'id')
        
        # Create image URL map (first variant per product)
        image_urls = {}
        seen_products = set()
        for variant in all_variants:
            if variant.product_id not in seen_products:
                image_urls[variant.product_id] = variant.image_url
                seen_products.add(variant.product_id)
        
        # Create lookup map
        product_map = {p.id: p for p in product_models}
        
        # Return in the same order as product_ids, filtering out missing ones
        products = []
        for pid in product_ids:
            if pid in product_map:
                product = self._to_domain(product_map[pid])
                # Attach image URL as a temporary attribute (not part of domain model)
                product._image_url = image_urls.get(pid)  # type: ignore
                products.append(product)
        
        return products
    
    def _to_domain(self, product_model: ProductModel) -> Product:
        """Convert Django model to domain entity."""
        return Product(
            id=product_model.id,
            name=product_model.name,
            brand=product_model.brand,
            price=product_model.price,
            price_new=product_model.price_new,
            price_old=product_model.price_old,
            availability=Availability(product_model.availability),
            category_id=product_model.category_id,
            subcategory_ids=list(
                product_model.subcategories.values_list('id', flat=True)
            ),
            currency=Currency(product_model.currency),
            created_at=product_model.created_at,
            updated_at=product_model.updated_at
        )

