from django.contrib import admin
from escrow.models import EscrowTransaction
from django.utils.html import format_html


@admin.register(EscrowTransaction)
class EscrowTransactionAdmin(admin.ModelAdmin):
    """Admin interface for Escrow Transaction management."""

    list_display = [
        "escrow_id",
        "order_number",
        "amount_display",
        "status_badge",
        "days_held_display",
        "held_at",
    ]

    list_filter = [
        "status",
        "held_at",
    ]

    search_fields = [
        "id",
        "order__id",
        "order__buyer__email",
        "order__seller__email",
        "debit_reference",
        "credit_reference",
        "refund_reference",
    ]

    readonly_fields = [
        "id",
        "order",
        "buyer_wallet",
        "seller_wallet",
        "amount",
        "debit_reference",
        "credit_reference",
        "refund_reference",
        "held_at",
        "released_at",
        "refunded_at",
        "days_held_display",
    ]

    fieldsets = (
        (
            "Escrow Information",
            {
                "fields": (
                    "id",
                    "order",
                    "amount",
                    "status",
                )
            },
        ),
        (
            "Wallets",
            {
                "fields": (
                    "buyer_wallet",
                    "seller_wallet",
                )
            },
        ),
        (
            "Transaction References",
            {
                "fields": (
                    "debit_reference",
                    "credit_reference",
                    "refund_reference",
                ),
                "description": "References to wallet transactions",
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "held_at",
                    "released_at",
                    "refunded_at",
                    "days_held_display",
                )
            },
        ),
        ("Notes", {"fields": ("notes",), "classes": ("collapse",)}),
    )

    ordering = ["-held_at"]
    date_hierarchy = "held_at"

    def escrow_id(self, obj):
        """Display short escrow ID."""
        return str(obj.id)[:8].upper()

    escrow_id.short_description = "Escrow #"

    def order_number(self, obj):
        """Display order number."""
        return obj.order.order_number

    order_number.short_description = "Order #"

    def amount_display(self, obj):
        """Display amount with currency."""
        return f"₦{obj.amount:,.2f}"

    amount_display.short_description = "Amount"
    amount_display.admin_order_field = "amount"

    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            "HELD": "#FFA500",  # Orange
            "RELEASED": "#4CAF50",  # Green
            "REFUNDED": "#2196F3",  # Blue
        }
        color = colors.get(obj.status, "#757575")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    def days_held_display(self, obj):
        """Display days held in escrow."""
        days = obj.days_held
        if obj.status == "HELD":
            return f"{days} days (ongoing)"
        return f"{days} days"

    days_held_display.short_description = "Days Held"

    def has_add_permission(self, request):
        """Prevent manual creation - escrow created via order flow."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - keep for audit trail."""
        return False
