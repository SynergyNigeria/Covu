"""
User Views for Authentication

Handles user registration, login (JWT), profile management, and password changes.
"""

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    PasswordChangeSerializer,
    CustomTokenObtainPairSerializer,
)
from .models import CustomUser
import logging

logger = logging.getLogger("users")


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view that uses our custom serializer.
    Returns JWT tokens along with user data.
    """

    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint.
    Creates user with auto-wallet creation (via signal).

    POST /api/auth/register/
    """

    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """
        Register a new user.
        Returns user profile with success message.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create user (wallet auto-created via signal)
        user = serializer.save()

        logger.info(f"New user registered: {user.email}")

        # Return user profile
        profile_serializer = UserProfileSerializer(user)

        return Response(
            {
                "message": "Registration successful! Your wallet has been created automatically.",
                "user": profile_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update user profile.

    GET /api/auth/profile/ - Get current user profile
    PATCH /api/auth/profile/ - Update profile fields
    PUT /api/auth/profile/ - Update profile fields
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Use different serializer for GET vs PATCH/PUT"""
        if self.request.method == "GET":
            return UserProfileSerializer
        return UserProfileUpdateSerializer

    def get_object(self):
        """Return the current authenticated user"""
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        """Get user profile with wallet balance"""
        instance = self.get_object()
        serializer = UserProfileSerializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update user profile"""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return full profile after update
        profile_serializer = UserProfileSerializer(instance)

        logger.info(f"Profile updated for user: {instance.email}")

        return Response(
            {"message": "Profile updated successfully", "user": profile_serializer.data}
        )


class PasswordChangeView(APIView):
    """
    Change user password.

    POST /api/auth/password/change/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Change password for authenticated user.
        Requires old_password, new_password, new_password_confirm.
        """
        serializer = PasswordChangeSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info(f"Password changed for user: {request.user.email}")

        return Response(
            {
                "message": "Password changed successfully. Please login again with your new password."
            },
            status=status.HTTP_200_OK,
        )


class BecomeSellerView(APIView):
    """
    Activate seller status for a user and create default store.

    POST /api/auth/become-seller/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Activate seller status for the authenticated user and create a default store.
        """
        user = request.user

        # Check if user is already a seller
        if user.is_seller:
            # If already a seller, check if they have a store
            try:
                from stores.models import Store

                store = Store.objects.get(seller=user)
                from stores.serializers import StoreDetailSerializer

                return Response(
                    {
                        "message": "You are already a seller.",
                        "user": UserProfileSerializer(user).data,
                        "store": StoreDetailSerializer(store).data,
                    },
                    status=status.HTTP_200_OK,
                )
            except Store.DoesNotExist:
                # User is seller but has no store (shouldn't happen, but let's create one)
                pass

        # Activate seller status
        user.is_seller = True
        user.save()

        # Create default store if one doesn't exist
        from stores.models import Store
        from stores.serializers import StoreDetailSerializer
        import random
        import string

        try:
            # Check if user already has a store
            store = Store.objects.get(seller=user)
            logger.info(f"User {user.email} already has a store: {store.name}")
        except Store.DoesNotExist:
            # Generate unique store name
            random_suffix = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=6)
            )
            default_store_name = (
                f"COVU-{user.full_name.replace(' ', '')}-{random_suffix}"
            )

            store = Store.objects.create(
                seller=user,
                name=default_store_name,
                description="Welcome to my store! I offer quality products with excellent customer service.",
                state=user.state,
                city=user.city,
                delivery_within_lga=1000.00,  # ₦1,000 for same city
                delivery_outside_lga=2500.00,  # ₦2,500 for different city
            )
            logger.info(
                f"User {user.email} activated seller status and created store: {store.name}"
            )

        # Return updated user profile and store data
        profile_serializer = UserProfileSerializer(user)
        store_serializer = StoreDetailSerializer(store)

        return Response(
            {
                "success": True,
                "message": "Congratulations! You are now a seller with your own store. Start adding products to reach customers!",
                "user": profile_serializer.data,
                "store": store_serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class UserDetailView(generics.RetrieveAPIView):
    """
    Get details of any user by ID (public info only).

    GET /api/auth/users/{id}/
    """

    queryset = CustomUser.objects.filter(is_active=True)
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        """Get public user profile"""
        instance = self.get_object()

        # Return limited public profile
        return Response(
            {
                "id": instance.id,
                "full_name": instance.full_name,
                "is_seller": instance.is_seller,
                "state": instance.state,
                "city": instance.city,
                "date_joined": instance.date_joined,
            }
        )
