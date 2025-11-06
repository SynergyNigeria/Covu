"""
Complaint Admin Interface
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Complaint


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    """Admin interface for managing complaints"""

    list_display = [
        "complaint_number",
        "complaint_type_badge",
        "subject_short",
        "reporter_name",
        "urgency_badge",
        "status_badge",
        "created_at",
    ]

    list_filter = [
        "complaint_type",
        "status",
        "urgency",
        "category",
        "created_at",
    ]

    search_fields = [
        "subject",
        "description",
        "reporter__email",
        "reporter__full_name",
        "reported_user_name",
        "order_id",
        "transaction_id",
    ]

    readonly_fields = [
        "id",
        "complaint_number",
        "reporter",
        "reporter_email",
        "created_at",
        "updated_at",
        "attachment_preview",
    ]

    fieldsets = (
        (
            "Complaint Info",
            {
                "fields": (
                    "id",
                    "complaint_number",
                    "complaint_type",
                    "category",
                    "urgency",
                    "status",
                )
            },
        ),
        (
            "Reporter Information",
            {
                "fields": (
                    "reporter",
                    "reporter_email",
                    "reporter_phone",
                )
            },
        ),
        (
            "Complaint Details",
            {
                "fields": (
                    "subject",
                    "description",
                    "attachment",
                    "attachment_preview",
                )
            },
        ),
        (
            "Related Information",
            {
                "fields": (
                    "reported_user",
                    "reported_user_name",
                    "order_id",
                    "transaction_id",
                    "transaction_type",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Admin Response",
            {
                "fields": (
                    "admin_notes",
                    "admin_response",
                    "resolved_by",
                    "resolved_at",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    ordering = ["-created_at"]

    def complaint_number(self, obj):
        """Display short complaint number"""
        return obj.complaint_number

    complaint_number.short_description = "Ref #"

    def complaint_type_badge(self, obj):
        """Display complaint type with color badge"""
        colors = {
            "SELLER": "red",
            "BUYER": "blue",
            "ORDER": "orange",
            "TRANSACTION": "purple",
        }
        color = colors.get(obj.complaint_type, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_complaint_type_display(),
        )

    complaint_type_badge.short_description = "Type"

    def subject_short(self, obj):
        """Display shortened subject"""
        return obj.subject[:50] + "..." if len(obj.subject) > 50 else obj.subject

    subject_short.short_description = "Subject"

    def reporter_name(self, obj):
        """Display reporter name"""
        return obj.reporter.full_name

    reporter_name.short_description = "Reporter"

    def urgency_badge(self, obj):
        """Display urgency with color badge"""
        colors = {
            "LOW": "#90EE90",
            "MEDIUM": "#FFD700",
            "HIGH": "#FFA500",
            "URGENT": "#FF4500",
        }
        color = colors.get(obj.urgency, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.urgency,
        )

    urgency_badge.short_description = "Urgency"

    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            "PENDING": "#FFA500",
            "IN_PROGRESS": "#1E90FF",
            "RESOLVED": "#32CD32",
            "CLOSED": "#808080",
            "REJECTED": "#DC143C",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    def attachment_preview(self, obj):
        """Display attachment preview if exists"""
        if obj.attachment:
            if obj.attachment.name.endswith((".jpg", ".jpeg", ".png")):
                return format_html(
                    '<a href="{}" target="_blank"><img src="{}" style="max-width: 200px; max-height: 200px;" /></a>',
                    obj.attachment.url,
                    obj.attachment.url,
                )
            else:
                return format_html(
                    '<a href="{}" target="_blank">View Attachment</a>',
                    obj.attachment.url,
                )
        return "No attachment"

    attachment_preview.short_description = "Attachment Preview"

    def save_model(self, request, obj, form, change):
        """Auto-set resolved_by when status changes to resolved"""
        if change and obj.status in ["RESOLVED", "CLOSED"] and not obj.resolved_by:
            obj.resolved_by = request.user
            if not obj.resolved_at:
                from django.utils import timezone

                obj.resolved_at = timezone.now()
        super().save_model(request, obj, form, change)
