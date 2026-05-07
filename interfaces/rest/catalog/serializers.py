"""Catalog serializers."""
from rest_framework import serializers
from src.application.catalog.dto import (
    CategoryResponse,
    CategoryWithSubcategoriesResponse,
    ProductResponse,
    ProductCardResponse,
    VariantProductPreview,
    SpecificationDetail,
    ListProductsRequest,
)


class CategoryResponseSerializer(serializers.Serializer):
    """Category response serializer."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    image = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()


class SubcategoryResponseSerializer(serializers.Serializer):
    """Subcategory response serializer."""
    id = serializers.IntegerField()
    category_id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    image = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()
    slug_aliases = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )


class CategoryWithSubcategoriesResponseSerializer(serializers.Serializer):
    """Category response serializer with subcategories."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    image = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()
    subcategories = SubcategoryResponseSerializer(many=True)


class VariantProductPreviewSerializer(serializers.Serializer):
    """Variant product preview serializer."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    price = serializers.CharField()
    availability = serializers.CharField()
    image = serializers.CharField(allow_null=True)
    color_name = serializers.CharField(allow_null=True)
    color_palette = serializers.CharField(allow_null=True)


class VariantSwitchOptionSerializer(serializers.Serializer):
    """Variant switcher option serializer."""
    id = serializers.IntegerField()
    image = serializers.CharField(allow_null=True)
    color_name = serializers.CharField(allow_null=True)
    color_palette = serializers.CharField(allow_null=True)
    is_current = serializers.BooleanField()


class ProductVariantImageSerializer(serializers.Serializer):
    """Single image item for product variant gallery."""
    id = serializers.IntegerField()
    url = serializers.CharField(source='image_url', allow_null=True)
    alt = serializers.CharField(allow_blank=True, default='')
    sort_order = serializers.IntegerField(min_value=0)
    is_primary = serializers.BooleanField()


class ProductVariantDetailSerializer(serializers.Serializer):
    """Detailed variant serializer for product detail endpoint."""
    id = serializers.IntegerField()
    folder = serializers.CharField(allow_null=True)
    color = serializers.CharField(allow_null=True)
    material = serializers.CharField(allow_null=True)
    cord_diameter = serializers.CharField(allow_null=True)
    cord_type = serializers.CharField(allow_null=True)
    description = serializers.CharField(allow_null=True)
    care = serializers.CharField(allow_null=True)
    handles = serializers.CharField(allow_null=True)
    image_url = serializers.CharField(allow_null=True)
    images = ProductVariantImageSerializer(many=True)
    sort_order = serializers.IntegerField()


class SpecificationDetailSerializer(serializers.Serializer):
    """Specification detail serializer."""
    key = serializers.CharField()
    label = serializers.CharField()
    type = serializers.CharField()
    value = serializers.JSONField()
    display = serializers.CharField()
    unit = serializers.CharField(allow_null=True)


class ProductResponseSerializer(serializers.Serializer):
    """Product response serializer."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    brand = serializers.CharField(allow_null=True)
    price = serializers.CharField()
    price_new = serializers.CharField(allow_null=True)
    price_old = serializers.CharField(allow_null=True)
    availability = serializers.CharField()
    category_id = serializers.IntegerField()
    subcategory_ids = serializers.ListField(child=serializers.IntegerField())
    category = CategoryResponseSerializer(allow_null=True)
    subcategories = SubcategoryResponseSerializer(many=True)
    currency = serializers.CharField()
    variant_group_id = serializers.IntegerField(allow_null=True)
    variant_color_name = serializers.CharField(allow_null=True)
    variant_color_palette = serializers.CharField(allow_null=True)
    variant_image = serializers.CharField(allow_null=True)
    variant_ids = serializers.ListField(child=serializers.IntegerField())
    variant_options = VariantSwitchOptionSerializer(many=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    variants = VariantProductPreviewSerializer(many=True)
    variants_detailed = ProductVariantDetailSerializer(many=True)
    specifications = serializers.DictField(child=serializers.CharField())
    specifications_detailed = SpecificationDetailSerializer(many=True)


class ProductCardResponseSerializer(serializers.Serializer):
    """Product card serializer for listing endpoint."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    brand = serializers.CharField(allow_null=True)
    price = serializers.CharField()
    price_new = serializers.CharField(allow_null=True)
    price_old = serializers.CharField(allow_null=True)
    availability = serializers.CharField()
    currency = serializers.CharField()
    image_url = serializers.CharField(allow_null=True)
    category_id = serializers.IntegerField()
    subcategory_ids = serializers.ListField(child=serializers.IntegerField())
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    specifications = serializers.DictField(
        child=serializers.CharField(),
        required=False,
    )
    specifications_detailed = SpecificationDetailSerializer(
        many=True,
        required=False,
    )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not data.get('specifications'):
            data.pop('specifications', None)
        if not data.get('specifications_detailed'):
            data.pop('specifications_detailed', None)
        return data


class PaginatedProductResponseSerializer(serializers.Serializer):
    """Paginated product response serializer."""
    items = ProductCardResponseSerializer(many=True)
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    has_next = serializers.BooleanField()
    has_previous = serializers.BooleanField()

