from django.db.models.signals import post_save
from django.dispatch import receiver
from orders.models import Order
from .services import notify_order_placed, notify_order_status_changed

@receiver(post_save, sender=Order)
def order_notification_handler(sender, instance, created, **kwargs):
    if created:
        notify_order_placed(instance)
    else:
        notify_order_status_changed(instance)

from django.contrib.auth import get_user_model
from .models import NotificationPreference

User = get_user_model()

@receiver(post_save, sender=User)
def create_notification_preference(sender, instance, created, **kwargs):
    if created:
        NotificationPreference.objects.get_or_create(user=instance)