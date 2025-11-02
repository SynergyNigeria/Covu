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
    logo = serializers.SerializerMethodField()
    seller_photo = serializers.SerializerMethodField()

    class Meta:
        model = Store
        fields = [
            "id",
            "name",
            "description",
            "category",
            "logo",
            "seller_photo",
            "state",
            "city",
            "seller_name",
            "average_rating",
            "product_count",
            "delivery_within_lga",
            "delivery_outside_lga",
            "delivery_outside_state",
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

    def get_logo(self, obj):
        """Return full Cloudinary URL for logo"""
        return obj.logo_url

    def get_seller_photo(self, obj):
        """Return full Cloudinary URL for seller photo"""
        return obj.seller_photo_url


class StoreDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for store detail view.
    Includes all store info including products.
    """

    seller_name = serializers.CharField(source="seller.full_name", read_only=True)
    seller_email = serializers.EmailField(source="seller.email", read_only=True)
    products = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()
    seller_photo = serializers.SerializerMethodField()

    class Meta:
        model = Store
        fields = [
            "id",
            "name",
            "description",
            "category",
            "logo",
            "seller_photo",
            "state",
            "city",
            "seller_name",
            "seller_email",
            "average_rating",
            "product_count",
            "delivery_within_lga",
            "delivery_outside_lga",
            "delivery_outside_state",
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

    def get_logo(self, obj):
        """Return full Cloudinary URL for logo"""
        return obj.logo_url

    def get_seller_photo(self, obj):
        """Return full Cloudinary URL for seller photo"""
        return obj.seller_photo_url

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

    logo = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    seller_photo = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )

    class Meta:
        model = Store
        fields = [
            "name",
            "description",
            "category",
            "logo",
            "seller_photo",
            "state",
            "city",
            "delivery_within_lga",
            "delivery_outside_lga",
            "delivery_outside_state",
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
        if attrs.get("delivery_outside_state") and attrs["delivery_outside_state"] < 0:
            raise serializers.ValidationError(
                {"delivery_outside_state": "Delivery fee must be positive"}
            )

        # Handle Cloudinary URLs - extract public_id from full URLs
        if (
            attrs.get("logo")
            and isinstance(attrs["logo"], str)
            and attrs["logo"].startswith("http")
        ):
            # Extract public_id from Cloudinary URL
            # Format: https://res.cloudinary.com/dpmxcjkfl/image/upload/v123456/folder/public_id.jpg
            try:
                parts = attrs["logo"].split("/upload/")
                if len(parts) == 2:
                    # Get everything after '/upload/' and before extension
                    path_with_version = parts[1]
                    # Remove version number (v1234567/)
                    if path_with_version.startswith("v"):
                        path_parts = path_with_version.split("/", 1)
                        if len(path_parts) == 2:
                            attrs["logo"] = path_parts[1].rsplit(".", 1)[
                                0
                            ]  # Remove extension
                        else:
                            attrs["logo"] = path_with_version.rsplit(".", 1)[0]
                    else:
                        attrs["logo"] = path_with_version.rsplit(".", 1)[0]
            except Exception as e:
                # If parsing fails, keep the original URL
                pass

        if (
            attrs.get("seller_photo")
            and isinstance(attrs["seller_photo"], str)
            and attrs["seller_photo"].startswith("http")
        ):
            # Extract public_id from Cloudinary URL
            try:
                parts = attrs["seller_photo"].split("/upload/")
                if len(parts) == 2:
                    path_with_version = parts[1]
                    if path_with_version.startswith("v"):
                        path_parts = path_with_version.split("/", 1)
                        if len(path_parts) == 2:
                            attrs["seller_photo"] = path_parts[1].rsplit(".", 1)[0]
                        else:
                            attrs["seller_photo"] = path_with_version.rsplit(".", 1)[0]
                    else:
                        attrs["seller_photo"] = path_with_version.rsplit(".", 1)[0]
            except Exception as e:
                pass

        return attrs

    def create(self, validated_data):
        """Create store and set seller from request user"""
        user = self.context["request"].user

        # Set user as seller (signal will update is_seller flag)
        validated_data["seller"] = user

        return super().create(validated_data)
