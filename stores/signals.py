from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from stores.models import Store
import logging

logger = logging.getLogger("wallet")  # Reuse wallet logger for now


@receiver(pre_save, sender=Store)
def set_default_store_name(sender, instance, **kwargs):
    """
    Auto-generate store name if not provided.

    One-Click Creation: Name format = COVU + user's unique ID
    Example: COVU123e4567-e89b-12d3-a456-426614174000
    """
    if not instance.name or instance.name == "":
        # Generate unique store name
        user_id_short = str(instance.seller.id)[:8]  # First 8 chars of UUID
        instance.name = f"COVU{user_id_short}"
        logger.info(
            f"Auto-generated store name: {instance.name} for user {instance.seller.email}"
        )


@receiver(post_save, sender=Store)
def set_user_as_seller(sender, instance, created, **kwargs):
    """
    Automatically set user.is_seller = True when store is created.

    This ensures user gains seller privileges immediately after store creation.
    """
    if created:
        user = instance.seller
        if not user.is_seller:
            user.is_seller = True
            user.save(update_fields=["is_seller"])
            logger.info(
                f"✅ User {user.email} is now a seller (store: {instance.name})"
            )


@receiver(post_save, sender=Store)
def copy_location_from_user(sender, instance, created, **kwargs):
    """
    Copy state and city from user if not already set.

    Location is critical for the 40% algorithm weight.
    """
    if created:
        if not instance.state:
            instance.state = instance.seller.state
        if not instance.city:
            instance.city = instance.seller.city

        # Save only if location was updated
        if (
            instance.state != instance.seller.state
            or instance.city != instance.seller.city
        ):
            instance.save(update_fields=["state", "city"])
            logger.info(
                f"Copied location ({instance.state}, {instance.city}) to store {instance.name}"
            )
