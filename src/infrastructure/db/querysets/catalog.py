"""Reusable catalog queryset helpers."""
from django.db.models import F, OuterRef, QuerySet, Subquery, Value
from django.db.models.functions import Coalesce, NullIf

from src.infrastructure.db.models.catalog import ProductVariant


def with_resolved_primary_image(queryset: QuerySet) -> QuerySet:
    """Annotate products with deterministic primary image resolution.

    Preserves Product.variant_image when present (historically curated),
    otherwise picks the first non-empty variant image by (sort_order, id).
    """
    variant_image_subquery = ProductVariant.objects.filter(
        product_id=OuterRef("pk"),
        image_url__isnull=False,
    ).exclude(
        image_url="",
    ).order_by(
        "sort_order",
        "id",
    ).values(
        "image_url"
    )[:1]

    return queryset.annotate(
        resolved_variant_image=Coalesce(
            NullIf(F("variant_image"), Value("")),
            Subquery(variant_image_subquery),
        )
    )
