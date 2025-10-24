"""
Store URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StoreViewSet

app_name = "stores"

# Create router and register viewset
router = DefaultRouter()
router.register(r"", StoreViewSet, basename="store")

urlpatterns = [
    path("", include(router.urls)),
]
