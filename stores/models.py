from django.db import models
from django.conf import settings
from users.models import NIGERIAN_STATES
from cloudinary.models import CloudinaryField
import uuid

# Import store categories for choices
from .categories import STORE_CATEGORIES


# ==============================================================================
# STORE MODEL
# ==============================================================================


class Store(models.Model):
    """
    Seller's store on COVU marketplace.

    One-Click Creation Philosophy:
    - User clicks "Create Store" button → Store created instantly with defaults
    - User can edit all details later (name, logo, description)
    - Default values ensure professional appearance immediately

    Location (state + city) used for 40% of listing algorithm weight.
    """

    # Default images from Cloudinary
    DEFAULT_LOGO_URL = "https://res.cloudinary.com/dpmxcjkfl/image/upload/v1760726056/samples/ecommerce/leather-bag-gray.jpg"
    DEFAULT_SELLER_PHOTO_URL = "https://res.cloudinary.com/dpmxcjkfl/image/upload/v1762100746/covu-flyer_hotir6.png"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    seller = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="store",
        help_text="One store per seller (for MVP)",
    )

    # Basic Info (with smart defaults)
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Auto-generated: COVU + user unique ID (editable later)",
    )
    description = models.TextField(
        default="This will be a very great store.",
        help_text="Default description (editable later)",
    )
    category = models.CharField(
        max_length=50,
        choices=STORE_CATEGORIES,
        db_index=True,
        default="other",
        help_text="Store category for filtering (editable)",
    )
    logo = CloudinaryField(
        "store_logos",
        blank=True,
        null=True,
        help_text="Store logo/brand image (editable later)",
    )
    seller_photo = CloudinaryField(
        "seller_photos",
        blank=True,
        null=True,
        help_text="Seller's profile photo for transparency (editable later)",
    )

    # Removed dynamic assignment of choices
    # Store._meta.get_field('category').choices = STORE_CATEGORIES

    # Location fields (for 40% algorithm weight - copied from user)
    state = models.CharField(
        max_length=50,
        choices=NIGERIAN_STATES,
        db_index=True,
        help_text="Copied from user's state",
    )
    city = models.CharField(
        max_length=100, db_index=True, help_text="Copied from user's city"
    )

    # Algorithm factors
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.0,
        help_text="Updated when ratings are added",
    )
    product_count = models.IntegerField(
        default=0, help_text="Auto-updated when products are added/removed"
    )

    # Delivery Pricing (for order delivery fees)
    delivery_within_lga = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1000.00,
        help_text="Delivery fee for buyers in same city/LGA (₦)",
    )
    delivery_outside_lga = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=2500.00,
        help_text="Delivery fee for buyers outside seller's city/LGA (₦)",
    )
    delivery_outside_state = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=4000.00,
        help_text="Delivery fee for buyers outside seller's state (₦)",
    )

    # Status
    is_active = models.BooleanField(
        default=True, help_text="Store can be deactivated by admin or seller"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stores"
        verbose_name = "Store"
        verbose_name_plural = "Stores"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["state", "city"]
            ),  # Critical for location-based listing
            models.Index(fields=["is_active"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["average_rating"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.seller.email})"

    def save(self, *args, **kwargs):
        """Set default logo URL if no logo provided."""
        # If logo field is empty, store the default URL in description
        # Note: CloudinaryField doesn't support default URL directly
        # We'll handle this in the view/signal
        super().save(*args, **kwargs)

    @property
    def logo_url(self):
        """Return logo URL or default."""
        try:
            if self.logo:
                return self.logo.url
        except (AttributeError, ValueError):
            pass
        return self.DEFAULT_LOGO_URL

    @property
    def seller_photo_url(self):
        """Return seller photo URL or default."""
        try:
            if self.seller_photo:
                return self.seller_photo.url
        except (AttributeError, ValueError):
            pass
        return self.DEFAULT_SELLER_PHOTO_URL

    @property
    def is_new(self):
        """Check if store is new (created within last 30 days) for algorithm boost."""
        from django.utils import timezone
        from datetime import timedelta

        return (timezone.now() - self.created_at) < timedelta(days=30)
