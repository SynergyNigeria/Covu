from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from products.models import Product
import logging

logger = logging.getLogger("wallet")  # Reuse wallet logger for now


@receiver(post_save, sender=Product)
def update_store_product_count_on_create(sender, instance, created, **kwargs):
    """
    Update store's product_count when a new product is created.

    This count is used in the store listing algorithm.
    """
    if created:
        store = instance.store
        store.product_count = store.products.filter(is_active=True).count()
        store.save(update_fields=["product_count"])
        logger.info(f"Store {store.name} product count updated: {store.product_count}")


@receiver(post_delete, sender=Product)
def update_store_product_count_on_delete(sender, instance, **kwargs):
    """
    Update store's product_count when a product is deleted.

    This count is used in the store listing algorithm.
    """
    store = instance.store
    store.product_count = store.products.filter(is_active=True).count()
    store.save(update_fields=["product_count"])
    logger.info(
        f"Store {store.name} product count updated after deletion: {store.product_count}"
    )
