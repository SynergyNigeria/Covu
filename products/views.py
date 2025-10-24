"""
Product Views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404

from .models import Product
from .serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
)
from .algorithms import rank_products

import logging

logger = logging.getLogger(__name__)


class ProductViewSet(viewsets.ModelViewSet):
    """
    Product management with custom ranking algorithm.

    List view uses custom algorithm from products/algorithms.py
    Retrieve view returns full product details with store info
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "list":
            return ProductListSerializer
        elif self.action == "retrieve":
            return ProductDetailSerializer
        else:  # create, update, partial_update
            return ProductCreateUpdateSerializer

    def get_queryset(self):
        """Get products - filtered by action"""
        if self.action in ["update", "partial_update", "destroy"]:
            # For update/delete, only return products from user's stores
            return Product.objects.filter(store__seller=self.request.user)

        # For list/retrieve, return all active products
        return Product.objects.filter(is_active=True).select_related("store")

    def list(self, request, *args, **kwargs):
        """
        List products with custom ranking algorithm.

        Algorithm: Randomness (30%), Location (30%), Recency (25%), Quality (15%)

        Query Params:
            - category: Filter by category (men_clothes, ladies_clothes, etc.)
            - premium_quality: Filter premium quality products (true/false)
            - durable: Filter durable products (true/false)
            - modern_design: Filter modern/stylish products (true/false)
            - easy_maintain: Filter easy to maintain products (true/false)
        """
        queryset = self.get_queryset()

        # Get user's location from their profile
        user_state = request.user.state
        user_city = request.user.city

        # Apply filters from query params
        category = request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category.lower())
            logger.info(f"Filtering products by category: {category}")

        # Filter by key features
        if request.query_params.get("premium_quality") == "true":
            queryset = queryset.filter(premium_quality=True)

        if request.query_params.get("durable") == "true":
            queryset = queryset.filter(durable=True)

        if request.query_params.get("modern_design") == "true":
            queryset = queryset.filter(modern_design=True)

        if request.query_params.get("easy_maintain") == "true":
            queryset = queryset.filter(easy_maintain=True)

        logger.info(f"Ranking products for user in {user_city}, {user_state}")

        # Apply custom ranking algorithm
        ranked_products = rank_products(queryset, user_state, user_city, category)

        # Serialize and return
        serializer = self.get_serializer(ranked_products, many=True)

        return Response(
            {
                "count": len(ranked_products),
                "results": serializer.data,
                "filters": {
                    "category": category,
                    "user_location": {"city": user_city, "state": user_state},
                },
            }
        )

    def retrieve(self, request, *args, **kwargs):
        """Get product details with full store info"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Create a new product.
        User must own the store.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        # Return created product with detail serializer
        return Response(
            ProductDetailSerializer(product).data, status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """Update product (full update)"""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        return Response(ProductDetailSerializer(product).data)

    def partial_update(self, request, *args, **kwargs):
        """Update product (partial update)"""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete product (set is_active=False).
        Hard delete not allowed to preserve order history.
        """
        instance = self.get_object()
        instance.is_active = False
        instance.save()

        return Response(
            {"message": "Product deactivated successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(detail=False, methods=["get"])
    def my_products(self, request):
        """Get current user's products (seller view)"""
        products = Product.objects.filter(store__seller=request.user)
        serializer = ProductListSerializer(products, many=True)

        return Response({"count": products.count(), "results": serializer.data})

    @action(detail=False, methods=["get"])
    def by_store(self, request):
        """
        Get products by store ID.

        Query Params:
            - store_id: Store UUID (required)
        """
        store_id = request.query_params.get("store_id")
        if not store_id:
            return Response(
                {"error": "store_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        products = Product.objects.filter(store_id=store_id, is_active=True)
        serializer = ProductListSerializer(products, many=True)

        return Response({"count": products.count(), "results": serializer.data})
