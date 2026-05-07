from decimal import Decimal

from django.test import TestCase
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.core.cache import cache
from rest_framework.test import APIClient

from src.infrastructure.db.models.catalog import (
    Attribute,
    Category,
    Product,
    ProductAttributeValue,
    ProductVariant,
    ProductVariantImage,
    Subcategory,
    VariantGroup,
)
from src.infrastructure.cache.storefront_cache import product_detail_cache_key


class CatalogContractTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.legacy_category = Category.objects.create(
            id=1,
            name='Bags',
            slug='bags-old-1',
        )
        cls.category = Category.objects.create(
            id=1000,
            name='Bags',
            slug='bags',
        )

        cls.crossbody = Subcategory.objects.create(
            id=1100,
            category=cls.category,
            name='Crossbody Bags',
            slug='crossbody-bags',
            description='Crossbody styles',
        )
        cls.shoulder = Subcategory.objects.create(
            id=1200,
            category=cls.category,
            name='Shoulder Bags',
            slug='shoulder-bags',
            description='Shoulder styles',
        )
        cls.handbags = Subcategory.objects.create(
            id=1300,
            category=cls.category,
            name='Handbags',
            slug='handbags',
            description='Top handle styles',
        )
        cls.clutches = Subcategory.objects.create(
            id=1400,
            category=cls.category,
            name='Clutches',
            slug='clutches',
            description=None,
        )
        cls.legacy_handbags = Subcategory.objects.create(
            id=1,
            category=cls.category,
            name='Handbags',
            slug='handbags-old-1',
        )

        cls.product_crossbody = Product.objects.create(
            name='Aurora',
            brand='Jasmine',
            price=Decimal('120.00'),
            availability=Product.AvailabilityChoices.IN_STOCK,
            category=cls.category,
            currency=Product.CurrencyChoices.USD,
        )
        cls.product_crossbody.subcategories.set([cls.crossbody, cls.handbags])

        cls.product_shoulder = Product.objects.create(
            name='Soleil',
            brand='Jasmine',
            price=Decimal('140.00'),
            availability=Product.AvailabilityChoices.OUT_OF_STOCK,
            category=cls.category,
            currency=Product.CurrencyChoices.USD,
        )
        cls.product_shoulder.subcategories.set([cls.shoulder])

        cls.product_clutch = Product.objects.create(
            name='Nocturne',
            brand='Atelier',
            price=Decimal('160.00'),
            availability=Product.AvailabilityChoices.IN_STOCK,
            category=cls.category,
            currency=Product.CurrencyChoices.USD,
        )
        cls.product_clutch.subcategories.set([cls.clutches])

        cls.variant_group = VariantGroup.objects.create(
            name='Aurora Family',
            slug='aurora-family',
            default_product=cls.product_crossbody,
        )
        cls.product_crossbody.variant_group = cls.variant_group
        cls.product_crossbody.variant_color_name = 'Navy'
        cls.product_crossbody.variant_color_palette = '#1f2a44'
        cls.product_crossbody.save(
            update_fields=[
                'variant_group',
                'variant_color_name',
                'variant_color_palette',
            ]
        )
        cls.product_shoulder.variant_group = cls.variant_group
        cls.product_shoulder.variant_color_name = 'Sand'
        cls.product_shoulder.variant_color_palette = '#c2b280'
        cls.product_shoulder.save(
            update_fields=[
                'variant_group',
                'variant_color_name',
                'variant_color_palette',
            ]
        )

        cls.material_attribute = Attribute.objects.create(
            scope_type=Attribute.ScopeTypeChoices.CATEGORY,
            scope_id=cls.category.id,
            key='material',
            label='Material',
            data_type=Attribute.DataTypeChoices.TEXT,
        )
        ProductAttributeValue.objects.create(
            product=cls.product_crossbody,
            attribute=cls.material_attribute,
            value_text='Leather',
        )
        ProductAttributeValue.objects.create(
            product=cls.product_shoulder,
            attribute=cls.material_attribute,
            value_text='Canvas',
        )
        ProductAttributeValue.objects.create(
            product=cls.product_clutch,
            attribute=cls.material_attribute,
            value_text='Satin',
        )

        # Deterministic image ordering: sort_order first, then id.
        ProductVariant.objects.create(
            product=cls.product_crossbody,
            name='Color',
            value='Navy',
            image_url='https://images.example.com/aurora-secondary.jpg',
            sort_order=2,
        )
        ProductVariant.objects.create(
            product=cls.product_crossbody,
            name='Color',
            value='Navy',
            image_url='https://images.example.com/aurora-primary.jpg',
            sort_order=1,
        )

        # Additional rows make N+1 regressions visible in query-count tests.
        for idx in range(4, 19):
            product = Product.objects.create(
                name=f'Carry {idx}',
                brand='Jasmine',
                price=Decimal('100.00'),
                availability=Product.AvailabilityChoices.IN_STOCK,
                category=cls.category,
                currency=Product.CurrencyChoices.USD,
            )
            product.subcategories.set([cls.clutches])
            ProductAttributeValue.objects.create(
                product=product,
                attribute=cls.material_attribute,
                value_text='Leather',
            )

    def setUp(self):
        self.client = APIClient()

    def test_categories_endpoint_hides_legacy_rows(self):
        response = self.client.get('/api/categories')
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]['id'], self.category.id)
        self.assertEqual(payload[0]['slug'], 'bags')
        self.assertNotIn('-old-', payload[0]['slug'])

    def test_categories_all_returns_only_canonical_taxonomy(self):
        response = self.client.get('/api/categories/all')
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(len(payload), 1)

        category = payload[0]
        self.assertEqual(category['slug'], 'bags')
        self.assertEqual(
            {subcategory['slug'] for subcategory in category['subcategories']},
            {'crossbody-bags', 'shoulder-bags', 'handbags', 'clutches'},
        )
        for subcategory in category['subcategories']:
            self.assertEqual(
                set(subcategory.keys()),
                {
                    'id',
                    'category_id',
                    'name',
                    'slug',
                    'description',
                    'image',
                    'created_at',
                    'slug_aliases',
                },
            )
        self.assertTrue(
            all('-old-' not in subcategory['slug']
                for subcategory in category['subcategories'])
        )
        descriptions_by_slug = {
            subcategory['slug']: subcategory['description']
            for subcategory in category['subcategories']
        }
        self.assertEqual(
            descriptions_by_slug['crossbody-bags'],
            'Crossbody styles',
        )
        self.assertIsNone(descriptions_by_slug['clutches'])
        aliases_by_slug = {
            subcategory['slug']: set(subcategory['slug_aliases'])
            for subcategory in category['subcategories']
        }
        self.assertIn('crossbody', aliases_by_slug['crossbody-bags'])
        self.assertIn('evening', aliases_by_slug['clutches'])

    def test_category_subcategories_endpoint_hides_legacy_rows(self):
        response = self.client.get(f'/api/categories/{self.category.id}/subcategories')
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(
            {subcategory['slug'] for subcategory in payload},
            {'crossbody-bags', 'shoulder-bags', 'handbags', 'clutches'},
        )

    def test_products_response_shape_is_stable(self):
        response = self.client.get('/api/products', {'page': 1, 'page_size': 2})
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(
            set(payload.keys()),
            {
                'items',
                'total',
                'page',
                'page_size',
                'total_pages',
                'has_next',
                'has_previous',
            },
        )
        self.assertEqual(payload['page'], 1)
        self.assertEqual(payload['page_size'], 2)
        self.assertGreaterEqual(payload['total'], 3)

        item = payload['items'][0]
        self.assertIn('category_id', item)
        self.assertIn('subcategory_ids', item)
        self.assertIn('image_url', item)
        self.assertNotIn('category', item)
        self.assertNotIn('subcategories', item)
        self.assertNotIn('specifications_detailed', item)

    def test_products_default_is_card_grade_only(self):
        response = self.client.get('/api/products', {'page': 1, 'page_size': 5})
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        for item in payload['items']:
            self.assertNotIn('specifications', item)
            self.assertNotIn('specifications_detailed', item)
            self.assertNotIn('variants', item)
            self.assertNotIn('variants_detailed', item)
            self.assertNotIn('category', item)
            self.assertNotIn('subcategories', item)

    def test_products_include_detailed_specs_flag(self):
        response = self.client.get('/api/products', {
            'page': 1,
            'page_size': 5,
            'include_detailed_specs': 'true',
        })
        self.assertEqual(response.status_code, 200)

        item = response.json()['items'][0]
        self.assertIn('specifications', item)
        self.assertIn('specifications_detailed', item)

    def test_product_detail_primary_image_is_deterministic(self):
        response = self.client.get(f'/api/products/{self.product_crossbody.id}')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            payload['variant_image'],
            'https://images.example.com/aurora-primary.jpg',
        )
        self.assertIn('variants_detailed', payload)
        self.assertEqual(len(payload['variants_detailed']), 2)
        variants_by_sort_order = {
            v['sort_order']: v for v in payload['variants_detailed']
        }
        self.assertEqual(variants_by_sort_order[1]['image_url'], 'https://images.example.com/aurora-primary.jpg')
        self.assertEqual(variants_by_sort_order[2]['image_url'], 'https://images.example.com/aurora-secondary.jpg')
        # Strict contract: images must always exist (empty when no gallery rows).
        for v in payload['variants_detailed']:
            self.assertIn('images', v)
            self.assertEqual(v['images'], [])
            self.assertIn('image_url', v)
            self.assertIn('sort_order', v)
        self.assertIn('variant_ids', payload)
        self.assertEqual(
            payload['variant_ids'],
            [self.product_crossbody.id, self.product_shoulder.id],
        )
        self.assertIn('variant_options', payload)
        self.assertEqual(len(payload['variant_options']), 2)
        self.assertEqual(payload['variant_options'][0]['id'], self.product_crossbody.id)
        self.assertTrue(payload['variant_options'][0]['is_current'])
        self.assertEqual(payload['variant_options'][1]['id'], self.product_shoulder.id)
        self.assertFalse(payload['variant_options'][1]['is_current'])

    def test_product_detail_variant_images_are_isolated_and_ordered(self):
        # Load deterministic variant ordering: sort_order then id.
        variants = list(
            ProductVariant.objects.filter(product=self.product_crossbody).order_by(
                'sort_order', 'id'
            )
        )
        self.assertEqual(len(variants), 2)
        v_sort_1, v_sort_2 = variants[0], variants[1]

        # Variant sort_order=1 gets two gallery images with an explicit primary.
        ProductVariantImage.objects.create(
            variant=v_sort_1,
            image_url='https://images.example.com/v1-secondary.jpg',
            alt='v1 secondary',
            sort_order=2,
            is_primary=False,
        )
        ProductVariantImage.objects.create(
            variant=v_sort_1,
            image_url='https://images.example.com/v1-primary.jpg',
            alt='v1 primary',
            sort_order=1,
            is_primary=True,
        )

        # Variant sort_order=2 gets one gallery image.
        ProductVariantImage.objects.create(
            variant=v_sort_2,
            image_url='https://images.example.com/v2-primary.jpg',
            alt='v2 primary',
            sort_order=1,
            is_primary=True,
        )

        # Cache can contain a stale PDP payload from other tests; evict explicitly.
        cache.delete(
            product_detail_cache_key(
                product_id=self.product_crossbody.id,
                include_detailed_specs=True,
            )
        )
        response = self.client.get(f'/api/products/{self.product_crossbody.id}')
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        variants_by_id = {v['id']: v for v in payload['variants_detailed']}

        v1_payload = variants_by_id[v_sort_1.id]
        self.assertEqual(v1_payload['image_url'], 'https://images.example.com/v1-primary.jpg')
        self.assertEqual(len(v1_payload['images']), 2)
        self.assertEqual(
            [img['url'] for img in v1_payload['images']],
            [
                'https://images.example.com/v1-primary.jpg',
                'https://images.example.com/v1-secondary.jpg',
            ],
        )
        self.assertTrue(v1_payload['images'][0]['is_primary'])

        v2_payload = variants_by_id[v_sort_2.id]
        self.assertEqual(v2_payload['image_url'], 'https://images.example.com/v2-primary.jpg')
        self.assertEqual(len(v2_payload['images']), 1)
        self.assertEqual(v2_payload['images'][0]['url'], 'https://images.example.com/v2-primary.jpg')

        # Isolation check: images don't leak between variants.
        self.assertNotIn(
            'https://images.example.com/v1-primary.jpg',
            {img['url'] for img in v2_payload['images']},
        )

    def test_product_detail_variant_image_url_primary_preference_and_fallback(self):
        # Get a single variant to test behavior.
        variant = list(
            ProductVariant.objects.filter(product=self.product_crossbody).order_by(
                'sort_order', 'id'
            )
        )[0]

        # Case 1: no primary => image_url should use first by sort_order.
        ProductVariantImage.objects.create(
            variant=variant,
            image_url='https://images.example.com/noprimary-2.jpg',
            alt='no primary second',
            sort_order=2,
            is_primary=False,
        )
        ProductVariantImage.objects.create(
            variant=variant,
            image_url='https://images.example.com/noprimary-1.jpg',
            alt='no primary first',
            sort_order=1,
            is_primary=False,
        )

        cache.delete(
            product_detail_cache_key(
                product_id=self.product_crossbody.id,
                include_detailed_specs=False,
            )
        )
        response = self.client.get(
            f'/api/products/{self.product_crossbody.id}',
            {'include_detailed_specs': 'false'},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        v_payload = next(v for v in payload['variants_detailed'] if v['id'] == variant.id)
        self.assertEqual(v_payload['image_url'], 'https://images.example.com/noprimary-1.jpg')

        # Case 2: primary exists => image_url should switch to the primary.
        ProductVariantImage.objects.create(
            variant=variant,
            image_url='https://images.example.com/hasprimary.jpg',
            alt='has primary',
            sort_order=0,
            is_primary=True,
        )

        cache.delete(
            product_detail_cache_key(
                product_id=self.product_crossbody.id,
                include_detailed_specs=False,
            )
        )
        response = self.client.get(
            f'/api/products/{self.product_crossbody.id}',
            {'include_detailed_specs': 'false'},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        v_payload = next(v for v in payload['variants_detailed'] if v['id'] == variant.id)
        self.assertEqual(v_payload['image_url'], 'https://images.example.com/hasprimary.jpg')

    def test_product_detail_query_count_guardrail(self):
        # Ensure there are enough gallery rows to expose N+1 patterns if present.
        variants = list(
            ProductVariant.objects.filter(product=self.product_crossbody).order_by(
                'sort_order', 'id'
            )
        )
        self.assertEqual(len(variants), 2)

        for v in variants:
            for sort_order in range(1, 5):
                ProductVariantImage.objects.create(
                    variant=v,
                    image_url=f'https://images.example.com/guard-{v.id}-{sort_order}.jpg',
                    alt='guard',
                    sort_order=sort_order,
                    is_primary=(sort_order == 1),
                )

        cache.delete(
            product_detail_cache_key(
                product_id=self.product_crossbody.id,
                include_detailed_specs=False,
            )
        )
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(
                f'/api/products/{self.product_crossbody.id}',
                {'include_detailed_specs': 'false'},
            )
        self.assertEqual(response.status_code, 200)
        # Should stay bounded: base product + prefetch variants + prefetch images (+ siblings + specs, though specs are disabled).
        self.assertLessEqual(len(queries), 12)

    def test_products_filter_by_category_id(self):
        response = self.client.get('/api/products', {
            'category_id': self.category.id,
            'page': 1,
            'page_size': 50,
        })
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json()['total'], 3)

    def test_products_filter_by_subcategory_id(self):
        response = self.client.get('/api/products', {
            'subcategory_id': self.crossbody.id,
            'page': 1,
            'page_size': 50,
        })
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertGreaterEqual(payload['total'], 1)
        self.assertIn(
            self.product_crossbody.id,
            {item['id'] for item in payload['items']},
        )

    def test_products_filter_by_subcategory_slug_alias(self):
        response = self.client.get('/api/products', {
            'subcategory_slug': 'evening',
            'category_id': self.category.id,
            'page': 1,
            'page_size': 50,
        })
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreaterEqual(payload['total'], 1)
        self.assertIn(
            self.product_clutch.id,
            {item['id'] for item in payload['items']},
        )

    def test_products_filter_by_subcategory_ids(self):
        response = self.client.get('/api/products', {
            'subcategory_ids': f'{self.crossbody.id},{self.shoulder.id}',
            'page': 1,
            'page_size': 50,
        })
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertGreaterEqual(payload['total'], 2)
        self.assertTrue(
            {self.product_crossbody.id, self.product_shoulder.id}.issubset(
                {item['id'] for item in payload['items']}
            )
        )

    def test_products_filter_by_search(self):
        response = self.client.get('/api/products', {
            'search': 'Aurora',
            'page': 1,
            'page_size': 50,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['total'], 1)

    def test_products_filter_by_availability(self):
        response = self.client.get('/api/products', {
            'availability': Product.AvailabilityChoices.OUT_OF_STOCK,
            'page': 1,
            'page_size': 50,
        })
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload['total'], 1)
        self.assertEqual(payload['items'][0]['id'], self.product_shoulder.id)

    def test_products_filter_by_spec_prefix(self):
        response = self.client.get('/api/products', {
            'spec_material': 'Leather',
            'page': 1,
            'page_size': 50,
        })
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertGreaterEqual(payload['total'], 1)
        self.assertIn(
            self.product_crossbody.id,
            {item['id'] for item in payload['items']},
        )

    def test_categories_all_query_count_guardrail(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get('/api/categories/all')
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(queries), 4)

    def test_products_listing_query_count_guardrail(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get('/api/products', {'page': 1, 'page_size': 20})
        self.assertEqual(response.status_code, 200)
        # Guardrail against per-product enrichment queries.
        self.assertLessEqual(len(queries), 6)
