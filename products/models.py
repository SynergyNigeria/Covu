from django.db import models
from stores.models import Store
from cloudinary.models import CloudinaryField
import uuid


# ==============================================================================
# PRODUCT MODEL
# ==============================================================================


class Product(models.Model):
    """
    Product listings on COVU marketplace.

    9 categories for fashion & beauty products.
    4 key features as boolean flags (from your vision).
    Location inherited from store for product listing algorithm.
    """

    # 9 Categories from your vision
    CATEGORIES = [
        ("mens_clothes", "Men Clothes"),
        ("ladies_clothes", "Ladies Clothes"),
        ("kids_clothes", "Kids Clothes"),
        ("beauty", "Beauty"),
        ("body_accessories", "Body Accessories"),
        ("clothing_extras", "Clothing Extras"),
        ("bags", "Bags"),
        ("wigs", "Wigs"),
        ("body_scents", "Body Scents"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="products",
        help_text="Store that owns this product",
    )

    # Basic Info
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Price in Nigerian Naira (NGN)"
    )
    category = models.CharField(
        max_length=50, choices=CATEGORIES, db_index=True, help_text="Product category"
    )

    # Product Images (Cloudinary)
    images = CloudinaryField("product_images", help_text="Primary product image")

    # Key Features (4 boolean flags from your vision)
    premium_quality = models.BooleanField(
        default=False, help_text="Premium quality materials"
    )
    durable = models.BooleanField(default=False, help_text="Durable and long-lasting")
    modern_design = models.BooleanField(
        default=False, help_text="Modern and stylish design"
    )
    easy_maintain = models.BooleanField(
        default=False, help_text="Easy to maintain and clean"
    )

    # Status
    is_active = models.BooleanField(
        default=True, help_text="Product is visible and available"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["-created_at"]  # Newest first for algorithm
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["created_at"]),  # For new product visibility
            models.Index(fields=["store", "is_active"]),  # Optimize store queries
            models.Index(fields=["name"]),  # For search performance
        ]

    def __str__(self):
        return f"{self.name} ({self.store.name})"

    @property
    def is_new(self):
        """Check if product is new (created within last 30 days) for algorithm boost."""
        from django.utils import timezone
        from datetime import timedelta

        return (timezone.now() - self.created_at) < timedelta(days=30)

    @property
    def location_state(self):
        """Get state from store for location-based algorithm."""
        return self.store.state

    @property
    def location_city(self):
        """Get city from store for location-based algorithm."""
        return self.store.city
