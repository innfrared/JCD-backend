"""Homepage URLs."""
from django.urls import path
from interfaces.rest.homepage.views import HomePageView

urlpatterns = [
    path('', HomePageView.as_view(), name='homepage'),
]

