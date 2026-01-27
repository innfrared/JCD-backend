"""Shared permissions."""
from rest_framework import permissions


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """Allow read-only access to unauthenticated users."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class IsStaffOrReadOnly(permissions.BasePermission):
    """Allow write access only to staff users."""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.is_staff

