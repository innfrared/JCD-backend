from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from src.infrastructure.db.models.catalog import Category, Product


@override_settings(
    AUTH_COOKIE_SECURE=False,
    AUTH_COOKIE_SAMESITE='Lax',
    AUTH_COOKIE_DOMAIN=None,
)
class AuthCookieTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='password123',
        )

    def _login(self):
        response = self.client.post(
            '/api/auth/login',
            data={'email': 'test@example.com', 'password': 'password123'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        return response

    def _csrf_header(self):
        csrf_cookie = self.client.cookies.get(settings.CSRF_COOKIE_NAME)
        return {'HTTP_X_CSRFTOKEN': csrf_cookie.value} if csrf_cookie else {}

    def test_login_sets_auth_cookies(self):
        response = self._login()
        access_cookie = response.cookies[settings.AUTH_ACCESS_COOKIE_NAME]
        refresh_cookie = response.cookies[settings.AUTH_REFRESH_COOKIE_NAME]

        self.assertTrue(access_cookie['httponly'])
        self.assertTrue(refresh_cookie['httponly'])
        self.assertFalse(access_cookie['secure'])
        self.assertFalse(refresh_cookie['secure'])
        self.assertEqual(access_cookie['samesite'], settings.AUTH_COOKIE_SAMESITE)
        self.assertEqual(refresh_cookie['samesite'], settings.AUTH_COOKIE_SAMESITE)
        self.assertEqual(access_cookie['path'], settings.AUTH_ACCESS_COOKIE_PATH)
        self.assertEqual(refresh_cookie['path'], settings.AUTH_REFRESH_COOKIE_PATH)

    def test_refresh_rotates_refresh_cookie(self):
        self._login()
        old_refresh = self.client.cookies[settings.AUTH_REFRESH_COOKIE_NAME].value
        response = self.client.post('/api/auth/refresh', **self._csrf_header())
        self.assertEqual(response.status_code, 200)
        new_refresh = response.cookies[settings.AUTH_REFRESH_COOKIE_NAME].value
        self.assertNotEqual(old_refresh, new_refresh)

    def test_logout_clears_cookies(self):
        self._login()
        response = self.client.post('/api/auth/logout', **self._csrf_header())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.cookies[settings.AUTH_ACCESS_COOKIE_NAME].value,
            '',
        )
        self.assertEqual(
            response.cookies[settings.AUTH_REFRESH_COOKIE_NAME].value,
            '',
        )

    def test_me_requires_authentication(self):
        response = self.client.get('/api/auth/me')
        self.assertEqual(response.status_code, 401)

        self._login()
        response = self.client.get('/api/auth/me')
        self.assertEqual(response.status_code, 200)

    def test_invalid_refresh_clears_cookies(self):
        self._login()
        self.client.cookies[settings.AUTH_REFRESH_COOKIE_NAME] = 'invalid'
        response = self.client.post('/api/auth/refresh', **self._csrf_header())
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.cookies[settings.AUTH_ACCESS_COOKIE_NAME].value,
            '',
        )
        self.assertEqual(
            response.cookies[settings.AUTH_REFRESH_COOKIE_NAME].value,
            '',
        )

    def test_trailing_slash_auth_routes_are_not_supported(self):
        self.assertEqual(
            self.client.post(
                '/api/auth/login/',
                data={'email': 'test@example.com', 'password': 'password123'},
                format='json',
            ).status_code,
            404,
        )
        self._login()
        self.assertEqual(
            self.client.post('/api/auth/refresh/', **self._csrf_header()).status_code,
            404,
        )
        self.assertEqual(
            self.client.post('/api/auth/logout/', **self._csrf_header()).status_code,
            404,
        )
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 404)


class RouteNormalizationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name='Bags', slug='bags')
        self.product = Product.objects.create(
            name='Test Bag',
            price=Decimal('120.00'),
            availability=Product.AvailabilityChoices.IN_STOCK,
            category=self.category,
            currency=Product.CurrencyChoices.USD,
        )

    def test_slashless_public_routes_resolve(self):
        response = self.client.get('/api/categories')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/api/categories/all')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            f'/api/categories/{self.category.id}/subcategories'
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/api/products')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f'/api/products/{self.product.id}')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/api/home')
        self.assertEqual(response.status_code, 200)

    def test_trailing_slash_public_routes_return_404(self):
        self.assertEqual(self.client.get('/api/categories/').status_code, 404)
        self.assertEqual(self.client.get('/api/categories/all/').status_code, 404)
        self.assertEqual(
            self.client.get(
                f'/api/categories/{self.category.id}/subcategories/'
            ).status_code,
            404,
        )
        self.assertEqual(self.client.get('/api/products/').status_code, 404)
        self.assertEqual(
            self.client.get(f'/api/products/{self.product.id}/').status_code,
            404,
        )
        self.assertEqual(self.client.get('/api/home/').status_code, 404)
