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