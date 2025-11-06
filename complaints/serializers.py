"""
Complaint Serializers
"""

from rest_framework import serializers
from .models import Complaint
from users.models import CustomUser


class ComplaintCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating complaints"""

    attachment = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Complaint
        fields = [
            "complaint_type",
            "category",
            "urgency",
            "subject",
            "description",
            "reported_user_name",
            "order_id",
            "transaction_id",
            "transaction_type",
            "attachment",
            "reporter_phone",
        ]

    def validate(self, data):
        """Validate based on complaint type"""
        complaint_type = data.get("complaint_type")

        # Validate seller/buyer complaints
        if complaint_type in ["SELLER", "BUYER"]:
            if not data.get("reported_user_name"):
                raise serializers.ValidationError(
                    {
                        "reported_user_name": "This field is required for seller/buyer reports"
                    }
                )

        # Validate order complaints
        if complaint_type == "ORDER":
            if not data.get("order_id"):
                raise serializers.ValidationError(
                    {"order_id": "Order number is required for order reports"}
                )

        # Validate transaction complaints
        if complaint_type == "TRANSACTION":
            if not data.get("transaction_id"):
                raise serializers.ValidationError(
                    {
                        "transaction_id": "Transaction ID is required for transaction reports"
                    }
                )
            if not data.get("transaction_type"):
                raise serializers.ValidationError(
                    {
                        "transaction_type": "Transaction type is required for transaction reports"
                    }
                )

        return data

    def create(self, validated_data):
        """Create complaint with reporter info"""
        user = self.context["request"].user
        validated_data["reporter"] = user
        validated_data["reporter_email"] = user.email

        # If reporter_phone not provided, use user's phone
        if not validated_data.get("reporter_phone"):
            validated_data["reporter_phone"] = user.phone_number or ""

        return super().create(validated_data)


class ComplaintListSerializer(serializers.ModelSerializer):
    """Serializer for listing complaints"""

    complaint_number = serializers.CharField(read_only=True)
    complaint_type_display = serializers.CharField(
        source="get_complaint_type_display", read_only=True
    )
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    urgency_display = serializers.CharField(
        source="get_urgency_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    is_resolved = serializers.BooleanField(read_only=True)

    class Meta:
        model = Complaint
        fields = [
            "id",
            "complaint_number",
            "complaint_type",
            "complaint_type_display",
            "category",
            "category_display",
            "urgency",
            "urgency_display",
            "subject",
            "status",
            "status_display",
            "is_resolved",
            "created_at",
            "updated_at",
        ]


class ComplaintDetailSerializer(serializers.ModelSerializer):
    """Serializer for complaint details"""

    complaint_number = serializers.CharField(read_only=True)
    complaint_type_display = serializers.CharField(
        source="get_complaint_type_display", read_only=True
    )
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    urgency_display = serializers.CharField(
        source="get_urgency_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    is_resolved = serializers.BooleanField(read_only=True)
    reporter_name = serializers.CharField(source="reporter.full_name", read_only=True)
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = Complaint
        fields = [
            "id",
            "complaint_number",
            "complaint_type",
            "complaint_type_display",
            "category",
            "category_display",
            "urgency",
            "urgency_display",
            "reporter_name",
            "reporter_email",
            "reporter_phone",
            "subject",
            "description",
            "reported_user_name",
            "order_id",
            "transaction_id",
            "transaction_type",
            "attachment_url",
            "status",
            "status_display",
            "admin_response",
            "is_resolved",
            "created_at",
            "updated_at",
            "resolved_at",
        ]

    def get_attachment_url(self, obj):
        """Return full URL for attachment"""
        if obj.attachment:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.attachment.url)
            return obj.attachment.url
        return None
