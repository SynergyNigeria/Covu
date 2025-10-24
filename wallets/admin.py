from django.contrib import admin
from .models import Wallet, WalletTransaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """
    Admin interface for Wallet management.
    Balance is read-only (computed from transactions).
    """

    list_display = (
        "user_email",
        "balance_display",
        "currency",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "currency", "created_at")
    search_fields = ("user__email", "user__full_name", "user__phone_number")
    readonly_fields = ("id", "balance_display", "currency", "created_at", "updated_at")

    fieldsets = (
        (
            "Wallet Information",
            {"fields": ("id", "user", "currency", "balance_display", "is_active")},
        ),
        (
            "Manual Balance Update (Testing Only)",
            {
                "fields": (),
                "description": "To update balance, go to Wallet Transactions and create a CREDIT transaction.",
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def user_email(self, obj):
        """Display user email."""
        return obj.user.email

    user_email.short_description = "User Email"
    user_email.admin_order_field = "user__email"

    def balance_display(self, obj):
        """Display formatted balance."""
        return f"₦{obj.balance:,.2f}"

    balance_display.short_description = "Balance"

    def has_add_permission(self, request):
        """Prevent manual wallet creation (auto-created via signal)."""
        return False


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    """
    Admin interface for Wallet Transaction audit trail.
    All fields are read-only (transactions are immutable).
    """

    list_display = (
        "reference",
        "wallet_user",
        "transaction_type",
        "amount_display",
        "balance_after_display",
        "created_at",
    )
    list_filter = ("transaction_type", "created_at")
    search_fields = (
        "reference",
        "wallet__user__email",
        "description",
        "wallet__user__full_name",
    )
    readonly_fields = (
        "id",
        "wallet",
        "transaction_type",
        "amount",
        "reference",
        "description",
        "balance_before",
        "balance_after",
        "metadata",
        "created_at",
    )

    fieldsets = (
        (
            "Transaction Details",
            {
                "fields": (
                    "id",
                    "wallet",
                    "transaction_type",
                    "amount",
                    "reference",
                    "description",
                )
            },
        ),
        ("Balance Tracking", {"fields": ("balance_before", "balance_after")}),
        ("Metadata", {"fields": ("metadata", "created_at"), "classes": ("collapse",)}),
    )

    def wallet_user(self, obj):
        """Display wallet owner."""
        return obj.wallet.user.email

    wallet_user.short_description = "User"
    wallet_user.admin_order_field = "wallet__user__email"

    def amount_display(self, obj):
        """Display formatted amount."""
        return f"₦{obj.amount:,.2f}"

    amount_display.short_description = "Amount"
    amount_display.admin_order_field = "amount"

    def balance_after_display(self, obj):
        """Display formatted balance after transaction."""
        return f"₦{obj.balance_after:,.2f}"

    balance_after_display.short_description = "Balance After"

    def has_add_permission(self, request):
        """Prevent manual transaction creation (created via wallet operations)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent transaction deletion (immutable audit trail)."""
        return False
