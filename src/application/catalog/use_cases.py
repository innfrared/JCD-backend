"""Catalog use cases."""
from typing import List
from src.domain.shared.exceptions import NotFoundError
from src.domain.catalog.entities import Product
from src.application.catalog.ports import CategoryRepository, ProductRepository
from src.application.catalog.dto import (
    CategoryResponse,
    CategoryWithSubcategoriesResponse,
    SubcategoryResponse,
    ProductResponse,
    VariantProductPreview,
    ListProductsRequest,
)
from src.application.shared.pagination import PaginatedResult


def _product_to_response(
    product_repo: ProductRepository,
    category_repo: CategoryRepository,
    product: Product
) -> ProductResponse:
    """Build ProductResponse from domain entity with related data."""
    specs_simple, specs_detailed = product_repo.get_specifications(product.id)
    
    # Get category and subcategories
    category = category_repo.get_by_id(product.category_id) if product.category_id else None
    category_response = CategoryResponse(
        id=category.id,
        name=category.name,
        slug=category.slug,
        created_at=category.created_at
    ) if category else None
    
    subcategory_responses: List[SubcategoryResponse] = []
    for subcategory_id in product.subcategory_ids:
        subcategory = category_repo.get_subcategory_by_id(subcategory_id)
        if subcategory:
            subcategory_responses.append(SubcategoryResponse(
                id=subcategory.id,
                category_id=subcategory.category_id,
                name=subcategory.name,
                slug=subcategory.slug,
                description=subcategory.description,
                created_at=subcategory.created_at
            ))
    
    # Get variant group products if product belongs to a variant group
    variant_previews = []
    if product.variant_group_id:
        variant_products = product_repo.get_variant_group_products(
            product.variant_group_id,
            exclude_product_id=product.id
        )
        # Products are already ordered by repository (default first, then by id)
        
        variant_previews = [
            VariantProductPreview(
                id=v.id,
                name=v.name,
                price=str(v.price),
                availability=v.availability.value,
                image=v.variant_image,
                color_name=v.variant_color_name,
                color_palette=v.variant_color_palette
            )
            for v in variant_products
        ]
    
    return ProductResponse(
        id=product.id,
        name=product.name,
        brand=product.brand,
        price=str(product.price),
        price_new=str(product.price_new) if product.price_new else None,
        price_old=str(product.price_old) if product.price_old else None,
        availability=product.availability.value,
        category_id=product.category_id,
        subcategory_ids=product.subcategory_ids,
        category=category_response,
        subcategories=subcategory_responses,
        currency=product.currency.value,
        variant_group_id=product.variant_group_id,
        variant_color_name=product.variant_color_name,
        variant_color_palette=product.variant_color_palette,
        variant_image=product.variant_image,
        created_at=product.created_at,
        updated_at=product.updated_at,
        variants=variant_previews,
        specifications=specs_simple,
        specifications_detailed=specs_detailed
    )


class ListCategoriesUseCase:
    """List categories use case."""
    
    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo
    
    def execute(self) -> List[CategoryResponse]:
        """Execute list categories."""
        categories = self.category_repo.get_all()
        return [
            CategoryResponse(
                id=cat.id,
                name=cat.name,
                slug=cat.slug,
                created_at=cat.created_at
            )
            for cat in categories
        ]


class ListSubcategoriesByCategoryUseCase:
    """List subcategories for a category."""

    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    def execute(self, category_id: int) -> List[SubcategoryResponse]:
        """Execute list subcategories."""
        subcategories = self.category_repo.get_subcategories_by_category(category_id)
        return [
            SubcategoryResponse(
                id=sub.id,
                category_id=sub.category_id,
                name=sub.name,
                slug=sub.slug,
                description=sub.description,
                created_at=sub.created_at
            )
            for sub in subcategories
        ]


class ListCategoriesWithSubcategoriesUseCase:
    """List categories with subcategories."""

    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    def execute(self) -> List[CategoryWithSubcategoriesResponse]:
        """Execute list categories with subcategories."""
        categories = self.category_repo.get_all()
        results: List[CategoryWithSubcategoriesResponse] = []

        for category in categories:
            subcategories = self.category_repo.get_subcategories_by_category(
                category.id
            )
            results.append(CategoryWithSubcategoriesResponse(
                id=category.id,
                name=category.name,
                slug=category.slug,
                created_at=category.created_at,
                subcategories=[
                    SubcategoryResponse(
                        id=sub.id,
                        category_id=sub.category_id,
                        name=sub.name,
                        slug=sub.slug,
                        description=sub.description,
                        created_at=sub.created_at
                    )
                    for sub in subcategories
                ],
            ))

        return results


class ListProductsUseCase:
    """List products use case."""
    
    def __init__(self, product_repo: ProductRepository, category_repo: CategoryRepository):
        self.product_repo = product_repo
        self.category_repo = category_repo
    
    def execute(self, request: ListProductsRequest) -> PaginatedResult[ProductResponse]:
        """Execute list products."""
        products, total = self.product_repo.get_all(
            category_id=request.category_id,
            subcategory_ids=request.subcategory_ids,
            search=request.search,
            availability=request.availability,
            spec_filters=request.spec_filters,
            page=request.page,
            page_size=request.page_size
        )
        
        # Convert to response DTOs (without variants for list view - only in detail)
        product_responses = []
        for product in products:
            specs_simple, specs_detailed = self.product_repo.get_specifications(product.id)
            
            # Get category and subcategories
            category = self.category_repo.get_by_id(product.category_id) if product.category_id else None
            category_response = CategoryResponse(
                id=category.id,
                name=category.name,
                slug=category.slug,
                created_at=category.created_at
            ) if category else None
            
            subcategory_responses: List[SubcategoryResponse] = []
            for subcategory_id in product.subcategory_ids:
                subcategory = self.category_repo.get_subcategory_by_id(subcategory_id)
                if subcategory:
                    subcategory_responses.append(SubcategoryResponse(
                        id=subcategory.id,
                        category_id=subcategory.category_id,
                        name=subcategory.name,
                        slug=subcategory.slug,
                        description=subcategory.description,
                        created_at=subcategory.created_at
                    ))
            
            product_responses.append(ProductResponse(
                id=product.id,
                name=product.name,
                brand=product.brand,
                price=str(product.price),
                price_new=str(product.price_new) if product.price_new else None,
                price_old=str(product.price_old) if product.price_old else None,
                availability=product.availability.value,
                category_id=product.category_id,
                subcategory_ids=product.subcategory_ids,
                category=category_response,
                subcategories=subcategory_responses,
                currency=product.currency.value,
                variant_group_id=product.variant_group_id,
                variant_color_name=product.variant_color_name,
                variant_color_palette=product.variant_color_palette,
                variant_image=product.variant_image,
                created_at=product.created_at,
                updated_at=product.updated_at,
                variants=[],  # No variants in list view
                specifications=specs_simple,
                specifications_detailed=specs_detailed
            ))
        
        total_pages = (total + request.page_size - 1) // request.page_size
        
        return PaginatedResult(
            items=product_responses,
            total=total,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages
        )


class GetProductUseCase:
    """Get product use case."""
    
    def __init__(self, product_repo: ProductRepository, category_repo: CategoryRepository):
        self.product_repo = product_repo
        self.category_repo = category_repo
    
    def execute(self, product_id: int) -> ProductResponse:
        """Execute get product."""
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise NotFoundError("Product not found")
        
        return _product_to_response(self.product_repo, self.category_repo, product)
