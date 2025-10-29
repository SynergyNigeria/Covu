"""
Store Views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404

from .models import Store
from .serializers import (
    StoreListSerializer,
    StoreDetailSerializer,
    StoreCreateUpdateSerializer,
)
from .algorithms import rank_stores

import logging

logger = logging.getLogger(__name__)


class StoreViewSet(viewsets.ModelViewSet):
    """
    Store management with custom ranking algorithm.

    List view uses custom algorithm from stores/algorithms.py
    Retrieve view returns full store details with products
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "list":
            return StoreListSerializer
        elif self.action == "retrieve":
            return StoreDetailSerializer
        else:  # create, update, partial_update
            return StoreCreateUpdateSerializer

    def get_queryset(self):
        """Get stores - filtered by action"""
        if self.action in ["update", "partial_update", "destroy"]:
            # For update/delete, only return user's own stores
            return Store.objects.filter(seller=self.request.user)

        # For list/retrieve, return all active stores
        return Store.objects.filter(is_active=True).select_related("seller")

    def list(self, request, *args, **kwargs):
        """
        List stores with custom ranking algorithm.

        Algorithm applies location-based ranking (40% weight),
        rating, product count, randomness, and newness boost.

        Query Params:
            - search: Search stores by name or description (optional)
            - category: Filter stores by product category (optional)
            - page: Page number for pagination (optional)
            - page_size: Number of results per page (default: 20)
        """
        queryset = self.get_queryset()

        # Get search query
        search_query = request.query_params.get("search", "").strip()
        if search_query:
            queryset = queryset.filter(name__icontains=search_query) | queryset.filter(
                description__icontains=search_query
            )
            logger.info(f"Filtering stores with search: {search_query}")

        # Get category filter
        category_filter = request.query_params.get("category", "").strip()
        if category_filter:
            # Filter stores that have products in this category
            queryset = queryset.filter(
                products__category__iexact=category_filter
            ).distinct()
            logger.info(f"Filtering stores with category: {category_filter}")

        # Get user's location from their profile
        user_state = request.user.state
        user_city = request.user.city

        logger.info(f"Ranking stores for user in {user_city}, {user_state}")

        # Apply custom ranking algorithm
        ranked_stores = rank_stores(queryset, user_state, user_city)

        # Pagination
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        paginated_stores = ranked_stores[start_idx:end_idx]
        has_next = end_idx < len(ranked_stores)

        serializer = self.get_serializer(paginated_stores, many=True)

        return Response(
            {
                "count": len(ranked_stores),
                "next": f"/api/stores/?page={page + 1}" if has_next else None,
                "previous": f"/api/stores/?page={page - 1}" if page > 1 else None,
                "results": serializer.data,
                "user_location": {"city": user_city, "state": user_state},
            }
        )

    def retrieve(self, request, *args, **kwargs):
        """Get store details with products"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Create a new store.
        User becomes a seller automatically (handled by signal).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        store = serializer.save()

        # Return created store with detail serializer
        return Response(
            StoreDetailSerializer(store).data, status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """Update store (full update) with 60-day edit limit"""
        from django.utils import timezone
        from datetime import timedelta

        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        # Enforce 60-day limit after last edit
        if (timezone.now() - instance.updated_at) > timedelta(days=60):
            return Response(
                {
                    "error": "You can only edit your store within 60 days of the last update. Please contact support if you need further changes."
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        store = serializer.save()
        return Response(StoreDetailSerializer(store).data)

    def partial_update(self, request, *args, **kwargs):
        """Update store (partial update)"""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete store (set is_active=False).
        Hard delete not allowed to preserve order history.
        """
        instance = self.get_object()
        instance.is_active = False
        instance.save()

        return Response(
            {"message": "Store deactivated successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(detail=False, methods=["get"])
    def my_stores(self, request):
        """Get current user's stores (seller view)"""
        stores = Store.objects.filter(seller=request.user)
        serializer = StoreListSerializer(stores, many=True)

        return Response({"count": stores.count(), "results": serializer.data})
