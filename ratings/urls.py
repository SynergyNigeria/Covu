"""
Rating URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RatingViewSet

app_name = "ratings"

# Create router and register viewset
router = DefaultRouter()
router.register(r"", RatingViewSet, basename="rating")

urlpatterns = [
    path("", include(router.urls)),
]
