"""
Store Serializers
"""

from rest_framework import serializers
from .models import Store


class StoreListSerializer(serializers.ModelSerializer):
    """
    Serializer for store list view.
    Includes basic store info for browsing.
    """

    seller_name = serializers.CharField(source="seller.full_name", read_only=True)

    class Meta:
        model = Store
        fields = [
            "id",
            "name",
            "description",
            "logo",
            "state",
            "city",
            "seller_name",
            "average_rating",
            "product_count",
            "delivery_within_lga",
            "delivery_outside_lga",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "average_rating",
            "product_count",
            "created_at",
            "updated_at",
        ]


class StoreDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for store detail view.
    Includes all store info including products.
    """

    seller_name = serializers.CharField(source="seller.full_name", read_only=True)
    seller_email = serializers.EmailField(source="seller.email", read_only=True)
    products = serializers.SerializerMethodField()

    class Meta:
        model = Store
        fields = [
            "id",
            "name",
            "description",
            "logo",
            "state",
            "city",
            "seller_name",
            "seller_email",
            "average_rating",
            "product_count",
            "delivery_within_lga",
            "delivery_outside_lga",
            "is_active",
            "created_at",
            "updated_at",
            "products",
        ]
        read_only_fields = [
            "id",
            "average_rating",
            "product_count",
            "created_at",
            "updated_at",
        ]

    def get_products(self, obj):
        """Get active products for this store"""
        from products.serializers import ProductListSerializer

        products = obj.products.filter(is_active=True)[:20]  # Limit to 20 products
        return ProductListSerializer(products, many=True).data


class StoreCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating stores.
    Seller can only modify their own stores.
    """

    class Meta:
        model = Store
        fields = [
            "name",
            "description",
            "logo",
            "state",
            "city",
            "delivery_within_lga",
            "delivery_outside_lga",
        ]

    def validate(self, attrs):
        """Validate store data"""
        # Ensure delivery fees are positive
        if attrs.get("delivery_within_lga") and attrs["delivery_within_lga"] < 0:
            raise serializers.ValidationError(
                {"delivery_within_lga": "Delivery fee must be positive"}
            )

        if attrs.get("delivery_outside_lga") and attrs["delivery_outside_lga"] < 0:
            raise serializers.ValidationError(
                {"delivery_outside_lga": "Delivery fee must be positive"}
            )

        return attrs

    def create(self, validated_data):
        """Create store and set seller from request user"""
        user = self.context["request"].user

        # Set user as seller (signal will update is_seller flag)
        validated_data["seller"] = user

        return super().create(validated_data)
