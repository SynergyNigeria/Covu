"""
Custom JWT Token Serializers with User Data
"""

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers
from .models import CustomUser


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that includes user data in the response.
    Fixes the "undefined full_name" error in frontend.
    """

    def validate(self, attrs):
        # Get the default token data
        data = super().validate(attrs)

        # Add custom user data
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


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token obtain view using our custom serializer.
    """

    serializer_class = CustomTokenObtainPairSerializer
