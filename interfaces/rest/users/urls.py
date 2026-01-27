"""User URLs."""
from django.urls import path
from interfaces.rest.users.views import (
    RegisterView, LoginView, RefreshTokenView, MeView,
    AddressListView, AddressDetailView, SetDefaultAddressView
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/refresh/', RefreshTokenView.as_view(), name='refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('addresses/', AddressListView.as_view(), name='address-list'),
    path('addresses/<int:address_id>/', AddressDetailView.as_view(), name='address-detail'),
    path('addresses/<int:address_id>/set-default/', SetDefaultAddressView.as_view(), name='address-set-default'),
]
