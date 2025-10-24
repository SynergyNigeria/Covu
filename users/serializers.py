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
        )
        read_only_fields = ("id", "email", "is_seller", "is_active", "date_joined")

    def get_wallet_balance(self, obj):
        """Get user's wallet balance"""
        try:
            return float(obj.wallet.balance)
        except Exception:
            return 0.0


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    Only allows updating certain fields.
    """

    class Meta:
        model = CustomUser
        fields = (
            "phone_number",
            "full_name",
            "city",
        )
        extra_kwargs = {
            "phone_number": {"required": False},
            "full_name": {"required": False},
            "city": {"required": False},
        }

    def validate_phone_number(self, value):
        """Check if phone number is already taken by another user"""
        user = self.context["request"].user
        if CustomUser.objects.filter(phone_number=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("This phone number is already in use.")
        return value


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
