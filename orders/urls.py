"""
Order URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet

app_name = "orders"

# Create router and register viewset
router = DefaultRouter()
router.register(r"", OrderViewSet, basename="order")

urlpatterns = [
    path("", include(router.urls)),
]
