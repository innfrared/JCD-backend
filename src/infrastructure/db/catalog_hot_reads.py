"""
Hot-path catalog reads: minimal ORM round trips for list/detail.

Owns SQL shape for GET /api/products and GET /api/products/<id>.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Exists, OuterRef, Prefetch, Q, Subquery

from src.application.catalog.dto import SpecificationDetail
from src.application.catalog.taxonomy_contract import (
    bags_subcategory_aliases,
    expand_bags_query_aliases,
)
from src.domain.shared.exceptions import NotFoundError
from src.infrastructure.db.querysets.catalog import with_resolved_primary_image
from src.infrastructure.db.models.catalog import (
    Attribute as AttributeModel,
    Product as ProductModel,
    ProductAttributeValue as ProductAttributeValueModel,
    ProductVariant as ProductVariantModel,
    Subcategory as SubcategoryModel,
)


def _detail_primary_image(product: ProductModel) -> Optional[str]:
    resolved = getattr(product, 'resolved_variant_image', None)
    if resolved:
        return resolved
    return product.variant_image


def _card_image_url(product: ProductModel) -> Optional[str]:
    if product.variant_image:
        return product.variant_image
    for v in product.variants.all():
        if v.image_url:
            return v.image_url
    return None


def _subcategory_ids_from_product(product: ProductModel) -> List[int]:
    return [s.id for s in product.subcategories.all()]


def build_product_list_queryset(
    *,
    category_id: Optional[int],
    subcategory_ids: Optional[List[int]],
    search: Optional[str],
    availability: Optional[str],
    spec_filters: Optional[Dict[str, str]],
) -> Any:
    """Single Product queryset without join-induced distinct(); filters use semijoins/Exists."""
    through = ProductModel.subcategories.through
    qs = ProductModel.objects.all()
    qs = qs.prefetch_related(
        Prefetch(
            'subcategories',
            SubcategoryModel.objects.only('id'),
        ),
        Prefetch(
            'variants',
            ProductVariantModel.objects.only(
                'id', 'product_id', 'image_url', 'sort_order'
            ).order_by('sort_order', 'id'),
        ),
    )
    qs = qs.only(
        'id',
        'name',
        'brand',
        'price',
        'price_new',
        'price_old',
        'availability',
        'currency',
        'variant_image',
        'category_id',
        'created_at',
        'updated_at',
    )

    if category_id:
        qs = qs.filter(category_id=category_id)
    if subcategory_ids:
        qs = qs.filter(
            id__in=Subquery(
                through.objects.filter(
                    subcategory_id__in=subcategory_ids
                ).values('product_id')
            )
        )
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(brand__icontains=search))
    if availability:
        qs = qs.filter(availability=availability)

    if spec_filters:
        attrs = list(AttributeModel.objects.filter(key__in=spec_filters.keys()))
        attrs_by_key = {a.key: a for a in attrs}
        for key, value in spec_filters.items():
            attr = attrs_by_key.get(key)
            if not attr:
                continue
            dt = attr.data_type
            if dt == AttributeModel.DataTypeChoices.TEXT:
                qs = qs.filter(
                    Exists(
                        ProductAttributeValueModel.objects.filter(
                            product_id=OuterRef('pk'),
                            attribute_id=attr.id,
                            value_text__icontains=value,
                        )
                    )
                )
            elif dt == AttributeModel.DataTypeChoices.NUMBER:
                try:
                    num_value = Decimal(value)
                except (ValueError, TypeError):
                    continue
                qs = qs.filter(
                    Exists(
                        ProductAttributeValueModel.objects.filter(
                            product_id=OuterRef('pk'),
                            attribute_id=attr.id,
                            value_number=num_value,
                        )
                    )
                )
            elif dt == AttributeModel.DataTypeChoices.BOOLEAN:
                bool_value = value.lower() in ('true', '1', 'yes')
                qs = qs.filter(
                    Exists(
                        ProductAttributeValueModel.objects.filter(
                            product_id=OuterRef('pk'),
                            attribute_id=attr.id,
                            value_bool=bool_value,
                        )
                    )
                )
            elif dt in (
                AttributeModel.DataTypeChoices.SINGLE_SELECT,
                AttributeModel.DataTypeChoices.MULTI_SELECT,
            ):
                qs = qs.filter(
                    Exists(
                        ProductAttributeValueModel.objects.filter(
                            product_id=OuterRef('pk'),
                            attribute_id=attr.id,
                            selected_options__option__value=value,
                        )
                    )
                )

    return qs.order_by('-created_at')


def paginate_product_queryset(
    qs,
    page: int,
    page_size: int,
) -> Tuple[List[ProductModel], int]:
    total = qs.count()
    start = (page - 1) * page_size
    rows = list(qs[start : start + page_size])
    return rows, total


def product_rows_to_card_dicts(
    rows: List[ProductModel],
    specifications_map: Optional[Dict[int, Tuple[Dict[str, str], List[SpecificationDetail]]]],
    include_detailed_specs: bool,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for p in rows:
        item: Dict[str, Any] = {
            'id': p.id,
            'name': p.name,
            'brand': p.brand,
            'price': str(p.price),
            'price_new': str(p.price_new) if p.price_new is not None else None,
            'price_old': str(p.price_old) if p.price_old is not None else None,
            'availability': p.availability,
            'currency': p.currency,
            'image_url': _card_image_url(p),
            'category_id': p.category_id,
            'subcategory_ids': _subcategory_ids_from_product(p),
            'created_at': p.created_at,
            'updated_at': p.updated_at,
        }
        if include_detailed_specs and specifications_map and p.id in specifications_map:
            simple, detailed = specifications_map[p.id]
            item['specifications'] = simple
            item['specifications_detailed'] = detailed
        out.append(item)
    return out


def resolve_list_subcategory_ids(
    category_repo,
    category_id: Optional[int],
    subcategory_slugs: Optional[List[str]],
    subcategory_ids: Optional[List[int]],
) -> Optional[List[int]]:
    if not subcategory_slugs:
        return subcategory_ids
    expanded = list(subcategory_slugs)
    if category_id:
        category = category_repo.get_by_id(category_id)
        if category and category.slug == 'bags':
            expanded = expand_bags_query_aliases(expanded)
    subs = category_repo.get_subcategories_by_slugs(
        slugs=expanded,
        category_id=category_id,
    )
    return [s.id for s in subs]


def load_product_detail_orm(product_id: int) -> ProductModel:
    """Load product with category, subcategories, variants, and variant-group siblings in few ORM round trips."""
    try:
        base = with_resolved_primary_image(
            ProductModel.objects.filter(pk=product_id).select_related(
                'category', 'variant_group'
            )
        )
        base = base.prefetch_related(
            Prefetch(
                'subcategories',
                SubcategoryModel.objects.all(),
            ),
            Prefetch(
                'variants',
                ProductVariantModel.objects.order_by('sort_order', 'id'),
            ),
        )
        sibling_qs = (
            ProductModel.objects.select_related('category')
            .prefetch_related(
                Prefetch(
                    'subcategories',
                    SubcategoryModel.objects.only(
                        'id',
                        'category_id',
                        'name',
                        'slug',
                        'description',
                        'image',
                        'created_at',
                    ),
                ),
            )
            .only(
                'id',
                'name',
                'price',
                'availability',
                'variant_image',
                'variant_color_name',
                'variant_color_palette',
                'variant_group_id',
                'category_id',
            )
            .order_by('id')
        )

        base = base.prefetch_related(
            Prefetch(
                'variant_group__products',
                queryset=sibling_qs,
            ),
        )
        return base.get(pk=product_id)
    except ProductModel.DoesNotExist as exc:
        raise NotFoundError('Product not found') from exc


def build_product_detail_payload(
    product: ProductModel,
    specs_simple: Dict[str, str],
    specs_detailed: List[SpecificationDetail],
) -> Dict[str, Any]:
    """Build PDP JSON dict from ORM instances (no extra DB)."""
    category = product.category
    is_bags = bool(category and category.slug == 'bags')

    subcategories_payload = []
    for sub in product.subcategories.all():
        aliases = bags_subcategory_aliases(sub.slug) if is_bags else None
        subcategories_payload.append(
            {
                'id': sub.id,
                'category_id': sub.category_id,
                'name': sub.name,
                'slug': sub.slug,
                'description': sub.description,
                'image': sub.image,
                'created_at': sub.created_at,
                'slug_aliases': aliases,
            }
        )

    category_payload = None
    if category:
        category_payload = {
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'image': category.image,
            'created_at': category.created_at,
        }

    primary_img = _detail_primary_image(product)
    variant_ids: List[int] = [product.id]
    variant_options: List[Dict[str, Any]] = [
        {
            'id': product.id,
            'image': primary_img,
            'color_name': product.variant_color_name,
            'color_palette': product.variant_color_palette,
            'is_current': True,
        }
    ]
    variant_previews: List[Dict[str, Any]] = []

    if product.variant_group_id:
        siblings = list(product.variant_group.products.all())
        vg = product.variant_group
        if vg and vg.default_product_id:
            siblings.sort(
                key=lambda p: (0 if p.id == vg.default_product_id else 1, p.id)
            )
        else:
            siblings.sort(key=lambda p: p.id)

        variant_ids = [p.id for p in siblings]
        variant_options = [
            {
                'id': p.id,
                'image': p.variant_image,
                'color_name': p.variant_color_name,
                'color_palette': p.variant_color_palette,
                'is_current': (p.id == product.id),
            }
            for p in siblings
        ]
        for p in siblings:
            if p.id != product.id:
                variant_previews.append(
                    {
                        'id': p.id,
                        'name': p.name,
                        'price': str(p.price),
                        'availability': p.availability,
                        'image': p.variant_image,
                        'color_name': p.variant_color_name,
                        'color_palette': p.variant_color_palette,
                    }
                )

    variants_detailed = [
        {
            'id': v.id,
            'folder': v.folder,
            'color': v.color,
            'material': v.material,
            'cord_diameter': v.cord_diameter,
            'cord_type': v.cord_type,
            'description': v.description,
            'care': v.care,
            'handles': v.handles,
            'image_url': v.image_url,
            'sort_order': v.sort_order,
        }
        for v in product.variants.all()
    ]

    return {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'brand': product.brand,
        'price': str(product.price),
        'price_new': str(product.price_new) if product.price_new is not None else None,
        'price_old': str(product.price_old) if product.price_old is not None else None,
        'availability': product.availability,
        'category_id': product.category_id,
        'subcategory_ids': [s.id for s in product.subcategories.all()],
        'category': category_payload,
        'subcategories': subcategories_payload,
        'currency': product.currency,
        'variant_group_id': product.variant_group_id,
        'variant_color_name': product.variant_color_name,
        'variant_color_palette': product.variant_color_palette,
        'variant_image': primary_img,
        'variant_ids': variant_ids,
        'variant_options': variant_options,
        'created_at': product.created_at,
        'updated_at': product.updated_at,
        'variants': variant_previews,
        'variants_detailed': variants_detailed,
        'specifications': specs_simple,
        'specifications_detailed': [
            {
                'key': s.key,
                'label': s.label,
                'type': s.type,
                'value': s.value,
                'display': s.display,
                'unit': s.unit,
            }
            for s in specs_detailed
        ],
    }
