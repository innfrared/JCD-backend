"""Catalog repository implementation."""
from typing import Optional, List, Dict, Tuple

from src.domain.catalog.entities import Category, Subcategory
from src.application.catalog.ports import CategoryRepository, ProductRepository
from src.application.catalog.dto import SpecificationDetail

from src.infrastructure.db.models.catalog import (
    Category as CategoryModel,
    Subcategory as SubcategoryModel,
    Attribute as AttributeModel,
    ProductAttributeValue as ProductAttributeValueModel,
)


class DjangoCategoryRepository(CategoryRepository):
    """Django category repository implementation."""

    LEGACY_SLUG_MARKER = '-old-'

    def _exclude_legacy_taxonomy(self, queryset):
        """Hide migrated legacy taxonomy rows from public category endpoints."""
        return queryset.exclude(slug__contains=self.LEGACY_SLUG_MARKER)
    
    def get_all(self) -> List[Category]:
        """Get all categories."""
        category_models = self._exclude_legacy_taxonomy(
            CategoryModel.objects.all()
        )
        return [self._to_domain(cat) for cat in category_models]
    
    def get_by_id(self, category_id: int) -> Optional[Category]:
        """Get category by ID."""
        category_model = self._exclude_legacy_taxonomy(
            CategoryModel.objects.filter(id=category_id)
        ).first()
        if not category_model:
            return None
        return self._to_domain(category_model)

    def get_by_ids(self, category_ids: List[int]) -> Dict[int, Category]:
        """Get categories indexed by ID."""
        if not category_ids:
            return {}
        category_models = self._exclude_legacy_taxonomy(
            CategoryModel.objects.filter(id__in=category_ids)
        )
        return {cat.id: self._to_domain(cat) for cat in category_models}
    
    def get_subcategory_by_id(self, subcategory_id: int) -> Optional[Subcategory]:
        """Get subcategory by ID."""
        subcategory_model = self._exclude_legacy_taxonomy(
            SubcategoryModel.objects.filter(id=subcategory_id)
        ).select_related('category').first()
        if not subcategory_model:
            return None
        return self._to_domain_subcategory(subcategory_model)

    def get_subcategories_by_category(self, category_id: int) -> List[Subcategory]:
        """Get subcategories for a category."""
        subcategory_models = self._exclude_legacy_taxonomy(
            SubcategoryModel.objects.filter(category_id=category_id)
        ).order_by('name')
        return [self._to_domain_subcategory(sub) for sub in subcategory_models]

    def get_subcategories_by_ids(
        self,
        subcategory_ids: List[int],
    ) -> Dict[int, Subcategory]:
        """Get subcategories indexed by ID."""
        if not subcategory_ids:
            return {}
        subcategory_models = self._exclude_legacy_taxonomy(
            SubcategoryModel.objects.filter(id__in=subcategory_ids)
        ).select_related('category')
        return {sub.id: self._to_domain_subcategory(sub) for sub in subcategory_models}

    def get_subcategories_by_category_ids(
        self,
        category_ids: List[int],
    ) -> Dict[int, List[Subcategory]]:
        """Get subcategories grouped by category ID."""
        if not category_ids:
            return {}
        grouped: Dict[int, List[Subcategory]] = {category_id: [] for category_id in category_ids}
        subcategory_models = self._exclude_legacy_taxonomy(
            SubcategoryModel.objects.filter(category_id__in=category_ids)
        ).select_related('category').order_by('category_id', 'name')
        for sub in subcategory_models:
            grouped.setdefault(sub.category_id, []).append(
                self._to_domain_subcategory(sub)
            )
        return grouped

    def get_subcategories_by_slugs(
        self,
        slugs: List[str],
        category_id: Optional[int] = None,
    ) -> List[Subcategory]:
        """Get subcategories matching slugs, optionally by category."""
        if not slugs:
            return []
        queryset = SubcategoryModel.objects.filter(slug__in=slugs)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        queryset = self._exclude_legacy_taxonomy(queryset).select_related('category')
        return [self._to_domain_subcategory(sub) for sub in queryset]
    
    def _to_domain_subcategory(self, subcategory_model: SubcategoryModel) -> Subcategory:
        """Convert Django model to domain entity."""
        return Subcategory(
            id=subcategory_model.id,
            category_id=subcategory_model.category_id,
            name=subcategory_model.name,
            slug=subcategory_model.slug,
            description=subcategory_model.description,
            image=subcategory_model.image,
            created_at=subcategory_model.created_at
        )
    
    def _to_domain(self, category_model: CategoryModel) -> Category:
        """Convert Django model to domain entity."""
        return Category(
            id=category_model.id,
            name=category_model.name,
            slug=category_model.slug,
            image=category_model.image,
            created_at=category_model.created_at
        )


class DjangoProductRepository(ProductRepository):
    """Specifications persistence; product list/detail reads use catalog_hot_reads."""

    def get_specifications_batch(
        self,
        product_ids: List[int],
        include_detailed: bool = False,
    ) -> Dict[int, Tuple[Dict[str, str], List[SpecificationDetail]]]:
        """Get product specifications in batch indexed by product ID."""
        if not product_ids:
            return {}

        attr_values = ProductAttributeValueModel.objects.filter(
            product_id__in=product_ids
        ).select_related('attribute').prefetch_related(
            'selected_options__option'
        ).order_by('product_id', 'attribute__sort_order', 'id')

        result: Dict[int, Tuple[Dict[str, str], List[SpecificationDetail]]] = {
            product_id: ({}, []) for product_id in product_ids
        }

        for attr_value in attr_values:
            simple_record, detailed_list = result.setdefault(
                attr_value.product_id, ({}, [])
            )
            attr = attr_value.attribute
            key = attr.key
            label = attr.label
            data_type = attr.data_type
            unit = attr.unit

            if data_type == AttributeModel.DataTypeChoices.TEXT:
                value = attr_value.value_text
                display = value or ''
            elif data_type == AttributeModel.DataTypeChoices.NUMBER:
                value = attr_value.value_number
                display = str(value) if value is not None else ''
            elif data_type == AttributeModel.DataTypeChoices.BOOLEAN:
                value = attr_value.value_bool
                display = '' if value is None else ('true' if value else 'false')
            elif data_type == AttributeModel.DataTypeChoices.SINGLE_SELECT:
                option = attr_value.selected_options.first()
                if option:
                    value = option.option.value
                    display = option.option.label
                else:
                    value = None
                    display = ''
            elif data_type == AttributeModel.DataTypeChoices.MULTI_SELECT:
                options = attr_value.selected_options.all()
                if options:
                    values = [opt.option.value for opt in options]
                    labels = [opt.option.label for opt in options]
                    value = ', '.join(values)
                    display = ', '.join(labels)
                else:
                    value = None
                    display = ''
            else:
                value = None
                display = ''

            if value is not None:
                simple_record[key] = str(display)

            if include_detailed:
                value_str = str(value) if value is not None else ''
                detailed_list.append(SpecificationDetail(
                    key=key,
                    label=label,
                    type=data_type,
                    value=value_str,
                    display=display,
                    unit=unit
                ))

        return result
