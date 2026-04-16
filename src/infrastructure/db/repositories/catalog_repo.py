"""Catalog repository implementation."""
from typing import Optional, List, Dict, Tuple
from django.db.models import Q
from django.core.paginator import Paginator
from decimal import Decimal

from src.domain.catalog.entities import (
    Category, Subcategory, Product, ProductVariant, VariantGroup, Attribute,
    AttributeOption, ProductAttributeValue
)
from typing import Optional
from src.domain.shared.types import Currency, Availability, AttributeDataType, ScopeType
from src.application.catalog.ports import CategoryRepository, ProductRepository
from src.application.catalog.dto import SpecificationDetail
from src.infrastructure.db.querysets.catalog import with_resolved_primary_image

from src.infrastructure.db.models.catalog import (
    Category as CategoryModel,
    Subcategory as SubcategoryModel,
    Product as ProductModel,
    VariantGroup as VariantGroupModel,
    ProductVariant as ProductVariantModel,
    VariantSize as VariantSizeModel,
    Attribute as AttributeModel,
    AttributeOption as AttributeOptionModel,
    ProductAttributeValue as ProductAttributeValueModel,
    ProductAttributeOption as ProductAttributeOptionModel
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
        try:
            category_model = CategoryModel.objects.get(id=category_id)
            return self._to_domain(category_model)
        except CategoryModel.DoesNotExist:
            return None

    def get_by_ids(self, category_ids: List[int]) -> Dict[int, Category]:
        """Get categories indexed by ID."""
        if not category_ids:
            return {}
        category_models = CategoryModel.objects.filter(id__in=category_ids)
        return {cat.id: self._to_domain(cat) for cat in category_models}
    
    def get_subcategory_by_id(self, subcategory_id: int) -> Optional[Subcategory]:
        """Get subcategory by ID."""
        try:
            subcategory_model = SubcategoryModel.objects.select_related('category').get(id=subcategory_id)
            return self._to_domain_subcategory(subcategory_model)
        except SubcategoryModel.DoesNotExist:
            return None

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
    """Django product repository implementation."""

    @staticmethod
    def _subcategory_ids_from_model(product_model: ProductModel) -> List[int]:
        """Read subcategory IDs without triggering per-product queries."""
        prefetched = getattr(product_model, '_prefetched_objects_cache', {})
        cached_subcategories = prefetched.get('subcategories')
        if cached_subcategories is not None:
            return [subcategory.id for subcategory in cached_subcategories]
        return list(product_model.subcategories.values_list('id', flat=True))
    
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
        queryset = with_resolved_primary_image(
            ProductModel.objects.select_related('category').prefetch_related('subcategories')
        )
        
        # Apply filters
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if subcategory_ids:
            queryset = queryset.filter(subcategories__id__in=subcategory_ids)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(brand__icontains=search)
            )
        if availability:
            queryset = queryset.filter(availability=availability)
        
        # Apply spec filters
        if spec_filters:
            attr_models = AttributeModel.objects.filter(key__in=spec_filters.keys()).order_by('id')
            attrs_by_key: Dict[str, AttributeModel] = {}
            for attr in attr_models:
                attrs_by_key.setdefault(attr.key, attr)
            for key, value in spec_filters.items():
                attr = attrs_by_key.get(key)
                if not attr:
                    continue
                # Filter products by attribute value
                if attr.data_type == AttributeModel.DataTypeChoices.TEXT:
                    queryset = queryset.filter(
                        attribute_values__attribute=attr,
                        attribute_values__value_text__icontains=value
                    )
                elif attr.data_type == AttributeModel.DataTypeChoices.NUMBER:
                    try:
                        num_value = Decimal(value)
                        queryset = queryset.filter(
                            attribute_values__attribute=attr,
                            attribute_values__value_number=num_value
                        )
                    except (ValueError, TypeError):
                        pass
                elif attr.data_type == AttributeModel.DataTypeChoices.BOOLEAN:
                    bool_value = value.lower() in ('true', '1', 'yes')
                    queryset = queryset.filter(
                        attribute_values__attribute=attr,
                        attribute_values__value_bool=bool_value
                    )
                elif attr.data_type in [
                    AttributeModel.DataTypeChoices.SINGLE_SELECT,
                    AttributeModel.DataTypeChoices.MULTI_SELECT
                ]:
                    queryset = queryset.filter(
                        attribute_values__attribute=attr,
                        attribute_values__selected_options__option__value=value
                    )
        
        # Paginate once and reuse paginator.count to avoid duplicate count queries.
        distinct_queryset = queryset.distinct()
        paginator = Paginator(distinct_queryset, page_size)
        page_obj = paginator.get_page(page)
        total = paginator.count
        
        products = [self._to_domain(p) for p in page_obj]
        return products, total
    
    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        try:
            product_model = with_resolved_primary_image(
                ProductModel.objects.select_related(
                    'category', 'variant_group'
                ).prefetch_related('subcategories')
            ).get(id=product_id)
            return self._to_domain(product_model)
        except ProductModel.DoesNotExist:
            return None
    
    def get_variant_group_products(
        self,
        variant_group_id: int,
        exclude_product_id: Optional[int] = None
    ) -> List[Product]:
        """Get all products in a variant group, excluding specified product."""
        queryset = with_resolved_primary_image(ProductModel.objects.filter(
            variant_group_id=variant_group_id
        ).select_related('category', 'variant_group').prefetch_related(
            'subcategories'
        ))
        
        if exclude_product_id:
            queryset = queryset.exclude(id=exclude_product_id)
        
        # Order: default product first (if exists), then by id
        variant_group = VariantGroupModel.objects.filter(id=variant_group_id).first()
        if variant_group and variant_group.default_product_id:
            # Put default first
            from django.db.models import Case, When, IntegerField
            queryset = queryset.annotate(
                is_default=Case(
                    When(id=variant_group.default_product_id, then=0),
                    default=1,
                    output_field=IntegerField()
                )
            ).order_by('is_default', 'id')
        else:
            queryset = queryset.order_by('id')
        
        return [self._to_domain(p) for p in queryset]

    def get_product_variants(self, product_id: int) -> List[ProductVariant]:
        """Get all variants for a specific product."""
        variant_models = ProductVariantModel.objects.filter(
            product_id=product_id
        ).order_by('sort_order', 'id')
        return [self._variant_to_domain(v) for v in variant_models]
    
    def get_specifications(
        self,
        product_id: int
    ) -> Tuple[Dict[str, str], List[SpecificationDetail]]:
        """Get product specifications."""
        specs_map = self.get_specifications_batch([product_id], include_detailed=True)
        return specs_map.get(product_id, ({}, []))

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
    
    def _to_domain(self, product_model: ProductModel) -> Product:
        """Convert Django model to domain entity."""
        resolved_variant_image = getattr(
            product_model,
            'resolved_variant_image',
            None,
        )
        return Product(
            id=product_model.id,
            name=product_model.name,
            description=product_model.description,
            brand=product_model.brand,
            price=product_model.price,
            price_new=product_model.price_new,
            price_old=product_model.price_old,
            availability=Availability(product_model.availability),
            category_id=product_model.category_id,
            subcategory_ids=self._subcategory_ids_from_model(product_model),
            currency=Currency(product_model.currency),
            variant_group_id=product_model.variant_group_id,
            variant_color_name=product_model.variant_color_name,
            variant_color_palette=product_model.variant_color_palette,
            variant_image=resolved_variant_image or product_model.variant_image,
            created_at=product_model.created_at,
            updated_at=product_model.updated_at
        )

    def _variant_to_domain(
        self,
        variant_model: ProductVariantModel,
    ) -> ProductVariant:
        """Convert Django variant model to domain entity."""
        return ProductVariant(
            id=variant_model.id,
            product_id=variant_model.product_id,
            folder=variant_model.folder,
            color=variant_model.color,
            material=variant_model.material,
            cord_diameter=variant_model.cord_diameter,
            cord_type=variant_model.cord_type,
            description=variant_model.description,
            care=variant_model.care,
            handles=variant_model.handles,
            name=variant_model.name,
            value=variant_model.value,
            image_url=variant_model.image_url,
            color_palette=variant_model.color_palette,
            sort_order=variant_model.sort_order,
            sizes=[],
        )
