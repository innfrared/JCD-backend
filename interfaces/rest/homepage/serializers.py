"""Homepage serializers."""
from rest_framework import serializers
from src.application.homepage.dto import (
    ProductCard, HomeCarouselSection, HomePageResponse
)


class ProductCardSerializer(serializers.Serializer):
    """Product card serializer."""
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
    subcategory_id = serializers.IntegerField(allow_null=True)


class HomeCarouselSectionSerializer(serializers.Serializer):
    """Home carousel section serializer."""
    id = serializers.IntegerField()
    key = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    main_image = serializers.CharField(allow_null=True)
    category_name = serializers.CharField(allow_null=True)
    product_count = serializers.IntegerField()
    sort_order = serializers.IntegerField()
    is_active = serializers.BooleanField()
    items = ProductCardSerializer(many=True)


class HomePageResponseSerializer(serializers.Serializer):
    """Homepage response serializer."""
    sections = HomeCarouselSectionSerializer(many=True)

