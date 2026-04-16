"""Catalog views."""
from django.conf import settings
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status

from src.application.catalog.use_cases import (
    ListCategoriesUseCase,
    ListCategoriesWithSubcategoriesUseCase,
    ListSubcategoriesByCategoryUseCase,
    ListProductsUseCase,
    GetProductUseCase,
)
from src.application.catalog.ports import CategoryRepository, ProductRepository
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
)


# Initialize dependencies
_category_repo: CategoryRepository = DjangoCategoryRepository()
_product_repo: ProductRepository = DjangoProductRepository()


class CategoryListView(APIView):
    """Category list view."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """List categories."""
        cached_payload = cache.get(categories_cache_key())
        if cached_payload is not None:
            return success_response(cached_payload)

        use_case = ListCategoriesUseCase(_category_repo)
        categories = use_case.execute()
        payload = [
            CategoryResponseSerializer(cat).data for cat in categories
        ]
        cache.set(categories_cache_key(), payload, timeout=settings.CACHE_TIMEOUT)
        return success_response(payload)


class CategoryWithSubcategoriesListView(APIView):
    """Category list with subcategories view."""
    permission_classes = [AllowAny]

    def get(self, request):
        """List categories with subcategories."""
        cached_payload = cache.get(categories_all_cache_key())
        if cached_payload is not None:
            return success_response(cached_payload)

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
        return success_response(payload)


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


class ProductListView(APIView):
    """Product list view."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """List products."""
        from src.application.catalog.dto import ListProductsRequest
        
        # Parse query parameters
        category_id = request.query_params.get('category_id')
        subcategory_id = request.query_params.get('subcategory_id')
        subcategory_ids_param = request.query_params.get('subcategory_ids')
        subcategory_slug = request.query_params.get('subcategory_slug')
        subcategory_slugs_param = request.query_params.get('subcategory_slugs')
        search = request.query_params.get('search')
        availability = request.query_params.get('availability')
        page = max(int(request.query_params.get('page', 1)), 1)
        requested_page_size = int(request.query_params.get('page_size', 20))
        page_size = min(max(requested_page_size, 1), 60)
        include_detailed_specs = (
            request.query_params.get('include_detailed_specs', 'false').lower()
            in ('true', '1', 'yes')
        )
        
        # Parse spec filters (e.g., ?spec_material=leather&spec_strap_length_cm=110)
        spec_filters = {}
        for key, value in request.query_params.items():
            if key.startswith('spec_'):
                spec_key = key[5:]  # Remove 'spec_' prefix
                spec_filters[spec_key] = value
        
        subcategory_ids = None
        subcategory_slugs = None
        if subcategory_ids_param:
            subcategory_ids = [
                int(val) for val in subcategory_ids_param.split(',')
                if val.strip().isdigit()
            ]
        elif subcategory_id:
            subcategory_ids = [int(subcategory_id)]

        if subcategory_slugs_param:
            subcategory_slugs = [
                val.strip() for val in subcategory_slugs_param.split(',')
                if val.strip()
            ]
        elif subcategory_slug:
            subcategory_slugs = [subcategory_slug.strip()]

        list_request = ListProductsRequest(
            category_id=int(category_id) if category_id else None,
            subcategory_ids=subcategory_ids,
            subcategory_slugs=subcategory_slugs,
            search=search,
            availability=availability,
            spec_filters=spec_filters if spec_filters else None,
            page=page,
            page_size=page_size,
            include_detailed_specs=include_detailed_specs,
        )
        
        use_case = ListProductsUseCase(_product_repo, _category_repo)
        result = use_case.execute(list_request)
        
        return success_response(PaginatedProductResponseSerializer({
            'items': result.items,
            'total': result.total,
            'page': result.page,
            'page_size': result.page_size,
            'total_pages': result.total_pages,
            'has_next': result.has_next,
            'has_previous': result.has_previous
        }).data)


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
                return success_response(cached_payload)

            use_case = GetProductUseCase(_product_repo, _category_repo)
            product = use_case.execute(product_id)
            payload = ProductResponseSerializer(product).data
            cache.set(cache_key, payload, timeout=settings.CACHE_TIMEOUT)
            return success_response(payload)
        except NotFoundError as e:
            return error_response(str(e), status=status.HTTP_404_NOT_FOUND)

