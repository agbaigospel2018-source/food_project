from .models import Notification, NotificationType, NotificationPreference


def _get_prefs(user):
    """
    Safely return the user's NotificationPreference,
    creating a default one if it doesn't exist yet.
    """
    prefs, _ = NotificationPreference.objects.get_or_create(user=user)
    return prefs


def notify_user(recipient, notification_type, title, message, order=None):
    """
    Create and persist a notification for a single user, but only if their
    preferences allow it.
    """
    prefs = _get_prefs(recipient)

    # ──────────────────────────────────────────────
    # Map notification types to the corresponding
    # preference flag.  If push notifications are
    # disabled we skip all in-app notifications.
    # ──────────────────────────────────────────────
    if not prefs.notify_push:
        return None

    type_to_pref = {
        NotificationType.NEW_ORDER: prefs.notify_new_orders,
        NotificationType.ORDER_PLACED: prefs.notify_status,
        NotificationType.ORDER_ACCEPTED: prefs.notify_status,
        NotificationType.ORDER_PREPARING: prefs.notify_status,
        NotificationType.ORDER_READY: prefs.notify_status,
        NotificationType.ORDER_COMPLETED: prefs.notify_status,
        NotificationType.ORDER_CANCELLED: prefs.notify_status,
        NotificationType.ORDER_REJECTED: prefs.notify_status,
        NotificationType.LOW_STOCK: prefs.notify_new_orders,
        NotificationType.PROMO: prefs.notify_marketing,
        NotificationType.SYSTEM: True,  # system messages always go through
    }

    if not type_to_pref.get(notification_type, True):
        return None

    return Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        order=order,
    )


def notify_order_placed(order):
    """Notify the vendor that a new order has been placed."""
    notify_user(
        recipient=order.vendor.owner,
        notification_type=NotificationType.NEW_ORDER,
        title='New Order Received!',
        message=(
            f'Order #{order.short_id()} has been placed by '
            f'{order.student.username}. Total: ₦{order.total_amount}'
        ),
        order=order,
    )


def notify_order_status_changed(order):
    """Notify the student when their order status changes."""
    status_messages = {
        'accepted': (
            'Order Accepted',
            'Your order has been accepted and will be prepared shortly.',
        ),
        'preparing': (
            'Order Being Prepared',
            'Your order is now being prepared.',
        ),
        'ready': (
            'Order Ready!',
            'Your order is ready for pickup!',
        ),
        'completed': (
            'Order Completed',
            'Your order has been completed. Enjoy your meal!',
        ),
        'cancelled': (
            'Order Cancelled',
            'Your order has been cancelled.',
        ),
        'rejected': (
            'Order Rejected',
            'Unfortunately, your order has been rejected by the vendor.',
        ),
    }

    if order.status in status_messages:
        title, message = status_messages[order.status]
        notify_user(
            recipient=order.student,
            notification_type=NotificationType(f'order_{order.status}'),
            title=title,
            message=f'{message} (Order #{order.short_id()})',
            order=order,
        )