"""Storefront cache helpers with explicit versioning/invalidation."""
from typing import Optional

from django.core.cache import cache


_TAXONOMY_VERSION_KEY = "storefront:version:taxonomy"
_HOMEPAGE_VERSION_KEY = "storefront:version:homepage"
_PRODUCT_VERSION_KEY = "storefront:version:product"


def _get_version(version_key: str) -> int:
    value = cache.get(version_key)
    if value is None:
        cache.set(version_key, 1, None)
        return 1
    return int(value)


def _bump_version(version_key: str) -> None:
    current = _get_version(version_key)
    cache.set(version_key, current + 1, None)


def bump_taxonomy_version() -> None:
    """Invalidate taxonomy caches."""
    _bump_version(_TAXONOMY_VERSION_KEY)


def bump_homepage_version() -> None:
    """Invalidate homepage caches."""
    _bump_version(_HOMEPAGE_VERSION_KEY)


def bump_product_version() -> None:
    """Bump storefront product version so default product-list snapshot and PDP caches invalidate."""
    _bump_version(_PRODUCT_VERSION_KEY)


def categories_cache_key() -> str:
    """Versioned key for /api/categories."""
    return f"storefront:categories:v{_get_version(_TAXONOMY_VERSION_KEY)}"


def categories_all_cache_key() -> str:
    """Versioned key for /api/categories/all."""
    return f"storefront:categories-all:v{_get_version(_TAXONOMY_VERSION_KEY)}"


def homepage_cache_key() -> str:
    """Versioned key for /api/home."""
    return f"storefront:homepage:v{_get_version(_HOMEPAGE_VERSION_KEY)}"


def product_detail_cache_key(
    product_id: int,
    include_detailed_specs: bool = True,
) -> str:
    """Versioned key for /api/products/<id>."""
    details_flag = "details-on" if include_detailed_specs else "details-off"
    return (
        f"storefront:product-detail:{product_id}:{details_flag}:"
        f"v{_get_version(_PRODUCT_VERSION_KEY)}"
    )


def product_list_default_cache_key() -> str:
    """Stable Django-cache key for exactly ONE listing variant.

    Only ``GET /api/products`` requests that pass ``_is_default_product_list_cacheable``
    in ``interfaces.rest.catalog.views`` may read/write this key: ``page=1``,
    ``page_size=20``, no ``category_id`` / subcategory ids or slugs, no ``search`` /
    ``availability``, no ``spec_*``, ``include_detailed_specs=false``.

    Any other query (including ``page_size=18`` or filtered listings) never touches this
    key—responses are computed fresh—so there is no collision risk from undocumented params
    (``color``, ``sort``, etc.). If those become supported filters later, either keep them
    out of this keyed path or extend caching explicitly.

    The trailing ``v{n}`` comes from ``bump_product_version()`` on catalog mutations (see
    ``signals.py``), so admin edits invalidate this snapshot without relying solely on TTL.
    """
    return f"storefront:products:list:default:v{_get_version(_PRODUCT_VERSION_KEY)}"
