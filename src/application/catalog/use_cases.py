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
    ProductCardResponse,
    ProductVariantDetailResponse,
    VariantSwitchOption,
    VariantProductPreview,
    ListProductsRequest,
)
from src.application.shared.pagination import PaginatedResult
from src.application.catalog.taxonomy_contract import (
    bags_subcategory_aliases,
    expand_bags_query_aliases,
)


def _subcategory_to_response(subcategory, is_bags_category: bool) -> SubcategoryResponse:
    """Convert domain subcategory to API response contract."""
    aliases = None
    if is_bags_category:
        aliases = bags_subcategory_aliases(subcategory.slug)
    return SubcategoryResponse(
        id=subcategory.id,
        category_id=subcategory.category_id,
        name=subcategory.name,
        slug=subcategory.slug,
        description=subcategory.description,
        image=subcategory.image,
        created_at=subcategory.created_at,
        slug_aliases=aliases,
    )


def _product_to_response(
    product_repo: ProductRepository,
    category_repo: CategoryRepository,
    product: Product
) -> ProductResponse:
    """Build ProductResponse from domain entity with related data."""
    product_ids = [product.id] if product.id else []
    specs_map = product_repo.get_specifications_batch(
        product_ids,
        include_detailed=True,
    )
    specs_simple, specs_detailed = specs_map.get(product.id, ({}, []))

    category_map = category_repo.get_by_ids(
        [product.category_id] if product.category_id else []
    )
    category = category_map.get(product.category_id) if product.category_id else None
    category_response = CategoryResponse(
        id=category.id,
        name=category.name,
        slug=category.slug,
        image=category.image,
        created_at=category.created_at
    ) if category else None
    
    subcategories_map = category_repo.get_subcategories_by_ids(
        product.subcategory_ids
    )
    is_bags_category = (category.slug == 'bags') if category else False
    raw_subcategories = [
        subcategory
        for subcategory_id in product.subcategory_ids
        if (subcategory := subcategories_map.get(subcategory_id))
    ]
    subcategory_responses = [
        _subcategory_to_response(subcategory, is_bags_category)
        for subcategory in raw_subcategories
    ]
    
    # Get variant group products for switcher + backward-compatible previews.
    variant_previews = []
    variant_ids = [product.id]
    variant_options = [
        VariantSwitchOption(
            id=product.id,
            image=product.variant_image,
            color_name=product.variant_color_name,
            color_palette=product.variant_color_palette,
            is_current=True,
        )
    ]
    if product.variant_group_id:
        variant_group_products = product_repo.get_variant_group_products(
            product.variant_group_id,
            exclude_product_id=None,
        )
        variant_ids = [v.id for v in variant_group_products]
        variant_options = [
            VariantSwitchOption(
                id=v.id,
                image=v.variant_image,
                color_name=v.variant_color_name,
                color_palette=v.variant_color_palette,
                is_current=(v.id == product.id),
            )
            for v in variant_group_products
        ]
        variant_products = [
            v for v in variant_group_products
            if v.id != product.id
        ]
        # Products are already ordered by repository (default first, then by id).
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

    variant_details = [
        ProductVariantDetailResponse(
            id=variant.id,
            folder=variant.folder,
            color=variant.color,
            material=variant.material,
            cord_diameter=variant.cord_diameter,
            cord_type=variant.cord_type,
            description=variant.description,
            care=variant.care,
            handles=variant.handles,
            image_url=variant.image_url,
            sort_order=variant.sort_order,
        )
        for variant in product_repo.get_product_variants(product.id)
    ]
    
    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
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
        variant_ids=variant_ids,
        variant_options=variant_options,
        created_at=product.created_at,
        updated_at=product.updated_at,
        variants=variant_previews,
        variants_detailed=variant_details,
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
                image=cat.image,
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
        category = self.category_repo.get_by_id(category_id)
        is_bags_category = bool(category and category.slug == 'bags')
        subcategories = self.category_repo.get_subcategories_by_category(category_id)
        return [
            _subcategory_to_response(sub, is_bags_category)
            for sub in subcategories
        ]


class ListCategoriesWithSubcategoriesUseCase:
    """List categories with subcategories."""

    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    def execute(self) -> List[CategoryWithSubcategoriesResponse]:
        """Execute list categories with subcategories."""
        categories = self.category_repo.get_all()
        category_ids = [category.id for category in categories if category.id]
        subcategories_map = self.category_repo.get_subcategories_by_category_ids(
            category_ids
        )
        results: List[CategoryWithSubcategoriesResponse] = []

        for category in categories:
            subcategories = subcategories_map.get(category.id, [])
            is_bags_category = category.slug == 'bags'
            results.append(CategoryWithSubcategoriesResponse(
                id=category.id,
                name=category.name,
                slug=category.slug,
                image=category.image,
                created_at=category.created_at,
                subcategories=[
                    _subcategory_to_response(sub, is_bags_category)
                    for sub in subcategories
                ],
            ))

        return results


class ListProductsUseCase:
    """List products use case."""
    
    def __init__(self, product_repo: ProductRepository, category_repo: CategoryRepository):
        self.product_repo = product_repo
        self.category_repo = category_repo
    
    def execute(self, request: ListProductsRequest) -> PaginatedResult[ProductCardResponse]:
        """Execute list products."""
        resolved_subcategory_ids = request.subcategory_ids
        if request.subcategory_slugs:
            expanded_slugs = list(request.subcategory_slugs)
            if request.category_id:
                category = self.category_repo.get_by_id(request.category_id)
                if category and category.slug == 'bags':
                    expanded_slugs = expand_bags_query_aliases(expanded_slugs)
            subcategories = self.category_repo.get_subcategories_by_slugs(
                slugs=expanded_slugs,
                category_id=request.category_id,
            )
            resolved_subcategory_ids = [sub.id for sub in subcategories]

        products, total = self.product_repo.get_all(
            category_id=request.category_id,
            subcategory_ids=resolved_subcategory_ids,
            search=request.search,
            availability=request.availability,
            spec_filters=request.spec_filters,
            page=request.page,
            page_size=request.page_size
        )
        
        # Optional detail-grade specs stay opt-in and off by default.
        specifications_map = {}
        if request.include_detailed_specs:
            product_ids = [product.id for product in products if product.id]
            specifications_map = self.product_repo.get_specifications_batch(
                product_ids,
                include_detailed=True,
            )

        product_responses = [
            ProductCardResponse(
                id=product.id,
                name=product.name,
                brand=product.brand,
                price=str(product.price),
                price_new=str(product.price_new) if product.price_new else None,
                price_old=str(product.price_old) if product.price_old else None,
                availability=product.availability.value,
                currency=product.currency.value,
                image_url=product.variant_image,
                category_id=product.category_id,
                subcategory_ids=product.subcategory_ids,
                created_at=product.created_at,
                updated_at=product.updated_at,
                specifications=specifications_map.get(product.id, ({}, []))[0]
                if request.include_detailed_specs else None,
                specifications_detailed=specifications_map.get(product.id, ({}, []))[1]
                if request.include_detailed_specs else None,
            )
            for product in products
        ]
        
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
