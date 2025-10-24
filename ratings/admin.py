from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    """Admin interface for Rating model with moderation tools."""

    list_display = [
        "id",
        "buyer_name",
        "store_name",
        "rating_stars",
        "has_review_badge",
        "approval_status",
        "created_at",
    ]
    list_filter = ["is_approved", "rating", "created_at"]
    search_fields = [
        "buyer__email",
        "buyer__first_name",
        "buyer__last_name",
        "store__name",
        "review",
    ]
    readonly_fields = [
        "order",
        "buyer",
        "store",
        "rating",
        "review",
        "created_at",
        "updated_at",
        "approved_at",
        "approved_by",
    ]
    list_per_page = 50
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    fieldsets = (
        (
            "Rating Information",
            {
                "fields": (
                    "order",
                    "buyer",
                    "store",
                    "rating",
                    "review",
                )
            },
        ),
        (
            "Moderation",
            {
                "fields": (
                    "is_approved",
                    "approved_at",
                    "approved_by",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def buyer_name(self, obj):
        """Display buyer's full name."""
        if obj.buyer:
            return obj.buyer.get_full_name() or obj.buyer.email
        return "Anonymous"

    buyer_name.short_description = "Buyer"

    def store_name(self, obj):
        """Display store name with link."""
        return format_html(
            '<a href="/admin/stores/store/{}/change/">{}</a>',
            obj.store.id,
            obj.store.name,
        )

    store_name.short_description = "Store"

    def rating_stars(self, obj):
        """Display rating as stars with color."""
        stars = "★" * obj.rating + "☆" * (5 - obj.rating)
        color = {
            1: "#e74c3c",  # Red
            2: "#e67e22",  # Orange
            3: "#f39c12",  # Yellow
            4: "#2ecc71",  # Light Green
            5: "#27ae60",  # Green
        }.get(obj.rating, "#95a5a6")
        return format_html(
            '<span style="color: {}; font-size: 16px;">{} ({})</span>',
            color,
            stars,
            obj.rating_text,
        )

    rating_stars.short_description = "Rating"

    def has_review_badge(self, obj):
        """Display badge if rating has review."""
        if obj.has_review:
            return format_html(
                '<span style="background-color: #3498db; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">📝 HAS REVIEW</span>'
            )
        return format_html(
            '<span style="color: #95a5a6; font-size: 11px;">No Review</span>'
        )

    has_review_badge.short_description = "Review"

    def approval_status(self, obj):
        """Display approval status with color coding."""
        if obj.is_approved:
            return format_html(
                '<span style="background-color: #27ae60; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">✓ APPROVED</span>'
            )
        return format_html(
            '<span style="background-color: #e67e22; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">⏳ PENDING</span>'
        )

    approval_status.short_description = "Status"

    def save_model(self, request, obj, form, change):
        """Set approved_by and approved_at when approving."""
        if change and "is_approved" in form.changed_data and obj.is_approved:
            if not obj.approved_at:
                obj.approved_at = timezone.now()
            if not obj.approved_by:
                obj.approved_by = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        """Prevent manual creation - ratings created via API."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion to preserve audit trail."""
        return False
