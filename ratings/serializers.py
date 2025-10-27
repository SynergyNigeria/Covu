"""
Rating Serializers

Handles rating submission and display:
- CreateRatingSerializer: For submitting ratings on confirmed orders
- RatingSerializer: For displaying rating details
- StoreRatingStatsSerializer: For store rating statistics
"""

from rest_framework import serializers
from .models import Rating
from orders.models import Order


class CreateRatingSerializer(serializers.ModelSerializer):
    """
    Serializer for creating ratings.

    Validates:
    - Order must be CONFIRMED
    - No duplicate ratings (one per order)
    - Buyer must own the order
    """

    order_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Rating
        fields = ["order_id", "rating", "review"]

    def validate_order_id(self, value):
        """Validate order exists and is confirmed"""
        try:
            order = Order.objects.select_related("product__store", "buyer").get(
                id=value
            )
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found")

        # Check order is confirmed
        if order.status != "CONFIRMED":
            raise serializers.ValidationError(
                f"Can only rate CONFIRMED orders. This order is {order.get_status_display()}"
            )

        # Check if already rated
        if hasattr(order, "rating"):
            raise serializers.ValidationError("This order has already been rated")

        # Check buyer owns the order
        request = self.context.get("request")
        if request and order.buyer != request.user:
            raise serializers.ValidationError("You can only rate your own orders")

        return value

    def validate_rating(self, value):
        """Validate rating is between 1-5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5 stars")
        return value

    def create(self, validated_data):
        """Create rating, link to order/store, and auto-approve it"""
        from django.utils import timezone

        order_id = validated_data.pop("order_id")
        order = Order.objects.select_related("product__store", "buyer").get(id=order_id)

        # Create rating with auto-approval
        rating = Rating.objects.create(
            order=order,
            buyer=order.buyer,
            store=order.product.store,
            rating=validated_data["rating"],
            review=validated_data.get("review", ""),
            is_approved=True,
            approved_at=timezone.now(),
            approved_by=None,
        )

        return rating


class RatingSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying rating details.

    Includes:
    - Buyer info (name only for privacy)
    - Order info (product name, order number)
    - Rating details
    """

    buyer_name = serializers.CharField(source="buyer.full_name", read_only=True)
    order_number = serializers.CharField(source="order.order_number", read_only=True)
    product_name = serializers.CharField(source="order.product.name", read_only=True)
    rating_text = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Rating
        fields = [
            "id",
            "buyer_name",
            "order_number",
            "product_name",
            "rating",
            "rating_text",
            "review",
            "created_at",
        ]
        read_only_fields = fields


class StoreRatingStatsSerializer(serializers.Serializer):
    """
    Serializer for store rating statistics.

    Aggregates all ratings for a store to show:
    - Average rating
    - Total number of ratings
    - Rating distribution (how many 5-star, 4-star, etc.)
    """

    store_id = serializers.UUIDField()
    store_name = serializers.CharField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    total_ratings = serializers.IntegerField()

    # Rating distribution
    five_star_count = serializers.IntegerField()
    four_star_count = serializers.IntegerField()
    three_star_count = serializers.IntegerField()
    two_star_count = serializers.IntegerField()
    one_star_count = serializers.IntegerField()

    # Percentage distribution
    five_star_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    four_star_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    three_star_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    two_star_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    one_star_percent = serializers.DecimalField(max_digits=5, decimal_places=2)


class OrderRatingSerializer(serializers.ModelSerializer):
    """
    Simple serializer for checking if an order has been rated.
    Used in order detail views.
    """

    rating_text = serializers.CharField(read_only=True)

    class Meta:
        model = Rating
        fields = ["id", "rating", "rating_text", "review", "created_at"]
        read_only_fields = fields
