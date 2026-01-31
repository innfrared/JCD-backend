"""Catalog serializers."""
from rest_framework import serializers
from src.application.catalog.dto import (
    CategoryResponse,
    CategoryWithSubcategoriesResponse,
    ProductResponse,
    VariantProductPreview,
    SpecificationDetail,
    ListProductsRequest,
)


class CategoryResponseSerializer(serializers.Serializer):
    """Category response serializer."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    created_at = serializers.DateTimeField()


class SubcategoryResponseSerializer(serializers.Serializer):
    """Subcategory response serializer."""
    id = serializers.IntegerField()
    category_id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()


class CategoryWithSubcategoriesResponseSerializer(serializers.Serializer):
    """Category response serializer with subcategories."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
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
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    variants = VariantProductPreviewSerializer(many=True)
    specifications = serializers.DictField(child=serializers.CharField())
    specifications_detailed = SpecificationDetailSerializer(many=True)


class PaginatedProductResponseSerializer(serializers.Serializer):
    """Paginated product response serializer."""
    items = ProductResponseSerializer(many=True)
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    has_next = serializers.BooleanField()
    has_previous = serializers.BooleanField()

