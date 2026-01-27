"""Homepage views."""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status

from src.application.homepage.use_cases import GetHomePageSectionsUseCase
from src.application.homepage.ports import HomeSectionRepository, ProductCardRepository
from src.infrastructure.db.repositories.homepage_repo import (
    DjangoHomeSectionRepository, DjangoProductCardRepository
)
from interfaces.rest.homepage.serializers import HomePageResponseSerializer
from interfaces.rest.shared.responses import success_response, error_response


# Initialize dependencies
_home_section_repo: HomeSectionRepository = DjangoHomeSectionRepository()
_product_card_repo: ProductCardRepository = DjangoProductCardRepository()


class HomePageView(APIView):
    """Homepage view."""
    authentication_classes = []  # No authentication for public endpoints
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get homepage sections."""
        try:
            use_case = GetHomePageSectionsUseCase(
                _home_section_repo,
                _product_card_repo
            )
            response = use_case.execute()
            return success_response(
                HomePageResponseSerializer(response).data
            )
        except Exception as e:
            return error_response(
                str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

