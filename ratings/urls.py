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
    # Explicit store stats endpoint
    path(
        "store/<uuid:store_id>/stats/",
        RatingViewSet.as_view({"get": "store_stats"}),
        name="store-stats",
    ),
    path("", include(router.urls)),
]
