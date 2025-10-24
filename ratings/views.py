"""
Rating Views

API endpoints for rating management:
- POST /api/ratings/ - Submit rating for confirmed order
- GET /api/ratings/ - List all ratings (filterable by store)
- GET /api/ratings/{id}/ - Get rating detail
- GET /api/ratings/store/{store_id}/stats/ - Get store rating statistics
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count, Q
from decimal import Decimal

from .models import Rating
from .serializers import (
    RatingSerializer,
    CreateRatingSerializer,
    StoreRatingStatsSerializer,
)
from stores.models import Store


class RatingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for rating management.

    Endpoints:
    - POST /api/ratings/ - Create rating (buyer only, confirmed orders)
    - GET /api/ratings/ - List ratings (filterable by store)
    - GET /api/ratings/{id}/ - Get rating details
    - GET /api/ratings/store/{store_id}/stats/ - Get store rating stats
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "create":
            return CreateRatingSerializer
        return RatingSerializer

    def get_queryset(self):
        """
        Get ratings filtered by query params.

        Query params:
        - store: Filter by store ID
        - approved_only: Show only approved ratings (default: true for public)
        """
        queryset = Rating.objects.select_related(
            "buyer", "order", "order__product", "store"
        ).all()

        # Filter by store
        store_id = self.request.query_params.get("store")
        if store_id:
            queryset = queryset.filter(store_id=store_id)

        # Filter by approval status (default to approved only for public listings)
        approved_only = self.request.query_params.get("approved_only", "true").lower()
        if approved_only == "true":
            queryset = queryset.filter(is_approved=True)

        return queryset.order_by("-created_at")

    def create(self, request, *args, **kwargs):
        """
        Create a rating for a confirmed order.

        Request body:
        {
            "order_id": "uuid",
            "rating": 1-5,
            "review": "optional text"
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rating = serializer.save()

        # Return full rating details
        output_serializer = RatingSerializer(rating)

        return Response(
            {
                "status": "success",
                "message": "Rating submitted successfully",
                "rating": output_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    def list(self, request, *args, **kwargs):
        """
        List ratings with optional filtering.

        Query params:
        - store: Filter by store ID
        - approved_only: true/false (default: true)
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response({"count": queryset.count(), "results": serializer.data})

    @action(detail=False, methods=["get"], url_path="store/(?P<store_id>[^/.]+)/stats")
    def store_stats(self, request, store_id=None):
        """
        Get rating statistics for a store.

        Returns:
        - Average rating
        - Total ratings
        - Rating distribution (5-star, 4-star, etc.)
        - Percentage distribution

        URL: GET /api/ratings/store/{store_id}/stats/
        """
        try:
            store = Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            return Response(
                {"error": "Store not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get all approved ratings for this store
        ratings = Rating.objects.filter(store=store, is_approved=True)
        total_ratings = ratings.count()

        if total_ratings == 0:
            return Response(
                {
                    "store_id": str(store.id),
                    "store_name": store.name,
                    "average_rating": "0.00",
                    "total_ratings": 0,
                    "five_star_count": 0,
                    "four_star_count": 0,
                    "three_star_count": 0,
                    "two_star_count": 0,
                    "one_star_count": 0,
                    "five_star_percent": "0.00",
                    "four_star_percent": "0.00",
                    "three_star_percent": "0.00",
                    "two_star_percent": "0.00",
                    "one_star_percent": "0.00",
                }
            )

        # Calculate average rating
        avg_rating = ratings.aggregate(avg=Avg("rating"))["avg"] or Decimal("0.00")

        # Count ratings by star level
        five_star = ratings.filter(rating=5).count()
        four_star = ratings.filter(rating=4).count()
        three_star = ratings.filter(rating=3).count()
        two_star = ratings.filter(rating=2).count()
        one_star = ratings.filter(rating=1).count()

        # Calculate percentages
        five_percent = (five_star / total_ratings * 100) if total_ratings > 0 else 0
        four_percent = (four_star / total_ratings * 100) if total_ratings > 0 else 0
        three_percent = (three_star / total_ratings * 100) if total_ratings > 0 else 0
        two_percent = (two_star / total_ratings * 100) if total_ratings > 0 else 0
        one_percent = (one_star / total_ratings * 100) if total_ratings > 0 else 0

        stats = {
            "store_id": str(store.id),
            "store_name": store.name,
            "average_rating": f"{avg_rating:.2f}",
            "total_ratings": total_ratings,
            "five_star_count": five_star,
            "four_star_count": four_star,
            "three_star_count": three_star,
            "two_star_count": two_star,
            "one_star_count": one_star,
            "five_star_percent": f"{five_percent:.2f}",
            "four_star_percent": f"{four_percent:.2f}",
            "three_star_percent": f"{three_percent:.2f}",
            "two_star_percent": f"{two_percent:.2f}",
            "one_star_percent": f"{one_percent:.2f}",
        }

        return Response(stats)

    @action(detail=False, methods=["get"], url_path="my-ratings")
    def my_ratings(self, request):
        """
        Get current user's submitted ratings.

        URL: GET /api/ratings/my-ratings/
        """
        ratings = (
            Rating.objects.filter(buyer=request.user)
            .select_related("order", "order__product", "store")
            .order_by("-created_at")
        )

        serializer = self.get_serializer(ratings, many=True)

        return Response({"count": ratings.count(), "results": serializer.data})
