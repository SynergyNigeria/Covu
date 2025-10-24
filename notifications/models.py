from django.db import models
from django.conf import settings


# ==============================================================================
# NOTIFICATION MODEL
# ==============================================================================


class Notification(models.Model):
    """
    Notification system for COVU marketplace.

    Stores notification history for all user notifications.
    Currently uses console logging (placeholder).

    Future: Will integrate WhatsApp Business API when credentials ready.

    Notification Types:
    - ORDER_CREATED: Seller notified of new order
    - ORDER_ACCEPTED: Buyer notified seller accepted
    - ORDER_DELIVERED: Buyer notified seller delivered
    - ORDER_CONFIRMED: Seller notified buyer confirmed
    - ORDER_CANCELLED: Both parties notified of cancellation
    - PAYMENT_RECEIVED: Seller notified of payment release
    - REFUND_ISSUED: Buyer notified of refund
    """

    NOTIFICATION_TYPES = [
        ("ORDER_CREATED", "New Order Created"),
        ("ORDER_ACCEPTED", "Order Accepted by Seller"),
        ("ORDER_DELIVERED", "Order Delivered"),
        ("ORDER_CONFIRMED", "Order Confirmed by Buyer"),
        ("ORDER_CANCELLED", "Order Cancelled"),
        ("PAYMENT_RECEIVED", "Payment Received"),
        ("REFUND_ISSUED", "Refund Issued"),
    ]

    # Recipient
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="User who should receive this notification",
    )

    # Notification Details
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        help_text="Type of notification",
    )
    title = models.CharField(
        max_length=200,
        help_text="Notification title/subject",
    )
    message = models.TextField(
        help_text="Full notification message content",
    )

    # Metadata
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
        help_text="Related order (if applicable)",
    )

    # Delivery Status
    is_sent = models.BooleanField(
        default=False,
        help_text="Whether notification was successfully sent",
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification was sent",
    )
    delivery_method = models.CharField(
        max_length=50,
        default="CONSOLE",
        help_text="How notification was delivered (CONSOLE, WHATSAPP, EMAIL, SMS)",
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if sending failed",
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When notification was created",
    )

    class Meta:
        db_table = "notifications"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["notification_type"]),
            models.Index(fields=["is_sent"]),
        ]

    def __str__(self):
        return f"{self.notification_type} → {self.user.email} ({self.get_status_display()})"

    @property
    def get_status_display(self):
        """Human-readable status."""
        if self.is_sent:
            return "✓ Sent"
        elif self.error_message:
            return "✗ Failed"
        return "⏳ Pending"

    @property
    def is_order_notification(self):
        """Check if notification is related to an order."""
        return self.order is not None
