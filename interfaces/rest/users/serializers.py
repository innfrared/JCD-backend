"""User serializers."""
from rest_framework import serializers
from src.application.users.dto import (
    RegisterRequest, LoginRequest, UserResponse, UpdateProfileRequest,
    AddressRequest, AddressResponse
)


class RegisterSerializer(serializers.Serializer):
    """Register serializer."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_null=True)
    last_name = serializers.CharField(required=False, allow_null=True)
    phone = serializers.CharField(required=False, allow_null=True)
    
    def to_internal_value(self, data):
        """Convert to RegisterRequest DTO."""
        validated = super().to_internal_value(data)
        return RegisterRequest(
            email=validated['email'],
            password=validated['password'],
            first_name=validated.get('first_name'),
            last_name=validated.get('last_name'),
            phone=validated.get('phone')
        )


class LoginSerializer(serializers.Serializer):
    """Login serializer."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def to_internal_value(self, data):
        """Convert to LoginRequest DTO."""
        validated = super().to_internal_value(data)
        return LoginRequest(
            email=validated['email'],
            password=validated['password']
        )


class TokenResponseSerializer(serializers.Serializer):
    """Token response serializer."""
    access = serializers.CharField()
    refresh = serializers.CharField()


class UserResponseSerializer(serializers.Serializer):
    """User response serializer."""
    id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField(allow_null=True)
    last_name = serializers.CharField(allow_null=True)
    phone = serializers.CharField(allow_null=True)
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()


class UpdateProfileSerializer(serializers.Serializer):
    """Update profile serializer."""
    first_name = serializers.CharField(required=False, allow_null=True)
    last_name = serializers.CharField(required=False, allow_null=True)
    phone = serializers.CharField(required=False, allow_null=True)
    
    def to_internal_value(self, data):
        """Convert to UpdateProfileRequest DTO."""
        validated = super().to_internal_value(data)
        return UpdateProfileRequest(
            first_name=validated.get('first_name'),
            last_name=validated.get('last_name'),
            phone=validated.get('phone')
        )


class AddressRequestSerializer(serializers.Serializer):
    """Address request serializer."""
    label = serializers.CharField()
    full_name = serializers.CharField()
    phone = serializers.CharField()
    country = serializers.CharField()
    city = serializers.CharField()
    street = serializers.CharField()
    apartment = serializers.CharField(required=False, allow_null=True)
    postal_code = serializers.CharField()
    is_default = serializers.BooleanField(default=False)
    
    def to_internal_value(self, data):
        """Convert to AddressRequest DTO."""
        validated = super().to_internal_value(data)
        return AddressRequest(
            label=validated['label'],
            full_name=validated['full_name'],
            phone=validated['phone'],
            country=validated['country'],
            city=validated['city'],
            street=validated['street'],
            apartment=validated.get('apartment'),
            postal_code=validated['postal_code'],
            is_default=validated.get('is_default', False)
        )


class AddressResponseSerializer(serializers.Serializer):
    """Address response serializer."""
    id = serializers.IntegerField()
    label = serializers.CharField()
    full_name = serializers.CharField()
    phone = serializers.CharField()
    country = serializers.CharField()
    city = serializers.CharField()
    street = serializers.CharField()
    apartment = serializers.CharField(allow_null=True)
    postal_code = serializers.CharField()
    is_default = serializers.BooleanField()
    created_at = serializers.DateTimeField()

