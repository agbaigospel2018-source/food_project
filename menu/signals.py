from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import MenuItemReview


@receiver([post_save, post_delete], sender=MenuItemReview)
def update_menu_item_rating(sender, instance, **kwargs):
    instance.item.refresh_rating_cache()
