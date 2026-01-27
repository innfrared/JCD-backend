"""User repository implementation."""
from typing import Optional, List
from datetime import datetime
from src.domain.users.entities import User, Address
from src.application.users.ports import UserRepository, AddressRepository
from src.infrastructure.db.models.users import User as UserModel, Address as AddressModel


class DjangoUserRepository(UserRepository):
    """Django user repository implementation."""
    
    def create(self, user: User) -> User:
        """Create a new user."""
        user_model = UserModel(
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            is_active=user.is_active,
            is_staff=user.is_staff
        )
        # Set password hash directly (already hashed by use case)
        user_model.password = user.password_hash
        user_model.save()
        return self._to_domain(user_model)
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        try:
            user_model = UserModel.objects.get(id=user_id)
            return self._to_domain(user_model)
        except UserModel.DoesNotExist:
            return None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            user_model = UserModel.objects.get(email=email)
            return self._to_domain(user_model)
        except UserModel.DoesNotExist:
            return None
    
    def update(self, user: User) -> User:
        """Update user."""
        user_model = UserModel.objects.get(id=user.id)
        user_model.first_name = user.first_name
        user_model.last_name = user.last_name
        user_model.phone = user.phone
        user_model.save()
        return self._to_domain(user_model)
    
    def _to_domain(self, user_model: UserModel) -> User:
        """Convert Django model to domain entity."""
        return User(
            id=user_model.id,
            email=user_model.email,
            password_hash=user_model.password,  # Django stores hashed password
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            phone=user_model.phone,
            is_active=user_model.is_active,
            is_staff=user_model.is_staff,
            created_at=user_model.created_at
        )


class DjangoAddressRepository(AddressRepository):
    """Django address repository implementation."""
    
    def create(self, address: Address) -> Address:
        """Create a new address."""
        address_model = AddressModel.objects.create(
            user_id=address.user_id,
            label=address.label,
            full_name=address.full_name,
            phone=address.phone,
            country=address.country,
            city=address.city,
            street=address.street,
            apartment=address.apartment,
            postal_code=address.postal_code,
            is_default=address.is_default
        )
        return self._to_domain(address_model)
    
    def get_by_id(self, address_id: int) -> Optional[Address]:
        """Get address by ID."""
        try:
            address_model = AddressModel.objects.get(id=address_id)
            return self._to_domain(address_model)
        except AddressModel.DoesNotExist:
            return None
    
    def get_by_user_id(self, user_id: int) -> List[Address]:
        """Get all addresses for a user."""
        address_models = AddressModel.objects.filter(user_id=user_id)
        return [self._to_domain(addr) for addr in address_models]
    
    def update(self, address: Address) -> Address:
        """Update address."""
        address_model = AddressModel.objects.get(id=address.id)
        address_model.label = address.label
        address_model.full_name = address.full_name
        address_model.phone = address.phone
        address_model.country = address.country
        address_model.city = address.city
        address_model.street = address.street
        address_model.apartment = address.apartment
        address_model.postal_code = address.postal_code
        address_model.is_default = address.is_default
        address_model.save()
        return self._to_domain(address_model)
    
    def delete(self, address_id: int) -> None:
        """Delete address."""
        AddressModel.objects.filter(id=address_id).delete()
    
    def set_default(self, user_id: int, address_id: int) -> None:
        """Set default address for user."""
        # Unset all defaults for user
        AddressModel.objects.filter(user_id=user_id).update(is_default=False)
        # Set new default
        AddressModel.objects.filter(id=address_id, user_id=user_id).update(is_default=True)
    
    def _to_domain(self, address_model: AddressModel) -> Address:
        """Convert Django model to domain entity."""
        return Address(
            id=address_model.id,
            user_id=address_model.user_id,
            label=address_model.label,
            full_name=address_model.full_name,
            phone=address_model.phone,
            country=address_model.country,
            city=address_model.city,
            street=address_model.street,
            apartment=address_model.apartment,
            postal_code=address_model.postal_code,
            is_default=address_model.is_default,
            created_at=address_model.created_at
        )

