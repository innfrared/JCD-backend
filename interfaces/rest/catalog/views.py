"""Catalog views."""
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


# Initialize dependencies
_category_repo: CategoryRepository = DjangoCategoryRepository()
_product_repo: ProductRepository = DjangoProductRepository()


class CategoryListView(APIView):
    """Category list view."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """List categories."""
        use_case = ListCategoriesUseCase(_category_repo)
        categories = use_case.execute()
        return success_response([
            CategoryResponseSerializer(cat).data for cat in categories
        ])


class CategoryWithSubcategoriesListView(APIView):
    """Category list with subcategories view."""
    permission_classes = [AllowAny]

    def get(self, request):
        """List categories with subcategories."""
        use_case = ListCategoriesWithSubcategoriesUseCase(_category_repo)
        categories = use_case.execute()
        return success_response([
            CategoryWithSubcategoriesResponseSerializer(cat).data
            for cat in categories
        ])


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
        search = request.query_params.get('search')
        availability = request.query_params.get('availability')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        # Parse spec filters (e.g., ?spec_material=leather&spec_strap_length_cm=110)
        spec_filters = {}
        for key, value in request.query_params.items():
            if key.startswith('spec_'):
                spec_key = key[5:]  # Remove 'spec_' prefix
                spec_filters[spec_key] = value
        
        list_request = ListProductsRequest(
            category_id=int(category_id) if category_id else None,
            subcategory_id=int(subcategory_id) if subcategory_id else None,
            search=search,
            availability=availability,
            spec_filters=spec_filters if spec_filters else None,
            page=page,
            page_size=page_size
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
            use_case = GetProductUseCase(_product_repo, _category_repo)
            product = use_case.execute(product_id)
            return success_response(ProductResponseSerializer(product).data)
        except NotFoundError as e:
            return error_response(str(e), status=status.HTTP_404_NOT_FOUND)

