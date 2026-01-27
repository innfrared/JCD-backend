"""User views."""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import status

from src.application.users.use_cases import (
    RegisterUserUseCase, LoginUserUseCase, GetMeUseCase, UpdateProfileUseCase,
    ListAddressesUseCase, CreateAddressUseCase, UpdateAddressUseCase,
    DeleteAddressUseCase, SetDefaultAddressUseCase
)
from src.application.users.ports import UserRepository, AddressRepository
from src.infrastructure.db.repositories.users_repo import (
    DjangoUserRepository, DjangoAddressRepository
)
from src.infrastructure.services.password_hasher import PasswordHasher
from src.infrastructure.services.token_service import TokenService
from src.domain.shared.exceptions import DomainException, ValidationError, NotFoundError
from interfaces.rest.users.serializers import (
    RegisterSerializer, LoginSerializer, TokenResponseSerializer,
    UserResponseSerializer, UpdateProfileSerializer,
    AddressRequestSerializer, AddressResponseSerializer
)
from interfaces.rest.shared.responses import success_response, error_response


# Initialize dependencies
_user_repo: UserRepository = DjangoUserRepository()
_address_repo: AddressRepository = DjangoAddressRepository()
_password_hasher = PasswordHasher()
_token_service = TokenService()


class RegisterView(APIView):
    """Register view."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Register a new user."""
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                'Validation failed',
                status=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )
        
        try:
            use_case = RegisterUserUseCase(_user_repo, _password_hasher, _token_service)
            user_response, tokens = use_case.execute(serializer.validated_data)
            
            return success_response({
                'user': UserResponseSerializer(user_response).data,
                'tokens': TokenResponseSerializer(tokens).data
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return error_response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except DomainException as e:
            return error_response(str(e), status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Login view."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Login user."""
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                'Validation failed',
                status=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )
        
        try:
            use_case = LoginUserUseCase(_user_repo, _password_hasher, _token_service)
            tokens = use_case.execute(serializer.validated_data)
            
            return success_response({
                'tokens': TokenResponseSerializer(tokens).data
            })
        except ValidationError as e:
            return error_response(str(e), status=status.HTTP_401_UNAUTHORIZED)
        except DomainException as e:
            return error_response(str(e), status=status.HTTP_401_UNAUTHORIZED)


class RefreshTokenView(TokenRefreshView):
    """Refresh token view."""
    permission_classes = [AllowAny]


class MeView(APIView):
    """Get current user view."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user."""
        try:
            use_case = GetMeUseCase(_user_repo)
            user_response = use_case.execute(request.user.id)
            return success_response(UserResponseSerializer(user_response).data)
        except NotFoundError as e:
            return error_response(str(e), status=status.HTTP_404_NOT_FOUND)
    
    def patch(self, request):
        """Update current user profile."""
        serializer = UpdateProfileSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                'Validation failed',
                status=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )
        
        try:
            use_case = UpdateProfileUseCase(_user_repo)
            user_response = use_case.execute(request.user.id, serializer.validated_data)
            return success_response(UserResponseSerializer(user_response).data)
        except NotFoundError as e:
            return error_response(str(e), status=status.HTTP_404_NOT_FOUND)
        except DomainException as e:
            return error_response(str(e), status=status.HTTP_400_BAD_REQUEST)


class AddressListView(APIView):
    """Address list view."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List addresses."""
        use_case = ListAddressesUseCase(_address_repo)
        addresses = use_case.execute(request.user.id)
        return success_response([
            AddressResponseSerializer(addr).data for addr in addresses
        ])
    
    def post(self, request):
        """Create address."""
        serializer = AddressRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                'Validation failed',
                status=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )
        
        try:
            use_case = CreateAddressUseCase(_address_repo)
            address_response = use_case.execute(request.user.id, serializer.validated_data)
            return success_response(
                AddressResponseSerializer(address_response).data,
                status=status.HTTP_201_CREATED
            )
        except DomainException as e:
            return error_response(str(e), status=status.HTTP_400_BAD_REQUEST)


class AddressDetailView(APIView):
    """Address detail view."""
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, address_id):
        """Update address."""
        serializer = AddressRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                'Validation failed',
                status=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )
        
        try:
            use_case = UpdateAddressUseCase(_address_repo)
            address_response = use_case.execute(
                request.user.id,
                address_id,
                serializer.validated_data
            )
            return success_response(AddressResponseSerializer(address_response).data)
        except NotFoundError as e:
            return error_response(str(e), status=status.HTTP_404_NOT_FOUND)
        except DomainException as e:
            return error_response(str(e), status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, address_id):
        """Delete address."""
        try:
            use_case = DeleteAddressUseCase(_address_repo)
            use_case.execute(request.user.id, address_id)
            return success_response({'message': 'Address deleted'}, status=status.HTTP_204_NO_CONTENT)
        except NotFoundError as e:
            return error_response(str(e), status=status.HTTP_404_NOT_FOUND)
        except DomainException as e:
            return error_response(str(e), status=status.HTTP_400_BAD_REQUEST)


class SetDefaultAddressView(APIView):
    """Set default address view."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, address_id):
        """Set default address."""
        try:
            use_case = SetDefaultAddressUseCase(_address_repo)
            use_case.execute(request.user.id, address_id)
            return success_response({'message': 'Default address updated'})
        except NotFoundError as e:
            return error_response(str(e), status=status.HTTP_404_NOT_FOUND)
        except DomainException as e:
            return error_response(str(e), status=status.HTTP_400_BAD_REQUEST)

