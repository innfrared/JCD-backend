"""Homepage views."""
import logging

from django.conf import settings
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from rest_framework import status

from src.application.homepage.use_cases import GetHomePageSectionsUseCase
from src.application.homepage.ports import HomeSectionRepository, ProductCardRepository
from src.infrastructure.db.repositories.homepage_repo import (
    DjangoHomeSectionRepository, DjangoProductCardRepository
)
from interfaces.rest.homepage.serializers import HomePageResponseSerializer
from interfaces.rest.shared.responses import success_response, error_response
from src.infrastructure.cache.storefront_cache import homepage_cache_key


# Initialize dependencies
_home_section_repo: HomeSectionRepository = DjangoHomeSectionRepository()
_product_card_repo: ProductCardRepository = DjangoProductCardRepository()
logger = logging.getLogger(__name__)


class HomePageView(APIView):
    """Homepage view."""
    authentication_classes = []  # No authentication for public endpoints
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'homepage'
    
    def get(self, request):
        """Get homepage sections."""
        try:
            cached_payload = cache.get(homepage_cache_key())
            if cached_payload is not None:
                return success_response(cached_payload)

            use_case = GetHomePageSectionsUseCase(
                _home_section_repo,
                _product_card_repo
            )
            response = use_case.execute()
            payload = HomePageResponseSerializer(response).data
            cache.set(homepage_cache_key(), payload, timeout=settings.CACHE_TIMEOUT)
            return success_response(payload)
        except Exception:
            logger.exception('Failed to build homepage response')
            return error_response(
                'Internal server error',
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

