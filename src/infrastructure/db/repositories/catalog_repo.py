"""Catalog repository implementation."""
from typing import Optional, List, Dict, Tuple
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
from decimal import Decimal

from src.domain.catalog.entities import (
    Category, Subcategory, Product, VariantGroup, Attribute,
    AttributeOption, ProductAttributeValue
)
from typing import Optional
from src.domain.shared.types import Currency, Availability, AttributeDataType, ScopeType
from src.application.catalog.ports import CategoryRepository, ProductRepository
from src.application.catalog.dto import SpecificationDetail

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
    
    def get_all(self) -> List[Category]:
        """Get all categories."""
        category_models = CategoryModel.objects.all()
        return [self._to_domain(cat) for cat in category_models]
    
    def get_by_id(self, category_id: int) -> Optional[Category]:
        """Get category by ID."""
        try:
            category_model = CategoryModel.objects.get(id=category_id)
            return self._to_domain(category_model)
        except CategoryModel.DoesNotExist:
            return None
    
    def get_subcategory_by_id(self, subcategory_id: int) -> Optional[Subcategory]:
        """Get subcategory by ID."""
        try:
            subcategory_model = SubcategoryModel.objects.select_related('category').get(id=subcategory_id)
            return self._to_domain_subcategory(subcategory_model)
        except SubcategoryModel.DoesNotExist:
            return None
    
    def _to_domain_subcategory(self, subcategory_model: SubcategoryModel) -> Subcategory:
        """Convert Django model to domain entity."""
        return Subcategory(
            id=subcategory_model.id,
            category_id=subcategory_model.category_id,
            name=subcategory_model.name,
            slug=subcategory_model.slug,
            created_at=subcategory_model.created_at
        )
    
    def _to_domain(self, category_model: CategoryModel) -> Category:
        """Convert Django model to domain entity."""
        return Category(
            id=category_model.id,
            name=category_model.name,
            slug=category_model.slug,
            created_at=category_model.created_at
        )


class DjangoProductRepository(ProductRepository):
    """Django product repository implementation."""
    
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
        queryset = ProductModel.objects.select_related('category', 'subcategory')
        
        # Apply filters
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if subcategory_id:
            queryset = queryset.filter(subcategory_id=subcategory_id)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(brand__icontains=search)
            )
        if availability:
            queryset = queryset.filter(availability=availability)
        
        # Apply spec filters
        if spec_filters:
            for key, value in spec_filters.items():
                # Find attribute by key
                try:
                    attr = AttributeModel.objects.get(key=key)
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
                except AttributeModel.DoesNotExist:
                    pass
        
        # Get total count before pagination
        total = queryset.count()
        
        # Paginate
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        products = [self._to_domain(p) for p in page_obj]
        return products, total
    
    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        try:
            product_model = ProductModel.objects.select_related(
                'category', 'subcategory', 'variant_group'
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
        queryset = ProductModel.objects.filter(
            variant_group_id=variant_group_id
        ).select_related('category', 'subcategory', 'variant_group')
        
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
    
    def get_specifications(
        self,
        product_id: int
    ) -> Tuple[Dict[str, str], List[SpecificationDetail]]:
        """Get product specifications."""
        # Get all attribute values for product
        attr_values = ProductAttributeValueModel.objects.filter(
            product_id=product_id
        ).select_related('attribute').prefetch_related(
            'selected_options__option'
        )
        
        simple_record: Dict[str, str] = {}
        detailed_list: List[SpecificationDetail] = []
        
        for attr_value in attr_values:
            attr = attr_value.attribute
            key = attr.key
            label = attr.label
            data_type = attr.data_type
            unit = attr.unit
            
            # Get value based on data type
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
            
            # Add to simple record
            if value is not None:
                simple_record[key] = str(display)
            
            # Add to detailed list
            # Convert value to string for DTO
            value_str = str(value) if value is not None else ''
            detailed_list.append(SpecificationDetail(
                key=key,
                label=label,
                type=data_type,
                value=value_str,
                display=display,
                unit=unit
            ))
        
        return simple_record, detailed_list
    
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
            subcategory_id=product_model.subcategory_id,
            currency=Currency(product_model.currency),
            variant_group_id=product_model.variant_group_id,
            variant_color_name=product_model.variant_color_name,
            variant_color_palette=product_model.variant_color_palette,
            variant_image=product_model.variant_image,
            created_at=product_model.created_at,
            updated_at=product_model.updated_at
        )
