from django.contrib import admin
from products.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin interface for Product management."""

    list_display = [
        "name",
        "store_name",
        "category",
        "price",
        "is_new_badge",
        "key_features_summary",
        "is_active",
        "created_at",
    ]

    list_filter = [
        "category",
        "is_active",
        "created_at",
        "premium_quality",
        "durable",
        "modern_design",
        "easy_maintain",
    ]

    search_fields = ["name", "description", "store__name", "store__seller__email"]

    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "is_new_badge",
        "location_info",
    ]

    fieldsets = (
        ("Product Identity", {"fields": ("id", "store", "name", "description")}),
        ("Pricing & Category", {"fields": ("price", "category")}),
        ("Images", {"fields": ("images",)}),
        (
            "Key Features (4 Flags)",
            {
                "fields": (
                    "premium_quality",
                    "durable",
                    "modern_design",
                    "easy_maintain",
                ),
                "description": "Boolean flags for product features",
            },
        ),
        (
            "Location (Inherited from Store)",
            {
                "fields": ("location_info",),
                "description": "Location used for product listing algorithm",
            },
        ),
        (
            "Status & Timestamps",
            {"fields": ("is_active", "is_new_badge", "created_at", "updated_at")},
        ),
    )

    ordering = ["-created_at"]
    date_hierarchy = "created_at"

    def store_name(self, obj):
        """Display store name."""
        return obj.store.name

    store_name.short_description = "Store"
    store_name.admin_order_field = "store__name"

    def is_new_badge(self, obj):
        """Display if product is new (< 30 days)."""
        return "🆕 New" if obj.is_new else ""

    is_new_badge.short_description = "New?"

    def key_features_summary(self, obj):
        """Display count of enabled key features."""
        features = [
            obj.premium_quality,
            obj.durable,
            obj.modern_design,
            obj.easy_maintain,
        ]
        count = sum(features)
        return f"{count}/4 features"

    key_features_summary.short_description = "Features"

    def location_info(self, obj):
        """Display product location from store."""
        return f"{obj.location_state} - {obj.location_city}"

    location_info.short_description = "Location (State - City)"
