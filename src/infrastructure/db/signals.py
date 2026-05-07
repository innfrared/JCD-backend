"""Signal handlers for storefront cache invalidation."""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from src.infrastructure.cache.storefront_cache import (
    bump_homepage_version,
    bump_product_version,
    bump_taxonomy_version,
)
from src.infrastructure.db.models.catalog import (
    Attribute,
    Category,
    Product,
    ProductAttributeValue,
    ProductVariant,
    ProductVariantImage,
    Subcategory,
)
from src.infrastructure.db.models.homepage import HomeSection, HomeSectionItem


@receiver([post_save, post_delete], sender=Category)
@receiver([post_save, post_delete], sender=Subcategory)
@receiver([post_save, post_delete], sender=Attribute)
def invalidate_taxonomy_cache(**kwargs) -> None:
    """Invalidate taxonomy cache groups."""
    bump_taxonomy_version()


@receiver([post_save, post_delete], sender=HomeSection)
@receiver([post_save, post_delete], sender=HomeSectionItem)
def invalidate_homepage_cache(**kwargs) -> None:
    """Invalidate homepage cache group."""
    bump_homepage_version()


@receiver([post_save, post_delete], sender=Product)
@receiver([post_save, post_delete], sender=ProductVariant)
@receiver([post_save, post_delete], sender=ProductVariantImage)
@receiver([post_save, post_delete], sender=ProductAttributeValue)
def invalidate_product_cache(**kwargs) -> None:
    """Bump product storefront version (detail URLs + default first-page list snapshot).

    Admin/API saves and deletes on catalog rows refresh cached payloads instead of relying
    solely on ``CACHE_TIMEOUT`` or CDN ``max-age``. TTL/CDN windows remain an upper bound for stale reads.
    """
    bump_product_version()
