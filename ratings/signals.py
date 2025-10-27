from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg, Count
from .models import Rating


@receiver(post_save, sender=Rating)
def update_store_rating_on_save(sender, instance, created, **kwargs):
    """
    Update store's average_rating and total_reviews when rating is approved.

    Only approved ratings count towards store statistics.
    """
    if instance.is_approved:
        update_store_ratings(instance.store)


@receiver(post_delete, sender=Rating)
def update_store_rating_on_delete(sender, instance, **kwargs):
    """
    Update store's average_rating and total_reviews when rating is deleted.
    """
    update_store_ratings(instance.store)


def update_store_ratings(store):
    """
    Recalculate store's average_rating and total_reviews from approved ratings.

    Args:
        store: Store instance to update
    """
    # Get all ratings for this store (no moderation)
    ratings = Rating.objects.filter(store=store)

    # Calculate statistics
    stats = ratings.aggregate(avg_rating=Avg("rating"))

    # Update store
    store.average_rating = stats["avg_rating"] or 0.0
    store.save(update_fields=["average_rating"])
