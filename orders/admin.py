from django.contrib import admin
from orders.models import Order
from django.utils.html import format_html


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin interface for Order management."""

    list_display = [
        "order_number_display",
        "product_name",
        "buyer_email",
        "seller_email",
        "total_amount_display",
        "status_badge",
        "created_at",
    ]

    list_filter = [
        "status",
        "created_at",
        "cancelled_by",
    ]

    search_fields = [
        "id",
        "buyer__email",
        "buyer__full_name",
        "seller__email",
        "seller__full_name",
        "product__name",
        "delivery_address",
    ]

    readonly_fields = [
        "id",
        "order_number_display",
        "created_at",
        "accepted_at",
        "delivered_at",
        "confirmed_at",
        "cancelled_at",
        "total_amount",
        "can_buyer_cancel_display",
        "can_seller_cancel_display",
    ]

    fieldsets = (
        (
            "Order Information",
            {
                "fields": (
                    "id",
                    "order_number_display",
                    "status",
                    "created_at",
                )
            },
        ),
        (
            "Parties",
            {
                "fields": (
                    "buyer",
                    "seller",
                    "product",
                )
            },
        ),
        (
            "Pricing",
            {
                "fields": (
                    "quantity",
                    "product_price",
                    "delivery_fee",
                    "total_amount",
                ),
                "description": "Prices are snapshots at order time",
            },
        ),
        ("Delivery", {"fields": ("delivery_address",)}),
        (
            "Status Tracking",
            {
                "fields": (
                    "accepted_at",
                    "delivered_at",
                    "confirmed_at",
                )
            },
        ),
        (
            "Cancellation Info",
            {
                "fields": (
                    "cancelled_by",
                    "cancellation_reason",
                    "cancelled_at",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "can_buyer_cancel_display",
                    "can_seller_cancel_display",
                )
            },
        ),
    )

    ordering = ["-created_at"]
    date_hierarchy = "created_at"

    def order_number_display(self, obj):
        """Display short order number."""
        return obj.order_number

    order_number_display.short_description = "Order #"

    def product_name(self, obj):
        """Display product name."""
        return obj.product.name

    product_name.short_description = "Product"
    product_name.admin_order_field = "product__name"

    def buyer_email(self, obj):
        """Display buyer email."""
        return obj.buyer.email

    buyer_email.short_description = "Buyer"
    buyer_email.admin_order_field = "buyer__email"

    def seller_email(self, obj):
        """Display seller email."""
        return obj.seller.email

    seller_email.short_description = "Seller"
    seller_email.admin_order_field = "seller__email"

    def total_amount_display(self, obj):
        """Display total amount with currency."""
        return f"₦{obj.total_amount:,.2f}"

    total_amount_display.short_description = "Total"
    total_amount_display.admin_order_field = "total_amount"

    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            "PENDING": "#FFA500",  # Orange
            "ACCEPTED": "#2196F3",  # Blue
            "DELIVERED": "#9C27B0",  # Purple
            "CONFIRMED": "#4CAF50",  # Green
            "CANCELLED": "#F44336",  # Red
        }
        color = colors.get(obj.status, "#757575")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    def can_buyer_cancel_display(self, obj):
        """Display if buyer can cancel."""
        return "✅ Yes" if obj.can_buyer_cancel else "❌ No"

    can_buyer_cancel_display.short_description = "Buyer Can Cancel?"

    def can_seller_cancel_display(self, obj):
        """Display if seller can cancel."""
        return "✅ Yes" if obj.can_seller_cancel else "❌ No"

    can_seller_cancel_display.short_description = "Seller Can Cancel?"

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of orders - keep for audit trail."""
        return False
