"""
Order Views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Order
from .serializers import (
    OrderListSerializer,
    OrderDetailSerializer,
    OrderCreateSerializer,
    OrderCancelSerializer,
)
from .services import (
    OrderService,
    InsufficientFundsError,
    InvalidOrderStatusError,
    PermissionDeniedError,
)
from products.models import Product

import logging

logger = logging.getLogger(__name__)


class OrderViewSet(viewsets.ModelViewSet):
    """
    Order management with custom actions.

    - List: Get user's orders (buyer or seller view)
    - Retrieve: Get order details
    - Create: Create new order (uses OrderService)
    - Custom actions: accept, deliver, confirm, cancel
    """

    permission_classes = [IsAuthenticated]
    lookup_field = "pk"  # Explicitly specify lookup field for UUID primary key

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "list":
            return OrderListSerializer
        elif self.action == "retrieve":
            return OrderDetailSerializer
        elif self.action == "create":
            return OrderCreateSerializer
        elif self.action == "cancel":
            return OrderCancelSerializer
        else:
            return OrderDetailSerializer

    def get_queryset(self):
        """
        Get orders filtered by user role.

        Query Params:
            - as_seller: 'true' to see orders as seller (default: buyer view)
            - status: Filter by status (PENDING, ACCEPTED, DELIVERED, etc.)
        """
        user = self.request.user

        # Check if user wants seller view
        as_seller = (
            self.request.query_params.get("as_seller", "false").lower() == "true"
        )

        if as_seller:
            # Seller view: orders where user is the seller
            queryset = Order.objects.filter(seller=user)
        else:
            # Buyer view: orders where user is the buyer
            queryset = Order.objects.filter(buyer=user)

        # Optional status filter
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        return queryset.select_related(
            "buyer", "seller", "product", "product__store"
        ).order_by("-created_at")

    def get_object(self):
        """
        Override to allow access to orders regardless of role filter.
        Permissions are checked in individual action methods.
        """
        queryset = Order.objects.all()  # Don't filter by role for single object lookup
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = (
            queryset.filter(**filter_kwargs)
            .select_related("buyer", "seller", "product", "product__store")
            .first()
        )

        if not obj:
            from rest_framework.exceptions import NotFound

            raise NotFound()

        # Check object-level permissions
        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request, *args, **kwargs):
        """List orders with role-based filtering"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # Determine current view
        as_seller = request.query_params.get("as_seller", "false").lower() == "true"
        view_type = "seller" if as_seller else "buyer"

        return Response(
            {"count": queryset.count(), "view": view_type, "results": serializer.data}
        )

    def retrieve(self, request, *args, **kwargs):
        """Get order details"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Create new order using OrderService.

        Body:
            - product_id: UUID of product to order
            - delivery_address: Complete delivery address
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data["product_id"]
        delivery_address = serializer.validated_data["delivery_address"]

        # Get product
        product = get_object_or_404(Product, id=product_id, is_active=True)

        # Check if user is trying to buy from their own store
        if product.store.seller == request.user:
            return Response(
                {"error": "You cannot buy from your own store"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Create order using service layer
            order = OrderService.create_order(
                buyer=request.user, product=product, delivery_address=delivery_address
            )

            logger.info(f"Order created: {order.order_number} by {request.user.email}")

            # Return created order
            return Response(
                OrderDetailSerializer(order).data, status=status.HTTP_201_CREATED
            )

        except InsufficientFundsError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return Response(
                {"error": "Failed to create order. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        """
        Seller accepts order (PENDING → ACCEPTED).

        Only seller can accept their own orders.
        Only PENDING orders can be accepted.
        """
        order = self.get_object()

        # Validate seller owns this order
        if order.seller != request.user:
            return Response(
                {"error": "You can only accept your own orders"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            OrderService.accept_order(order=order, seller=request.user)

            logger.info(f"Order accepted: {order.order_number} by {request.user.email}")

            return Response(
                {
                    "status": "success",
                    "message": "Order accepted successfully",
                    "order": OrderDetailSerializer(order).data,
                }
            )

        except InvalidOrderStatusError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDeniedError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=["post"])
    def deliver(self, request, pk=None):
        """
        Seller marks order as delivered (ACCEPTED → DELIVERED).

        Only seller can mark their own orders as delivered.
        Only ACCEPTED orders can be marked delivered.
        """
        order = self.get_object()

        # Validate seller owns this order
        if order.seller != request.user:
            return Response(
                {"error": "You can only deliver your own orders"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            OrderService.deliver_order(order=order, seller=request.user)

            logger.info(
                f"Order delivered: {order.order_number} by {request.user.email}"
            )

            return Response(
                {
                    "status": "success",
                    "message": "Order marked as delivered",
                    "order": OrderDetailSerializer(order).data,
                }
            )

        except InvalidOrderStatusError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDeniedError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """
        Buyer confirms delivery (DELIVERED → CONFIRMED).

        Only buyer can confirm their own orders.
        Only DELIVERED orders can be confirmed.
        This releases escrow funds to seller.
        """
        order = self.get_object()

        # Validate buyer owns this order
        if order.buyer != request.user:
            return Response(
                {"error": "You can only confirm your own orders"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            OrderService.confirm_order(order=order, buyer=request.user)

            logger.info(
                f"Order confirmed: {order.order_number} by {request.user.email}"
            )

            return Response(
                {
                    "status": "success",
                    "message": "Order confirmed, payment released to seller",
                    "order": OrderDetailSerializer(order).data,
                }
            )

        except InvalidOrderStatusError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDeniedError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """
        Cancel order with refund.

        Rules:
        - Buyer can cancel PENDING orders only
        - Seller can cancel before CONFIRMED
        - Cancelled orders refund buyer automatically
        """
        order = self.get_object()

        # Determine who is cancelling
        if order.buyer == request.user:
            cancelled_by = "BUYER"
        elif order.seller == request.user:
            cancelled_by = "SELLER"
        else:
            return Response(
                {"error": "You are not authorized to cancel this order"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get cancellation reason
        serializer = OrderCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get("reason", "No reason provided")

        try:
            OrderService.cancel_order(
                order=order, cancelled_by=cancelled_by, reason=reason
            )

            logger.info(
                f"Order cancelled: {order.order_number} by {cancelled_by} ({request.user.email})"
            )

            return Response(
                {
                    "status": "success",
                    "message": "Order cancelled, refund processed",
                    "order": OrderDetailSerializer(order).data,
                }
            )

        except InvalidOrderStatusError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDeniedError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """
        Get order statistics for current user.

        Returns counts by status for both buyer and seller views.
        """
        user = request.user

        buyer_stats = {
            "total": Order.objects.filter(buyer=user).count(),
            "pending": Order.objects.filter(buyer=user, status="PENDING").count(),
            "accepted": Order.objects.filter(buyer=user, status="ACCEPTED").count(),
            "delivered": Order.objects.filter(buyer=user, status="DELIVERED").count(),
            "confirmed": Order.objects.filter(buyer=user, status="CONFIRMED").count(),
            "cancelled": Order.objects.filter(buyer=user, status="CANCELLED").count(),
        }

        seller_stats = {
            "total": Order.objects.filter(seller=user).count(),
            "pending": Order.objects.filter(seller=user, status="PENDING").count(),
            "accepted": Order.objects.filter(seller=user, status="ACCEPTED").count(),
            "delivered": Order.objects.filter(seller=user, status="DELIVERED").count(),
            "confirmed": Order.objects.filter(seller=user, status="CONFIRMED").count(),
            "cancelled": Order.objects.filter(seller=user, status="CANCELLED").count(),
        }

        return Response({"buyer": buyer_stats, "seller": seller_stats})
