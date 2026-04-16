"""Catalog use cases (taxonomy). Product list/detail hot paths: catalog_hot_reads."""
from typing import List
from src.application.catalog.ports import CategoryRepository
from src.application.catalog.dto import (
    CategoryResponse,
    CategoryWithSubcategoriesResponse,
    SubcategoryResponse,
)
from src.application.catalog.taxonomy_contract import bags_subcategory_aliases


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
