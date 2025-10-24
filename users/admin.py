from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """
    Admin configuration for CustomUser model.
    """

    model = CustomUser

    list_display = (
        "email",
        "full_name",
        "phone_number",
        "state",
        "city",
        "is_seller",
        "is_active",
        "is_staff",
        "date_joined",
    )

    list_filter = (
        "is_seller",
        "is_active",
        "is_staff",
        "is_superuser",
        "state",
        "date_joined",
    )

    search_fields = ("email", "full_name", "phone_number", "city")

    ordering = ("-date_joined",)

    readonly_fields = ("date_joined", "last_login")

    fieldsets = (
        (
            "User Information",
            {"fields": ("email", "phone_number", "full_name", "state")},
        ),
        (
            "Account Status",
            {"fields": ("is_seller", "is_active", "is_staff", "is_superuser")},
        ),
        (
            "Permissions",
            {
                "fields": ("groups", "user_permissions"),
                "classes": ("collapse",),
            },
        ),
        (
            "Important Dates",
            {
                "fields": ("date_joined", "last_login"),
            },
        ),
    )

    add_fieldsets = (
        (
            "User Information",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "phone_number",
                    "full_name",
                    "state",
                    "city",
                    "password1",
                    "password2",
                ),
            },
        ),
        (
            "Account Status",
            {
                "fields": ("is_seller", "is_active", "is_staff", "is_superuser"),
            },
        ),
    )

    filter_horizontal = ("groups", "user_permissions")
