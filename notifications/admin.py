from django.contrib import admin
from django.utils.html import format_html
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notification model."""

    list_display = [
        "id",
        "user_email",
        "notification_type_badge",
        "title_short",
        "delivery_status",
        "delivery_method",
        "created_at",
    ]
    list_filter = ["notification_type", "is_sent", "delivery_method", "created_at"]
    search_fields = ["user__email", "title", "message", "order__order_number"]
    readonly_fields = [
        "user",
        "notification_type",
        "title",
        "message",
        "order",
        "is_sent",
        "sent_at",
        "delivery_method",
        "error_message",
        "created_at",
    ]
    list_per_page = 50
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    fieldsets = (
        (
            "Recipient",
            {"fields": ("user",)},
        ),
        (
            "Notification Details",
            {
                "fields": (
                    "notification_type",
                    "title",
                    "message",
                    "order",
                )
            },
        ),
        (
            "Delivery Status",
            {
                "fields": (
                    "is_sent",
                    "sent_at",
                    "delivery_method",
                    "error_message",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )

    def user_email(self, obj):
        """Display user email."""
        return obj.user.email

    user_email.short_description = "User"

    def notification_type_badge(self, obj):
        """Display notification type with color coding."""
        colors = {
            "ORDER_CREATED": "#3498db",  # Blue
            "ORDER_ACCEPTED": "#2ecc71",  # Green
            "ORDER_DELIVERED": "#9b59b6",  # Purple
            "ORDER_CONFIRMED": "#27ae60",  # Dark Green
            "ORDER_CANCELLED": "#e74c3c",  # Red
            "PAYMENT_RECEIVED": "#f39c12",  # Orange
            "REFUND_ISSUED": "#e67e22",  # Dark Orange
        }
        color = colors.get(obj.notification_type, "#95a5a6")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_notification_type_display(),
        )

    notification_type_badge.short_description = "Type"

    def title_short(self, obj):
        """Display truncated title."""
        if len(obj.title) > 50:
            return obj.title[:47] + "..."
        return obj.title

    title_short.short_description = "Title"

    def delivery_status(self, obj):
        """Display delivery status with icon."""
        if obj.is_sent:
            return format_html(
                '<span style="color: #27ae60; font-weight: bold;">✓ Sent</span>'
            )
        elif obj.error_message:
            return format_html(
                '<span style="color: #e74c3c; font-weight: bold;">✗ Failed</span>'
            )
        return format_html(
            '<span style="color: #f39c12; font-weight: bold;">⏳ Pending</span>'
        )

    delivery_status.short_description = "Status"

    def has_add_permission(self, request):
        """Prevent manual creation - notifications created by system."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup (unlike escrow/orders)."""
        return True  # Notifications can be deleted for cleanup
