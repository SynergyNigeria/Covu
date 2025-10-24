from django.contrib import admin
from stores.models import Store


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    """Admin interface for Store management."""

    list_display = [
        "name",
        "seller_email",
        "state",
        "city",
        "average_rating",
        "product_count",
        "is_active",
        "created_at",
    ]

    list_filter = [
        "state",
        "is_active",
        "created_at",
        "average_rating",
    ]

    search_fields = [
        "name",
        "seller__email",
        "seller__full_name",
        "city",
        "description",
    ]

    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "seller_email",
        "logo_url",
    ]

    fieldsets = (
        ("Store Info", {"fields": ("id", "name", "description", "logo", "logo_url")}),
        ("Seller", {"fields": ("seller", "seller_email")}),
        ("Location (40% Algorithm Weight)", {"fields": ("state", "city")}),
        ("Algorithm Factors", {"fields": ("average_rating", "product_count")}),
        ("Status", {"fields": ("is_active", "created_at", "updated_at")}),
    )

    def seller_email(self, obj):
        """Display seller email for easy identification."""
        return obj.seller.email

    seller_email.short_description = "Seller Email"

    def logo_url(self, obj):
        """Display logo URL (default or uploaded)."""
        return obj.logo_url

    logo_url.short_description = "Logo URL"
