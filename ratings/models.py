from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from orders.models import Order
from stores.models import Store


# ==============================================================================
# RATING MODEL
# ==============================================================================


class Rating(models.Model):
    """
    Rating system for COVU marketplace.

    Business Rules:
    - One rating per order (OneToOneField)
    - Can only rate after order is CONFIRMED
    - Rating is 1-5 stars (integer)
    - Review text is optional
    - Requires moderation before appearing on store
    - Auto-updates store.average_rating and total_reviews via signal

    Flow:
    1. Buyer confirms order delivery
    2. System prompts buyer to rate the store
    3. Buyer submits rating (1-5 stars) with optional review
    4. Rating pending moderation (is_approved=False)
    5. Admin approves rating
    6. Store average_rating and total_reviews updated automatically
    """

    # Primary Keys and Relationships
    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,  # Preserve rating even if order deleted
        related_name="rating",
        help_text="The order being rated (one rating per order)",
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="ratings_given",
        help_text="The buyer who left the rating",
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,  # Delete rating if store deleted
        related_name="ratings",
        help_text="The store being rated",
    )

    # Rating Fields
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Star rating from 1-5 (1=Poor, 5=Excellent)",
    )
    review = models.TextField(
        blank=True,
        null=True,
        max_length=1000,
        help_text="Optional written review (max 1000 characters)",
    )

    # Moderation
    is_approved = models.BooleanField(
        default=False,
        help_text="Admin must approve before rating appears on store page",
    )
    approved_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the rating was approved by admin",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ratings_approved",
        help_text="Admin who approved the rating",
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the rating was submitted",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last time rating was updated",
    )

    class Meta:
        db_table = "ratings"
        verbose_name = "Rating"
        verbose_name_plural = "Ratings"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["store", "-created_at"]),
            models.Index(fields=["is_approved"]),
            models.Index(fields=["rating"]),
        ]

    def __str__(self):
        return f"{self.buyer.get_full_name() if self.buyer else 'Anonymous'} → {self.store.name} ({self.rating}★)"

    @property
    def rating_text(self):
        """Human-readable rating description."""
        ratings = {
            1: "Poor",
            2: "Fair",
            3: "Good",
            4: "Very Good",
            5: "Excellent",
        }
        return ratings.get(self.rating, "Unknown")

    @property
    def is_pending_approval(self):
        """Check if rating is waiting for admin approval."""
        return not self.is_approved

    @property
    def has_review(self):
        """Check if rating has written review."""
        return bool(self.review and self.review.strip())
