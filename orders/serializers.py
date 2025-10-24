"""
Order Serializers
"""

from rest_framework import serializers
from .models import Order
from products.models import Product
from users.models import CustomUser


class OrderBuyerSerializer(serializers.ModelSerializer):
    """Minimal buyer info for order"""

    class Meta:
        model = CustomUser
        fields = ["id", "full_name", "email", "phone_number"]
        read_only_fields = fields


class OrderSellerSerializer(serializers.ModelSerializer):
    """Minimal seller info for order"""

    class Meta:
        model = CustomUser
        fields = ["id", "full_name", "email", "phone_number"]
        read_only_fields = fields


class OrderProductSerializer(serializers.ModelSerializer):
    """Minimal product info for order"""

    store_name = serializers.CharField(source="store.name", read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "images", "category", "store_name"]
        read_only_fields = fields


class OrderListSerializer(serializers.ModelSerializer):
    """
    Serializer for order list view.
    Shows essential order info for browsing.
    """

    buyer_name = serializers.CharField(source="buyer.full_name", read_only=True)
    seller_name = serializers.CharField(source="seller.full_name", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_images = serializers.ImageField(source="product.images", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "buyer_name",
            "seller_name",
            "product_name",
            "product_images",
            "total_amount",
            "status",
            "status_display",
            "delivery_address",
            "created_at",
        ]
        read_only_fields = fields


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for order detail view.
    Includes complete nested data (buyer, seller, product).
    """

    buyer = OrderBuyerSerializer(read_only=True)
    seller = OrderSellerSerializer(read_only=True)
    product = OrderProductSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    # Escrow info
    escrow_status = serializers.SerializerMethodField()
    escrow_amount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "buyer",
            "seller",
            "product",
            "quantity",
            "product_price",
            "delivery_fee",
            "total_amount",
            "status",
            "status_display",
            "delivery_address",
            "escrow_status",
            "escrow_amount",
            "created_at",
            "accepted_at",
            "delivered_at",
            "confirmed_at",
            "cancelled_at",
            "cancelled_by",
            "cancellation_reason",
        ]
        read_only_fields = fields

    def get_escrow_status(self, obj):
        """Get escrow transaction status"""
        try:
            return obj.escrow.status
        except:
            return None

    def get_escrow_amount(self, obj):
        """Get escrow transaction amount"""
        try:
            return float(obj.escrow.amount)
        except:
            return None


class OrderCreateSerializer(serializers.Serializer):
    """
    Serializer for creating orders.
    Uses OrderService.create_order() under the hood.
    """

    product_id = serializers.UUIDField(required=True)
    delivery_address = serializers.CharField(
        required=True, max_length=500, help_text="Complete delivery address"
    )

    def validate_product_id(self, value):
        """Ensure product exists and is active"""
        try:
            product = Product.objects.get(id=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or inactive")

        return value

    def validate_delivery_address(self, value):
        """Ensure delivery address is not empty"""
        if not value.strip():
            raise serializers.ValidationError("Delivery address cannot be empty")

        return value.strip()


class OrderCancelSerializer(serializers.Serializer):
    """
    Serializer for cancelling orders.
    """

    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Reason for cancellation",
    )

    def validate_reason(self, value):
        """Provide default reason if empty"""
        if not value or not value.strip():
            return "No reason provided"
        return value.strip()
