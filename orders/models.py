from django.db import models
from django.conf import settings
from products.models import Product
from django.core.validators import MinValueValidator
import uuid


# ==============================================================================
# ORDER MODEL
# ==============================================================================


class Order(models.Model):
    """
    Order management for COVU marketplace.

    Order Flow:
    PENDING → ACCEPTED → DELIVERED → CONFIRMED
       ↓          ↓           ↓
    CANCELLED  CANCELLED  CANCELLED

    Money Flow:
    - PENDING: Money deducted from buyer, held in escrow
    - ACCEPTED: Still in escrow
    - DELIVERED: Still in escrow, waiting buyer confirmation
    - CONFIRMED: Money released to seller
    - CANCELLED: Money refunded to buyer
    """

    STATUS_CHOICES = [
        ("PENDING", "Pending - Waiting Seller Acceptance"),
        ("ACCEPTED", "Accepted - Seller Preparing Order"),
        ("DELIVERED", "Delivered - Waiting Buyer Confirmation"),
        ("CONFIRMED", "Confirmed - Transaction Complete"),
        ("CANCELLED", "Cancelled"),
    ]

    CANCELLED_BY_CHOICES = [
        ("BUYER", "Buyer"),
        ("SELLER", "Seller"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,  # Don't delete if user deleted
        related_name="purchases",
        help_text="User who placed the order",
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sales",
        help_text="Store owner who will fulfill the order",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,  # Keep order even if product deleted
        related_name="orders",
        help_text="Product being ordered",
    )

    # Order Details (snapshot at order time - prices may change later)
    quantity = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Quantity ordered (always 1 for MVP)",
    )
    product_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Product price at time of order (snapshot)",
    )
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Delivery fee based on buyer location",
    )
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="product_price + delivery_fee"
    )
    delivery_address = models.TextField(
        help_text="Full delivery address provided by buyer"
    )

    # Product snapshot fields (preserve what buyer actually ordered)
    product_name_snapshot = models.CharField(
        max_length=200,
        help_text="Product name at time of order (snapshot)",
        blank=True,
        default="",
    )
    product_image_snapshot = models.URLField(
        max_length=500,
        help_text="Product image URL at time of order (snapshot)",
        blank=True,
        default="",
    )
    product_category_snapshot = models.CharField(
        max_length=50,
        help_text="Product category at time of order (snapshot)",
        blank=True,
        default="",
    )

    # Status & Tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
        db_index=True,
        help_text="Current order status",
    )

    # Cancellation Info
    cancelled_by = models.CharField(
        max_length=10,
        choices=CANCELLED_BY_CHOICES,
        null=True,
        blank=True,
        help_text="Who cancelled the order (buyer or seller)",
    )
    cancellation_reason = models.TextField(
        null=True, blank=True, help_text="Optional reason for cancellation"
    )

    # Timestamps (track order progression)
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="When order was placed"
    )
    accepted_at = models.DateTimeField(
        null=True, blank=True, help_text="When seller accepted the order"
    )
    delivered_at = models.DateTimeField(
        null=True, blank=True, help_text="When seller marked as delivered"
    )
    confirmed_at = models.DateTimeField(
        null=True, blank=True, help_text="When buyer confirmed receipt"
    )
    cancelled_at = models.DateTimeField(
        null=True, blank=True, help_text="When order was cancelled"
    )

    class Meta:
        db_table = "orders"
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["buyer", "status"]),
            models.Index(fields=["seller", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Order {str(self.id)[:8]} - {self.product.name} ({self.status})"

    @property
    def order_number(self):
        """Short order number for display."""
        return str(self.id)[:8].upper()

    @property
    def can_buyer_cancel(self):
        """Check if buyer can cancel this order."""
        return self.status == "PENDING"

    @property
    def can_seller_cancel(self):
        """Check if seller can cancel this order."""
        return self.status in ["PENDING", "ACCEPTED", "DELIVERED"]

    @property
    def can_be_confirmed(self):
        """Check if order can be confirmed by buyer."""
        return self.status == "DELIVERED"

    @property
    def is_completed(self):
        """Check if order is completed."""
        return self.status == "CONFIRMED"

    @property
    def is_cancelled(self):
        """Check if order is cancelled."""
        return self.status == "CANCELLED"

    def save(self, *args, **kwargs):
        """Calculate total_amount before saving."""
        if not self.total_amount:
            self.total_amount = self.product_price + self.delivery_fee
        super().save(*args, **kwargs)
