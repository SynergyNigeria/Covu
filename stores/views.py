"""
Store Views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404

from .models import Store
from .serializers import (
    StoreListSerializer,
    StoreDetailSerializer,
    StoreCreateUpdateSerializer,
)
from .algorithms import rank_stores

import logging

logger = logging.getLogger(__name__)


class StoreViewSet(viewsets.ModelViewSet):
    """
    Store management with custom ranking algorithm.

    List view uses custom algorithm from stores/algorithms.py
    Retrieve view returns full store details with products
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "list":
            return StoreListSerializer
        elif self.action == "retrieve":
            return StoreDetailSerializer
        else:  # create, update, partial_update
            return StoreCreateUpdateSerializer

    def get_queryset(self):
        """Get stores - filtered by action"""
        if self.action in ["update", "partial_update", "destroy"]:
            # For update/delete, only return user's own stores
            return Store.objects.filter(seller=self.request.user)

        # For list/retrieve, return all active stores
        return Store.objects.filter(is_active=True).select_related("seller")

    def list(self, request, *args, **kwargs):
        """
        List stores with custom ranking algorithm.

        Algorithm applies location-based ranking (40% weight),
        rating, product count, randomness, and newness boost.

        Query Params:
            - search: Search stores by name or description (optional)
            - category: Filter stores by product category (optional)
            - page: Page number for pagination (optional)
            - page_size: Number of results per page (default: 20)
        """
        queryset = self.get_queryset()

        # Get search query
        search_query = request.query_params.get("search", "").strip()
        if search_query:
            queryset = queryset.filter(name__icontains=search_query) | queryset.filter(
                description__icontains=search_query
            )
            logger.info(f"Filtering stores with search: {search_query}")

        # Get category filter
        category_filter = request.query_params.get("category", "").strip()
        if category_filter:
            # Map display names to database values
            category_mapping = {
                "Men Clothes": "mens_clothes",
                "Ladies Clothes": "ladies_clothes",
                "Kids Clothes": "kids_clothes",
                "Beauty": "beauty",
                "Body Accessories": "body_accessories",
                "Clothing Extras": "clothing_extras",
                "Bags": "bags",
                "Wigs": "wigs",
                "Body Scents": "body_scents",
            }

            category_snake_case = category_mapping.get(
                category_filter, category_filter.lower().replace(" ", "_")
            )

            # Filter stores by their store category (not product category)
            queryset = queryset.filter(category__iexact=category_snake_case)
            logger.info(
                f"Filtering stores with category: {category_filter} -> {category_snake_case}"
            )

        # Get user's location from their profile
        user_state = request.user.state
        user_city = request.user.city

        logger.info(f"Ranking stores for user in {user_city}, {user_state}")

        # Apply custom ranking algorithm
        ranked_stores = rank_stores(queryset, user_state, user_city)

        # Pagination
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        paginated_stores = ranked_stores[start_idx:end_idx]
        has_next = end_idx < len(ranked_stores)

        serializer = self.get_serializer(paginated_stores, many=True)

        return Response(
            {
                "count": len(ranked_stores),
                "next": f"/api/stores/?page={page + 1}" if has_next else None,
                "previous": f"/api/stores/?page={page - 1}" if page > 1 else None,
                "results": serializer.data,
                "user_location": {"city": user_city, "state": user_state},
            }
        )

    def retrieve(self, request, *args, **kwargs):
        """Get store details with products"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Create a new store.
        User becomes a seller automatically (handled by signal).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        store = serializer.save()

        # Return created store with detail serializer
        return Response(
            StoreDetailSerializer(store).data, status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """Update store (full update) with 60-day edit limit"""
        from django.utils import timezone
        from datetime import timedelta
        import cloudinary.uploader

        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        # Check if this is an image-only update (logo or seller_photo)
        is_image_only_update = set(request.data.keys()).issubset(
            {"logo", "seller_photo"}
        )

        # Check if store has been genuinely edited (not just created)
        # Allow small time difference (< 5 seconds) to account for microsecond differences
        time_diff = abs((instance.updated_at - instance.created_at).total_seconds())
        has_been_edited = time_diff > 5  # More than 5 seconds means it was edited

        # Enforce 60-day lock: After ANY edit, user must wait 60 days before editing again
        # Images can ALWAYS be updated (not affected by lock)
        if not is_image_only_update and has_been_edited:
            days_since_update = (timezone.now() - instance.updated_at).days

            if days_since_update < 60:
                # LOCKED: Less than 60 days have passed since last edit
                days_left = 60 - days_since_update
                return Response(
                    {
                        "error": f"Store details are locked. You can edit again in {days_left} day{'s' if days_left != 1 else ''}. Images can be updated anytime.",
                        "days_since_update": days_since_update,
                        "days_left": days_left,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Delete old images from Cloudinary before updating
        if "logo" in request.data and instance.logo:
            try:
                # Extract public_id from old logo
                old_public_id = str(instance.logo)
                if old_public_id and old_public_id != "image/upload/":
                    cloudinary.uploader.destroy(old_public_id, invalidate=True)
                    print(f"Deleted old logo: {old_public_id}")
            except Exception as e:
                print(f"Failed to delete old logo: {e}")

        if "seller_photo" in request.data and instance.seller_photo:
            try:
                # Extract public_id from old seller photo
                old_public_id = str(instance.seller_photo)
                if old_public_id and old_public_id != "image/upload/":
                    cloudinary.uploader.destroy(old_public_id, invalidate=True)
                    print(f"Deleted old seller photo: {old_public_id}")
            except Exception as e:
                print(f"Failed to delete old seller photo: {e}")

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        store = serializer.save()
        return Response(StoreDetailSerializer(store).data)

    def partial_update(self, request, *args, **kwargs):
        """Update store (partial update)"""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete store (set is_active=False).
        Hard delete not allowed to preserve order history.
        """
        instance = self.get_object()
        instance.is_active = False
        instance.save()

        return Response(
            {"message": "Store deactivated successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(detail=False, methods=["get"])
    def my_stores(self, request):
        """Get current user's stores (seller view)"""
        stores = Store.objects.filter(seller=request.user)
        serializer = StoreListSerializer(stores, many=True)

        return Response({"count": stores.count(), "results": serializer.data})

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def upload_image(self, request):
        """
        Upload image to Cloudinary and return URL.
        Handles both store logos and seller photos.
        """
        try:
            from cloudinary.uploader import upload as cloudinary_upload

            # Get uploaded file
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                return Response(
                    {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
                )

            # Validate file size (max 5MB)
            if uploaded_file.size > 5 * 1024 * 1024:
                return Response(
                    {"error": "File size must be less than 5MB"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate file type
            allowed_types = [
                "image/jpeg",
                "image/jpg",
                "image/png",
                "image/gif",
                "image/webp",
            ]
            if uploaded_file.content_type not in allowed_types:
                return Response(
                    {"error": "Invalid file type. Only images are allowed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get folder from request (store_logos or seller_photos)
            folder = request.data.get("folder", "store_images")

            # Upload to Cloudinary
            upload_result = cloudinary_upload(
                uploaded_file,
                folder=folder,
                resource_type="image",
                overwrite=True,
                invalidate=True,
            )

            # Return the secure URL
            return Response(
                {
                    "url": upload_result["secure_url"],
                    "public_id": upload_result["public_id"],
                    "success": True,
                },
                status=status.HTTP_200_OK,
            )

        except ImportError:
            logger.error("Cloudinary not properly configured")
            return Response(
                {
                    "error": "Image upload service not configured. Please contact support."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.error(f"Error uploading image to Cloudinary: {str(e)}")
            return Response(
                {"error": f"Upload failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
