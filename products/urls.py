"""
Product URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet

app_name = "products"

# Create router and register viewset
router = DefaultRouter()
router.register(r"", ProductViewSet, basename="product")

urlpatterns = [
    path("", include(router.urls)),
]
