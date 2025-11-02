"""
Product Serializers
"""

from rest_framework import serializers
from .models import Product


class ProductListSerializer(serializers.ModelSerializer):
    """
    Serializer for product list view.
    Includes basic product info with store details.
    """

    store_name = serializers.CharField(source="store.name", read_only=True)
    store_city = serializers.CharField(source="store.city", read_only=True)
    store_state = serializers.CharField(source="store.state", read_only=True)
    store_rating = serializers.FloatField(source="store.average_rating", read_only=True)
    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "category",
            "images",
            "premium_quality",
            "durable",
            "modern_design",
            "easy_maintain",
            "store_name",
            "store_city",
            "store_state",
            "store_rating",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_images(self, obj):
        """Return full Cloudinary URL for images"""
        if obj.images:
            return obj.images.url
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for product detail view.
    Includes full product info with complete store details.
    """

    store_info = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "category",
            "images",
            "premium_quality",
            "durable",
            "modern_design",
            "easy_maintain",
            "store_info",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_images(self, obj):
        """Return full Cloudinary URL for images"""
        if obj.images:
            return obj.images.url
        return None

    def get_store_info(self, obj):
        """Get complete store information"""
        store = obj.store
        return {
            "id": str(store.id),
            "name": store.name,
            "description": store.description,
            "logo": store.logo.url if store.logo else None,
            "seller_photo": store.seller_photo.url if store.seller_photo else None,
            "city": store.city,
            "state": store.state,
            "average_rating": float(store.average_rating),
            "delivery_within_lga": float(store.delivery_within_lga),
            "delivery_outside_lga": float(store.delivery_outside_lga),
        }


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating products.
    Seller can only modify products in their own stores.
    Store is automatically assigned based on authenticated user.
    """

    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "price",
            "category",
            "images",
            "premium_quality",
            "durable",
            "modern_design",
            "easy_maintain",
        ]

        def create(self, validated_data):
            user = self.context["request"].user
            if not hasattr(user, "store"):
                raise serializers.ValidationError(
                    "You must create a store before adding products"
                )
            validated_data["store"] = user.store
            return super().create(validated_data)

    def validate_price(self, value):
        """Ensure price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero")
        return value

    def validate_category(self, value):
        """Validate category is one of the allowed choices"""
        allowed_categories = [
            "mens_clothes",
            "ladies_clothes",
            "kids_clothes",
            "beauty",
            "body_accessories",
            "clothing_extras",
            "bags",
            "wigs",
            "body_scents",
        ]

        if value.lower() not in allowed_categories:
            raise serializers.ValidationError(
                f"Category must be one of: {', '.join(allowed_categories)}"
            )

        return value.lower()

    def create(self, validated_data):
        """Create product and auto-assign user's store"""
        user = self.context["request"].user

        # Check if user has a store
        if not hasattr(user, "store"):
            raise serializers.ValidationError(
                "You must create a store before adding products"
            )

        # Auto-assign the user's store
        validated_data["store"] = user.store
        return super().create(validated_data)
