"""Catalog views."""
import logging
import re
import time

from django.conf import settings
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from rest_framework import status

from src.application.catalog.use_cases import (
    ListCategoriesUseCase,
    ListCategoriesWithSubcategoriesUseCase,
    ListSubcategoriesByCategoryUseCase,
)
from src.application.catalog.ports import CategoryRepository, ProductRepository
from src.domain.shared.types import Availability
from src.infrastructure.db.repositories.catalog_repo import (
    DjangoCategoryRepository, DjangoProductRepository
)
from src.domain.shared.exceptions import NotFoundError
from interfaces.rest.catalog.serializers import (
    CategoryResponseSerializer,
    CategoryWithSubcategoriesResponseSerializer,
    SubcategoryResponseSerializer,
    ProductResponseSerializer,
    PaginatedProductResponseSerializer,
)
from interfaces.rest.shared.responses import success_response, error_response
from src.infrastructure.cache.storefront_cache import (
    categories_all_cache_key,
    categories_cache_key,
    product_detail_cache_key,
    product_list_default_cache_key,
)
from src.infrastructure.db import catalog_hot_reads as catalog_hot_reads


logger = logging.getLogger('catalog.timing')

_PUBLIC_CATALOG_CACHE_CONTROL = (
    'public, max-age=60, s-maxage=600, stale-while-revalidate=300'
)


def _with_public_cache_headers(response):
    """CDN-friendly headers only; never ``Vary: Cookie`` (would defeat shared CDN/cache)."""
    response['Cache-Control'] = _PUBLIC_CATALOG_CACHE_CONTROL
    response['Vary'] = 'Accept-Encoding'
    return response


# Initialize dependencies
_category_repo: CategoryRepository = DjangoCategoryRepository()
_product_repo: ProductRepository = DjangoProductRepository()
MAX_PAGE_SIZE = 60
MAX_SEARCH_LENGTH = 120
MAX_SPEC_FILTERS = 12
MAX_SUBCATEGORY_SLUGS = 10
SLUG_PATTERN = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
ALLOWED_AVAILABILITY = {item.value for item in Availability}


def _parse_int_param(query_params, name: str, default=None, min_value=None, max_value=None):
    raw_value = query_params.get(name)
    if raw_value in (None, ''):
        return default
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        raise ValueError(f'Invalid integer value for "{name}"')

    if min_value is not None and value < min_value:
        raise ValueError(f'"{name}" must be at least {min_value}')
    if max_value is not None and value > max_value:
        raise ValueError(f'"{name}" must be at most {max_value}')
    return value


def _parse_bool_param(query_params, name: str, default: bool = False) -> bool:
    raw_value = query_params.get(name)
    if raw_value is None:
        return default
    normalized = str(raw_value).strip().lower()
    if normalized in ('true', '1', 'yes'):
        return True
    if normalized in ('false', '0', 'no'):
        return False
    raise ValueError(f'Invalid boolean value for "{name}"')


def _parse_slug_filter(raw_slug: str, field_name: str) -> str:
    slug = raw_slug.strip()
    if not slug:
        raise ValueError(f'"{field_name}" cannot be empty')
    if not SLUG_PATTERN.match(slug):
        raise ValueError(f'Invalid slug format in "{field_name}"')
    return slug


def _parse_subcategory_slugs(query_params):
    subcategory_slug = query_params.get('subcategory_slug')
    subcategory_slugs_param = query_params.get('subcategory_slugs')

    if subcategory_slugs_param:
        slugs = [
            _parse_slug_filter(raw_slug, 'subcategory_slugs')
            for raw_slug in subcategory_slugs_param.split(',')
            if raw_slug.strip()
        ]
        if not slugs:
            raise ValueError('"subcategory_slugs" must include at least one slug')
        if len(slugs) > MAX_SUBCATEGORY_SLUGS:
            raise ValueError(
                f'"subcategory_slugs" supports up to {MAX_SUBCATEGORY_SLUGS} slugs'
            )
        return slugs

    if subcategory_slug:
        return [_parse_slug_filter(subcategory_slug, 'subcategory_slug')]
    return None


def _parse_spec_filters(query_params):
    spec_filters = {}
    for key, value in query_params.items():
        if not key.startswith('spec_'):
            continue
        spec_key = key[5:]
        if not spec_key:
            raise ValueError('Invalid spec filter key')
        if len(spec_filters) >= MAX_SPEC_FILTERS:
            raise ValueError(
                f'A maximum of {MAX_SPEC_FILTERS} spec filters is allowed'
            )
        spec_filters[spec_key] = value
    return spec_filters or None


class CategoryListView(APIView):
    """Category list view."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """List categories."""
        cached_payload = cache.get(categories_cache_key())
        if cached_payload is not None:
            return _with_public_cache_headers(success_response(cached_payload))

        use_case = ListCategoriesUseCase(_category_repo)
        categories = use_case.execute()
        payload = [
            CategoryResponseSerializer(cat).data for cat in categories
        ]
        cache.set(categories_cache_key(), payload, timeout=settings.CACHE_TIMEOUT)
        return _with_public_cache_headers(success_response(payload))


class CategoryWithSubcategoriesListView(APIView):
    """Category list with subcategories view."""
    permission_classes = [AllowAny]

    def get(self, request):
        """List categories with subcategories."""
        cached_payload = cache.get(categories_all_cache_key())
        if cached_payload is not None:
            return _with_public_cache_headers(success_response(cached_payload))

        use_case = ListCategoriesWithSubcategoriesUseCase(_category_repo)
        categories = use_case.execute()
        payload = [
            CategoryWithSubcategoriesResponseSerializer(cat).data
            for cat in categories
        ]
        cache.set(
            categories_all_cache_key(),
            payload,
            timeout=settings.CACHE_TIMEOUT,
        )
        return _with_public_cache_headers(success_response(payload))


class SubcategoryListByCategoryView(APIView):
    """Subcategory list for a category view."""
    permission_classes = [AllowAny]

    def get(self, request, category_id: int):
        """List subcategories for a category."""
        use_case = ListSubcategoriesByCategoryUseCase(_category_repo)
        subcategories = use_case.execute(category_id)
        return success_response([
            SubcategoryResponseSerializer(sub).data for sub in subcategories
        ])


def _is_default_product_list_cacheable(
    *,
    category_id,
    subcategory_ids,
    subcategory_slugs,
    search,
    availability,
    spec_filters,
    page,
    page_size,
    include_detailed_specs,
) -> bool:
    """Gate Django-cache use for the global default listing only.

    When ``True``, responses share ``product_list_default_cache_key()`` (not parameterized by
    query beyond these guards). ``False`` for every filtered/paged variant—including e.g.
    ``page_size=18``, ``category_id``, ``subcategory_slug``, ``search``, ``spec_*``—so those
    requests never read/write the default snapshot and cannot serve stale wrong slices.

    There is no ``sort`` / ``color`` query API today; if added, either keep uncached here or
    introduce explicit keys.
    """
    if include_detailed_specs:
        return False
    if page != 1 or page_size != 20:
        return False
    if category_id is not None:
        return False
    if subcategory_ids or subcategory_slugs:
        return False
    if search or availability or spec_filters:
        return False
    return True


class ProductListView(APIView):
    """Product list view."""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'catalog_list'

    def get(self, request):
        """List products."""
        from src.application.catalog.dto import ListProductsRequest

        t0 = time.perf_counter()

        try:
            category_id = _parse_int_param(
                request.query_params,
                'category_id',
                default=None,
                min_value=1,
            )
            subcategory_id = _parse_int_param(
                request.query_params,
                'subcategory_id',
                default=None,
                min_value=1,
            )
            page = _parse_int_param(
                request.query_params,
                'page',
                default=1,
                min_value=1,
            )
            page_size = _parse_int_param(
                request.query_params,
                'page_size',
                default=20,
                min_value=1,
                max_value=MAX_PAGE_SIZE,
            )
            include_detailed_specs = _parse_bool_param(
                request.query_params,
                'include_detailed_specs',
                default=False,
            )
            search = request.query_params.get('search')
            if search and len(search) > MAX_SEARCH_LENGTH:
                raise ValueError(
                    f'"search" must be at most {MAX_SEARCH_LENGTH} characters'
                )

            availability = request.query_params.get('availability')
            if availability and availability not in ALLOWED_AVAILABILITY:
                raise ValueError(
                    f'Invalid "availability". Allowed values: {", ".join(sorted(ALLOWED_AVAILABILITY))}'
                )

            spec_filters = _parse_spec_filters(request.query_params)
            subcategory_slugs = _parse_subcategory_slugs(request.query_params)

            subcategory_ids_param = request.query_params.get('subcategory_ids')
            subcategory_ids = None
            if subcategory_ids_param:
                subcategory_ids = []
                for value in subcategory_ids_param.split(','):
                    normalized = value.strip()
                    if not normalized:
                        continue
                    try:
                        parsed_id = int(normalized)
                    except ValueError:
                        raise ValueError('Invalid "subcategory_ids" value')
                    if parsed_id < 1:
                        raise ValueError('"subcategory_ids" values must be positive')
                    subcategory_ids.append(parsed_id)
                if not subcategory_ids:
                    raise ValueError('"subcategory_ids" must include at least one id')
            elif subcategory_id:
                subcategory_ids = [subcategory_id]
        except ValueError as exc:
            return error_response(str(exc), status=status.HTTP_400_BAD_REQUEST)

        list_request = ListProductsRequest(
            category_id=category_id,
            subcategory_ids=subcategory_ids,
            subcategory_slugs=subcategory_slugs,
            search=search,
            availability=availability,
            spec_filters=spec_filters,
            page=page,
            page_size=page_size,
            include_detailed_specs=include_detailed_specs,
        )

        cacheable = _is_default_product_list_cacheable(
            category_id=list_request.category_id,
            subcategory_ids=list_request.subcategory_ids,
            subcategory_slugs=list_request.subcategory_slugs,
            search=list_request.search,
            availability=list_request.availability,
            spec_filters=list_request.spec_filters,
            page=list_request.page,
            page_size=list_request.page_size,
            include_detailed_specs=list_request.include_detailed_specs,
        )

        cache_state = 'skip'
        if cacheable:
            cache_key = product_list_default_cache_key()
            cached_payload = cache.get(cache_key)
            if cached_payload is not None:
                total_ms = (time.perf_counter() - t0) * 1000.0
                logger.info(
                    'products.list cache=hit total_ms=%.1f page=%d page_size=%d',
                    total_ms,
                    list_request.page,
                    list_request.page_size,
                )
                return _with_public_cache_headers(
                    success_response(cached_payload)
                )
            cache_state = 'miss'

        t_db_start = time.perf_counter()
        resolved_subcategory_ids = catalog_hot_reads.resolve_list_subcategory_ids(
            _category_repo,
            list_request.category_id,
            list_request.subcategory_slugs,
            list_request.subcategory_ids,
        )

        qs = catalog_hot_reads.build_product_list_queryset(
            category_id=list_request.category_id,
            subcategory_ids=resolved_subcategory_ids,
            search=list_request.search,
            availability=list_request.availability,
            spec_filters=list_request.spec_filters,
        )
        rows, total = catalog_hot_reads.paginate_product_queryset(
            qs, list_request.page, list_request.page_size
        )

        specifications_map = None
        if list_request.include_detailed_specs:
            ids = [p.id for p in rows if p.id]
            specifications_map = _product_repo.get_specifications_batch(
                ids, include_detailed=True
            )

        t_after_db = time.perf_counter()

        items = catalog_hot_reads.product_rows_to_card_dicts(
            rows,
            specifications_map,
            list_request.include_detailed_specs,
        )

        total_pages = (
            (total + list_request.page_size - 1) // list_request.page_size
            if list_request.page_size
            else 0
        )
        has_next = list_request.page < total_pages if total_pages else False
        has_previous = list_request.page > 1

        payload = PaginatedProductResponseSerializer({
            'items': items,
            'total': total,
            'page': list_request.page,
            'page_size': list_request.page_size,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_previous': has_previous,
        }).data

        t_after_serialize = time.perf_counter()

        db_ms = (t_after_db - t_db_start) * 1000.0
        serialize_ms = (t_after_serialize - t_after_db) * 1000.0
        total_ms = (t_after_serialize - t0) * 1000.0
        logger.info(
            'products.list cache=%s total_ms=%.1f db_ms=%.1f serialize_ms=%.1f '
            'items=%d page=%d page_size=%d total_rows=%d',
            cache_state,
            total_ms,
            db_ms,
            serialize_ms,
            len(items),
            list_request.page,
            list_request.page_size,
            total,
        )

        if cacheable:
            cache.set(
                product_list_default_cache_key(),
                payload,
                timeout=settings.CACHE_TIMEOUT,
            )

        resp = success_response(payload)
        if cacheable:
            return _with_public_cache_headers(resp)
        return resp


class ProductDetailView(APIView):
    """Product detail view."""
    permission_classes = [AllowAny]
    
    def get(self, request, product_id):
        """Get product by ID."""
        try:
            include_detailed_specs = (
                request.query_params.get('include_detailed_specs', 'true').lower()
                in ('true', '1', 'yes')
            )
            cache_key = product_detail_cache_key(
                product_id=product_id,
                include_detailed_specs=include_detailed_specs,
            )
            cached_payload = cache.get(cache_key)
            if cached_payload is not None:
                return _with_public_cache_headers(success_response(cached_payload))

            product = catalog_hot_reads.load_product_detail_orm(int(product_id))
            specs_map = _product_repo.get_specifications_batch(
                [int(product_id)], include_detailed=include_detailed_specs
            )
            specs_simple, specs_detailed = specs_map.get(
                int(product_id), ({}, [])
            )
            payload = ProductResponseSerializer(
                catalog_hot_reads.build_product_detail_payload(
                    product, specs_simple, specs_detailed
                )
            ).data
            cache.set(cache_key, payload, timeout=settings.CACHE_TIMEOUT)
            return _with_public_cache_headers(success_response(payload))
        except NotFoundError as e:
            return error_response(str(e), status=status.HTTP_404_NOT_FOUND)

