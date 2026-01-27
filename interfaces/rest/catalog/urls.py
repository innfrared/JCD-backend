"""Catalog URLs."""
from django.urls import path
from interfaces.rest.catalog.views import (
    CategoryListView, ProductListView, ProductDetailView
)

urlpatterns = [
    path('categories', CategoryListView.as_view(), name='category-list'),
    path('products', ProductListView.as_view(), name='product-list'),
    path('products/<int:product_id>', ProductDetailView.as_view(), name='product-detail'),
]
