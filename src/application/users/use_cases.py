"""User use cases."""
from typing import Optional, Tuple
from datetime import datetime
from src.domain.users.entities import User, Address
from src.domain.users.rules import ensure_user_is_active, ensure_user_owns_address
from src.domain.shared.exceptions import NotFoundError, ValidationError
from src.application.users.ports import UserRepository, AddressRepository
from src.application.users.dto import (
    RegisterRequest, LoginRequest, UserResponse, UpdateProfileRequest,
    AddressRequest, AddressResponse
)
from src.application.shared.auth import TokenPair


def _user_to_response(user: User) -> UserResponse:
    """Map User entity to response DTO."""
    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        is_active=user.is_active,
        created_at=user.created_at
    )


def _address_to_response(address: Address) -> AddressResponse:
    """Map Address entity to response DTO."""
    return AddressResponse(
        id=address.id,
        label=address.label,
        full_name=address.full_name,
        phone=address.phone,
        country=address.country,
        city=address.city,
        street=address.street,
        apartment=address.apartment,
        postal_code=address.postal_code,
        is_default=address.is_default,
        created_at=address.created_at
    )


class RegisterUserUseCase:
    """Register user use case."""
    
    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher,
        token_service
    ):
        self.user_repo = user_repo
        self.password_hasher = password_hasher
        self.token_service = token_service
    
    def execute(self, request: RegisterRequest) -> Tuple[UserResponse, TokenPair]:
        """Execute register user."""
        # Check if user exists
        existing = self.user_repo.get_by_email(request.email)
        if existing:
            raise ValidationError("User with this email already exists")
        
        # Hash password
        password_hash = self.password_hasher.hash(request.password)
        
        # Create user
        user = User(
            id=None,
            email=request.email,
            password_hash=password_hash,
            first_name=request.first_name,
            last_name=request.last_name,
            phone=request.phone,
            is_active=True,
            is_staff=False,
            created_at=datetime.utcnow()
        )
        
        user = self.user_repo.create(user)
        
        # Generate tokens
        tokens = self.token_service.generate_tokens(user.id, user.email, user.is_staff)
        
        return (
            _user_to_response(user),
            tokens
        )


class LoginUserUseCase:
    """Login user use case."""
    
    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher,
        token_service
    ):
        self.user_repo = user_repo
        self.password_hasher = password_hasher
        self.token_service = token_service
    
    def execute(self, request: LoginRequest) -> TokenPair:
        """Execute login."""
        user = self.user_repo.get_by_email(request.email)
        if not user:
            raise ValidationError("Invalid email or password")
        
        ensure_user_is_active(user)
        
        if not self.password_hasher.verify(request.password, user.password_hash):
            raise ValidationError("Invalid email or password")
        
        return self.token_service.generate_tokens(user.id, user.email, user.is_staff)


class GetMeUseCase:
    """Get current user use case."""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    def execute(self, user_id: int) -> UserResponse:
        """Execute get me."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        return _user_to_response(user)


class UpdateProfileUseCase:
    """Update profile use case."""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    def execute(self, user_id: int, request: UpdateProfileRequest) -> UserResponse:
        """Execute update profile."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Update fields
        if request.first_name is not None:
            user.first_name = request.first_name
        if request.last_name is not None:
            user.last_name = request.last_name
        if request.phone is not None:
            user.phone = request.phone
        
        user = self.user_repo.update(user)
        
        return _user_to_response(user)


class ListAddressesUseCase:
    """List addresses use case."""
    
    def __init__(self, address_repo: AddressRepository):
        self.address_repo = address_repo
    
    def execute(self, user_id: int) -> list[AddressResponse]:
        """Execute list addresses."""
        addresses = self.address_repo.get_by_user_id(user_id)
        return [_address_to_response(addr) for addr in addresses]


class CreateAddressUseCase:
    """Create address use case."""
    
    def __init__(self, address_repo: AddressRepository):
        self.address_repo = address_repo
    
    def execute(self, user_id: int, request: AddressRequest) -> AddressResponse:
        """Execute create address."""
        address = Address(
            id=None,
            user_id=user_id,
            label=request.label,
            full_name=request.full_name,
            phone=request.phone,
            country=request.country,
            city=request.city,
            street=request.street,
            apartment=request.apartment,
            postal_code=request.postal_code,
            is_default=request.is_default,
            created_at=datetime.utcnow()
        )
        
        address = self.address_repo.create(address)
        
        # If this is default, unset others
        if request.is_default:
            self.address_repo.set_default(user_id, address.id)
        
        return _address_to_response(address)


class UpdateAddressUseCase:
    """Update address use case."""
    
    def __init__(self, address_repo: AddressRepository):
        self.address_repo = address_repo
    
    def execute(self, user_id: int, address_id: int, request: AddressRequest) -> AddressResponse:
        """Execute update address."""
        address = self.address_repo.get_by_id(address_id)
        if not address:
            raise NotFoundError("Address not found")
        
        ensure_user_owns_address(user_id, address.user_id)
        
        # Update fields
        address.label = request.label
        address.full_name = request.full_name
        address.phone = request.phone
        address.country = request.country
        address.city = request.city
        address.street = request.street
        address.apartment = request.apartment
        address.postal_code = request.postal_code
        address.is_default = request.is_default
        
        address = self.address_repo.update(address)
        
        # If this is default, unset others
        if request.is_default:
            self.address_repo.set_default(user_id, address.id)
        
        return _address_to_response(address)


class DeleteAddressUseCase:
    """Delete address use case."""
    
    def __init__(self, address_repo: AddressRepository):
        self.address_repo = address_repo
    
    def execute(self, user_id: int, address_id: int) -> None:
        """Execute delete address."""
        address = self.address_repo.get_by_id(address_id)
        if not address:
            raise NotFoundError("Address not found")
        
        ensure_user_owns_address(user_id, address.user_id)
        
        self.address_repo.delete(address_id)


class SetDefaultAddressUseCase:
    """Set default address use case."""
    
    def __init__(self, address_repo: AddressRepository):
        self.address_repo = address_repo
    
    def execute(self, user_id: int, address_id: int) -> None:
        """Execute set default address."""
        address = self.address_repo.get_by_id(address_id)
        if not address:
            raise NotFoundError("Address not found")
        
        ensure_user_owns_address(user_id, address.user_id)
        
        self.address_repo.set_default(user_id, address_id)
