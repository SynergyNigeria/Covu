from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Wallet
import logging

logger = logging.getLogger("wallets")


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wallet(sender, instance, created, **kwargs):
    """
    Auto-create wallet when new user registers.

    Philosophy: "Everyone gets a wallet automatically"
    - User registers → Wallet created with ₦0.00 balance
    - No manual wallet creation needed
    - Secure by default
    """
    if created:
        wallet = Wallet.objects.create(user=instance)
        logger.info(f"✅ Wallet auto-created for user: {instance.email}")


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_user_wallet(sender, instance, **kwargs):
    """
    Ensure wallet exists for user (safety net).
    Creates wallet if missing for any reason.
    """
    if not hasattr(instance, "wallet"):
        wallet = Wallet.objects.create(user=instance)
        logger.warning(f"⚠️  Wallet was missing for {instance.email}, created now")
