"""Guardrails for hot catalog read path query counts (regression detection)."""
from decimal import Decimal

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from src.infrastructure.db.models.catalog import Category, Product, Subcategory


class CatalogHotReadsPerfTests(TestCase):
    """Baseline: list/detail stay bounded vs N+1 explosion."""

    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            id=2000,
            name='PerfCat',
            slug='perf-cat',
        )
        cls.sub = Subcategory.objects.create(
            id=2100,
            category=cls.category,
            name='PerfSub',
            slug='perf-sub',
        )
        cls.product = Product.objects.create(
            name='PerfBag',
            brand='Jasmine',
            price=Decimal('99.00'),
            availability=Product.AvailabilityChoices.IN_STOCK,
            category=cls.category,
            currency=Product.CurrencyChoices.USD,
            variant_image='https://example.com/img.jpg',
        )
        cls.product.subcategories.set([cls.sub])

    def setUp(self):
        self.client = APIClient()

    def test_product_list_query_count_bounded(self):
        with CaptureQueriesContext(connection) as ctx:
            r = self.client.get('/api/products?page=1&page_size=20')
        self.assertEqual(r.status_code, 200)
        self.assertLessEqual(len(ctx.captured_queries), 12)

    def test_product_detail_query_count_bounded(self):
        with CaptureQueriesContext(connection) as ctx:
            r = self.client.get(f'/api/products/{self.product.id}')
        self.assertEqual(r.status_code, 200)
        self.assertLessEqual(len(ctx.captured_queries), 20)
