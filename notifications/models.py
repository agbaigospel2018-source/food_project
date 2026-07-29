import uuid
from django.conf import settings
from django.db import models

class NotificationType(models.TextChoices):
    # Order lifecycle
    ORDER_PLACED = 'order_placed', 'Order Placed'
    ORDER_ACCEPTED = 'order_accepted', 'Order Accepted'
    ORDER_PREPARING = 'order_preparing', 'Order Preparing'
    ORDER_READY = 'order_ready', 'Order Ready for Pickup'
    ORDER_COMPLETED = 'order_completed', 'Order Completed'
    ORDER_CANCELLED = 'order_cancelled', 'Order Cancelled'
    ORDER_REJECTED = 'order_rejected', 'Order Rejected'
    # Vendor
    NEW_ORDER = 'new_order', 'New Order Received'
    LOW_STOCK = 'low_stock', 'Low Stock Alert'
    # General
    PROMO = 'promo', 'Promotion'
    SYSTEM = 'system', 'System Notification'

class Notification(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    # Optional link to the related order
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['recipient', '-created_at']),

        ]
        
    def __str__(self):
        return f'{self.title} → {self.recipient.username}'

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    notify_new_orders = models.BooleanField(default=True)
    notify_status = models.BooleanField(default=True)
    notify_reviews = models.BooleanField(default=True)
    notify_push = models.BooleanField(default=True)
    notify_email = models.BooleanField(default=False)
    notify_marketing = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.username} Preferences'