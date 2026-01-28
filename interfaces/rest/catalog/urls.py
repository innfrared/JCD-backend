"""Catalog URLs."""
from django.urls import path
from interfaces.rest.catalog.views import (
    CategoryListView,
    CategoryWithSubcategoriesListView,
    SubcategoryListByCategoryView,
    ProductListView,
    ProductDetailView,
)

urlpatterns = [
    path('categories', CategoryListView.as_view(), name='category-list'),
    path(
        'categories/all',
        CategoryWithSubcategoriesListView.as_view(),
        name='category-list-with-subcategories',
    ),
    path(
        'categories/<int:category_id>/subcategories',
        SubcategoryListByCategoryView.as_view(),
        name='subcategory-list-by-category',
    ),
    path('products', ProductListView.as_view(), name='product-list'),
    path('products/<int:product_id>', ProductDetailView.as_view(), name='product-detail'),
]
