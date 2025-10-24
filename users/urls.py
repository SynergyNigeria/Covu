"""
User URL Configuration

Authentication endpoints for registration, login, profile management.
"""

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    RegisterView,
    ProfileView,
    PasswordChangeView,
    UserDetailView,
    BecomeSellerView,
)
from .serializers_auth import CustomTokenObtainPairView

app_name = "users"

urlpatterns = [
    # Registration
    path("register/", RegisterView.as_view(), name="register"),
    # JWT Token endpoints
    path("login/", CustomTokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # Profile management
    path("profile/", ProfileView.as_view(), name="profile"),
    path("password/change/", PasswordChangeView.as_view(), name="password_change"),
    path("become-seller/", BecomeSellerView.as_view(), name="become_seller"),
    # User details (public)
    path("users/<int:pk>/", UserDetailView.as_view(), name="user_detail"),
]
