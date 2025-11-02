"""
User Serializers for Authentication

Handles user registration, profile management, and data serialization.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CustomUser
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Validates password and creates user with auto-wallet creation.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        min_length=8,
        help_text="Password must be at least 8 characters long",
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        help_text="Confirm your password",
    )

    class Meta:
        model = CustomUser
        fields = (
            "email",
            "phone_number",
            "full_name",
            "state",
            "city",
            "password",
            "password_confirm",
        )
        extra_kwargs = {
            "email": {"required": True},
            "phone_number": {"required": True},
            "full_name": {"required": True},
            "state": {"required": True},
            "city": {"required": True},
        }

    def validate(self, attrs):
        """Validate that passwords match"""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )

        # Validate password strength
        try:
            validate_password(attrs["password"])
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return attrs

    def validate_email(self, value):
        """Check if email already exists"""
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_phone_number(self, value):
        """Check if phone number already exists"""
        if CustomUser.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                "A user with this phone number already exists."
            )
        return value

    def create(self, validated_data):
        """Create user with hashed password (wallet auto-created via signal)"""
        # Remove password_confirm as it's not needed for user creation
        validated_data.pop("password_confirm")

        # Create user using create_user method (hashes password automatically)
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            phone_number=validated_data["phone_number"],
            full_name=validated_data["full_name"],
            state=validated_data["state"],
            city=validated_data["city"],
        )

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile.
    Includes wallet balance and read-only fields.
    """

    wallet_balance = serializers.SerializerMethodField()
    can_update_location = serializers.SerializerMethodField()
    can_update_contact = serializers.SerializerMethodField()
    location_update_available_in_days = serializers.SerializerMethodField()
    contact_update_available_in_days = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "email",
            "phone_number",
            "full_name",
            "state",
            "city",
            "is_seller",
            "wallet_balance",
            "is_active",
            "date_joined",
            "location_last_updated",
            "contact_last_updated",
            "can_update_location",
            "can_update_contact",
            "location_update_available_in_days",
            "contact_update_available_in_days",
        )
        read_only_fields = (
            "id",
            "email",
            "is_seller",
            "is_active",
            "date_joined",
            "location_last_updated",
            "contact_last_updated",
        )

    def get_wallet_balance(self, obj):
        """Get user's wallet balance"""
        try:
            return float(obj.wallet.balance)
        except Exception:
            return 0.0

    def get_can_update_location(self, obj):
        """Check if user can update location (30-day limit)"""
        from django.utils import timezone
        from datetime import timedelta

        if not obj.location_last_updated:
            return True

        now = timezone.now()
        thirty_days = timedelta(days=30)
        time_since_last_update = now - obj.location_last_updated

        return time_since_last_update >= thirty_days

    def get_can_update_contact(self, obj):
        """Check if user can update contact (30-day limit)"""
        from django.utils import timezone
        from datetime import timedelta

        if not obj.contact_last_updated:
            return True

        now = timezone.now()
        thirty_days = timedelta(days=30)
        time_since_last_update = now - obj.contact_last_updated

        return time_since_last_update >= thirty_days

    def get_location_update_available_in_days(self, obj):
        """Calculate days remaining until location can be updated"""
        from django.utils import timezone
        from datetime import timedelta

        if not obj.location_last_updated:
            return 0

        now = timezone.now()
        thirty_days = timedelta(days=30)
        time_since_last_update = now - obj.location_last_updated

        if time_since_last_update >= thirty_days:
            return 0

        days_remaining = 30 - time_since_last_update.days
        return max(0, days_remaining)

    def get_contact_update_available_in_days(self, obj):
        """Calculate days remaining until contact can be updated"""
        from django.utils import timezone
        from datetime import timedelta

        if not obj.contact_last_updated:
            return 0

        now = timezone.now()
        thirty_days = timedelta(days=30)
        time_since_last_update = now - obj.contact_last_updated

        if time_since_last_update >= thirty_days:
            return 0

        days_remaining = 30 - time_since_last_update.days
        return max(0, days_remaining)


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    Only allows updating certain fields with 30-day rate limiting for location and contact.
    """

    class Meta:
        model = CustomUser
        fields = (
            "phone_number",
            "full_name",
            "state",
            "city",
        )
        extra_kwargs = {
            "phone_number": {"required": False},
            "full_name": {"required": False},
            "state": {"required": False},
            "city": {"required": False},
        }

    def validate_phone_number(self, value):
        """Check if phone number is already taken by another user"""
        user = self.context["request"].user
        if CustomUser.objects.filter(phone_number=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("This phone number is already in use.")
        return value

    def validate(self, attrs):
        """
        Validate 30-day rate limiting for location and contact updates.
        """
        from django.utils import timezone
        from datetime import timedelta

        user = self.context["request"].user
        now = timezone.now()
        thirty_days = timedelta(days=30)

        # Check if location fields (state or city) are being updated
        location_fields_updated = "state" in attrs or "city" in attrs
        if location_fields_updated:
            # Check if user has updated location before
            if user.location_last_updated:
                time_since_last_update = now - user.location_last_updated
                if time_since_last_update < thirty_days:
                    days_remaining = 30 - time_since_last_update.days
                    raise serializers.ValidationError(
                        {
                            "location": f"You can only update your location once every 30 days. Please wait {days_remaining} more day(s)."
                        }
                    )

        # Check if contact field (phone_number) is being updated
        if "phone_number" in attrs:
            # Check if user has updated contact before
            if user.contact_last_updated:
                time_since_last_update = now - user.contact_last_updated
                if time_since_last_update < thirty_days:
                    days_remaining = 30 - time_since_last_update.days
                    raise serializers.ValidationError(
                        {
                            "phone_number": f"You can only update your phone number once every 30 days. Please wait {days_remaining} more day(s)."
                        }
                    )

        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""

    old_password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )
    new_password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}, min_length=8
    )
    new_password_confirm = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )

    def validate_old_password(self, value):
        """Validate old password is correct"""
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate(self, attrs):
        """Validate new passwords match"""
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password": "New password fields didn't match."}
            )

        # Validate password strength
        try:
            validate_password(attrs["new_password"])
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})

        return attrs

    def save(self):
        """Update user password"""
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that includes user data in response.
    Fixes the "undefined full_name" error in frontend.
    """

    def validate(self, attrs):
        # Get the default token response
        data = super().validate(attrs)

        # Add user data to response
        data["user"] = {
            "id": str(self.user.id),
            "email": self.user.email,
            "full_name": self.user.full_name,
            "phone_number": self.user.phone_number,
            "state": self.user.state,
            "city": self.user.city,
            "is_seller": self.user.is_seller,
            "wallet_balance": (
                float(self.user.wallet.balance) if hasattr(self.user, "wallet") else 0.0
            ),
            "is_active": self.user.is_active,
        }

        return data
